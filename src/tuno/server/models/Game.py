from collections.abc import Mapping
from random import shuffle
from threading import RLock, Thread
from time import monotonic

from tuno.server.config import (
    GAME_WATCHER_INTERVAL,
    GAME_WATCHER_SKIP_THRESHOLD,
    PLAYER_TIMEOUT,
)
from tuno.server.exceptions import (
    ApiException,
    GameAlreadyStartedException,
    GameNotStartedException,
    InvalidLeadCardInfoException,
    NewPlayerToStartedGameException,
    NotEnoughPlayersException,
    PlayerNotFoundException,
)
from tuno.server.utils.create_deck import create_deck
from tuno.server.utils.Logger import Logger
from tuno.server.utils.misc import format_optional_operator
from tuno.shared.constraints import (
    DEFAULT_INITIAL_HAND_SIZE,
    DEFAULT_PLAYER_CAPACITY,
    MIN_PLAYER_CAPACITY,
)
from tuno.shared.deck import BasicCardColor, Card, Deck
from tuno.shared.loop import loop
from tuno.shared.rules import GameRules, check_rule_update
from tuno.shared.sse_events import (
    CardsEvent,
    EndOfConnectionEvent,
    GameStateEvent,
    NotificationEvent,
    ServerSentEvent,
)

from .Player import Player


class Game:

    tag: str = "default"  # TODO: maybe multiple games in one server someday
    lock: RLock
    watcher_thread: Thread

    __players: list[Player]
    __started: bool
    __rules: GameRules
    __draw_pile: Deck
    __discard_pile: Deck
    __current_player_index: int
    __lead_card: Card | None
    __lead_color: BasicCardColor | None
    __logger: Logger

    def __init__(self) -> None:

        self.__players = []
        self.__started = False
        self.__rules = GameRules(
            player_capacity=DEFAULT_PLAYER_CAPACITY,
            initial_hand_size=DEFAULT_INITIAL_HAND_SIZE,
            test_bool=True,
        )
        self.__draw_pile = []
        self.__discard_pile = []
        self.__current_player_index = -1
        self.__lead_card = None
        self.__lead_color = None
        self.lock = RLock()
        self.__logger = Logger(f"{__name__}#{self.tag}")
        self.watcher_thread = Thread(target=self.watcher_loop, daemon=True)

        self.__logger.debug(f"game#{self.tag} created")

    @property
    def started(self) -> bool:
        return self.__started

    def broadcast(self, event: ServerSentEvent) -> None:
        with self.lock:
            for player in self.__players:
                player.message_queue.put_nowait(event)

    def get_game_state_event(self) -> GameStateEvent:
        with self.lock:
            started = self.__started
            return GameStateEvent(
                GameStateEvent.DataType(
                    started=started,
                    rules=self.__rules,
                    draw_pile_size=(len(self.__draw_pile) if started else -1),
                    discard_pile_size=(
                        len(self.__discard_pile) if started else -1
                    ),
                    players=[
                        GameStateEvent.PlayerDataType(
                            name=player.name,
                            connected=player.connected,
                            card_count=(len(player.cards) if started else -1),
                        )
                        for player in self.__players
                    ],
                    current_player_index=self.__current_player_index,
                    lead_card=self.__lead_card,
                    lead_color=self.__lead_color,
                )
            )

    def update_rules(
        self,
        modified_rules: Mapping[str, object],
        *,
        operator_name: str | None,
    ) -> None:

        with self.lock:

            rules = self.__rules.copy()
            for key, value in modified_rules.items():
                check_rule_update(key, value)
                rules[key] = value  # type: ignore[literal-required]
            self.__rules = rules

            message = format_optional_operator(
                "Game rules updated",
                operator_name,
            )
            self.__logger.info(message)
            self.broadcast(
                NotificationEvent(
                    NotificationEvent.DataType(
                        title="Rules Updated",
                        message=message,
                    )
                )
            )

            if "player_capacity" in modified_rules:
                new_capacity = self.__rules["player_capacity"]
                if len(self.__players) > new_capacity:
                    while len(self.__players) > new_capacity:
                        excess_player = self.__players.pop()
                        excess_player.message_queue.put_nowait(
                            EndOfConnectionEvent(
                                "Sorry, you are kicked out due to "
                                "a recent rule change."
                            )
                        )
                        excess_player.connected = False
                    self.broadcast(self.get_game_state_event())

    def get_player(
        self,
        player_name: str,
        allow_creation: bool = False,
    ) -> Player:
        with self.lock:

            for player in self.__players:
                if player.name == player_name:
                    return player

            else:

                exception: ApiException | None = None
                if not allow_creation:
                    exception = PlayerNotFoundException(player_name)
                elif self.__started:
                    exception = NewPlayerToStartedGameException(player_name)
                if exception:
                    self.__logger.warn(exception.message)
                    raise exception

                new_player = Player(player_name)
                self.__players.append(new_player)
                self.broadcast(self.get_game_state_event())

                return new_player

    def kick_out_player(
        self,
        *,
        target_name: str,
        operator_name: str | None,
    ) -> None:

        with self.lock:
            target_player = self.get_player(target_name)
            target_player.connected = False
            target_player.message_queue.put_nowait(
                EndOfConnectionEvent(
                    format_optional_operator(
                        "Sorry, you are kicked out",
                        operator_name,
                    )
                )
            )
            self.__players.remove(target_player)

        self.__logger.info(
            format_optional_operator(
                f"player#{target_name} is kicked out",
                operator_name,
            )
        )

    def set_lead_card_info(
        self,
        lead_card: Card,
        *,
        lead_color: BasicCardColor | None = None,
    ) -> None:
        with self.lock:
            if lead_card["type"] == "wild":
                if lead_color is None:
                    raise InvalidLeadCardInfoException(lead_card, lead_color)
                self.__lead_color = lead_color
            else:
                if lead_color is not None:
                    raise InvalidLeadCardInfoException(lead_card, lead_color)
            self.__lead_card = lead_card

    def draw_card(
        self,
        count: int,
        *,
        player: Player | None = None,
        allow_shuffle: bool = False,
    ) -> Deck | None:

        drawn_cards: Deck = []

        with self.lock:

            for _ in range(count):

                if not len(self.__draw_pile):

                    if allow_shuffle:
                        self.__draw_pile = self.__discard_pile
                        self.__discard_pile = []
                        shuffle(self.__draw_pile)

                    if not len(self.__draw_pile):
                        self.__draw_pile.extend(reversed(drawn_cards))
                        self.broadcast(
                            NotificationEvent(
                                NotificationEvent.DataType(
                                    title="Not Enough Cards",
                                    message="Not enough cards to draw...",
                                )
                            )
                        )
                        self.stop(state_check_required=False)
                        return None

                drawn_card = self.__draw_pile.pop()
                drawn_cards.append(drawn_card)

                if player:
                    with player.lock:
                        player.cards.extend(drawn_cards)
                        player.message_queue.put_nowait(
                            CardsEvent(player.cards)
                        )

            self.broadcast(self.get_game_state_event())

        return drawn_cards

    def start(self, player_name: str) -> None:
        with self.lock:

            if self.__started:
                raise GameAlreadyStartedException()

            if len(self.__players) < MIN_PLAYER_CAPACITY:
                raise NotEnoughPlayersException()

            # -- reset card piles --
            self.__draw_pile = create_deck()
            self.__discard_pile = []
            shuffle(self.__draw_pile)

            # -- dispatch initial cards --
            initial_hand_size = self.__rules["initial_hand_size"]
            for player in self.__players:
                if not self.draw_card(initial_hand_size, player=player):
                    return

            # -- set lead card --
            lead_card: Card | None = None
            while (lead_card is None) or (lead_card["type"] != "number"):
                lead_card_drawn = self.draw_card(1)
                if not lead_card_drawn:
                    return
                else:
                    assert len(lead_card_drawn) == 1
                    lead_card = lead_card_drawn[0]
                    self.__discard_pile.append(lead_card)
            self.set_lead_card_info(lead_card)

            # -- initialize other states --
            self.__current_player_index = 0
            self.__started = True

            message = f"Game started by player#{player_name}."
            self.__logger.info(message)
            self.broadcast(
                NotificationEvent(
                    NotificationEvent.DataType(
                        title="Started!",
                        message=message,
                    )
                )
            )

            self.broadcast(self.get_game_state_event())

    def stop(
        self,
        player_name: str = "",
        state_check_required: bool = True,
    ) -> None:
        with self.lock:

            if state_check_required:
                if not self.__started:
                    raise GameNotStartedException()

            self.__started = False

            message = format_optional_operator(
                "Game stopped",
                player_name,
            )
            self.__logger.info(message)
            self.broadcast(
                NotificationEvent(
                    NotificationEvent.DataType(
                        title="Stopped!",
                        message=message,
                    )
                )
            )

            self.broadcast(self.get_game_state_event())

    def watcher_loop(self) -> None:

        def on_slow(continuous_slow_count: int) -> None:
            if continuous_slow_count >= GAME_WATCHER_SKIP_THRESHOLD:
                self.__logger.warn(
                    "The watcher loop seems to be slow. "
                    f"(continuous_slow_count: {continuous_slow_count})"
                )

        for _ in loop(GAME_WATCHER_INTERVAL, allow_skip=True, on_slow=on_slow):
            with self.lock:

                now = monotonic()

                player_timeout_seconds = PLAYER_TIMEOUT.total_seconds()
                state_changed = False

                for player in self.__players:
                    with player.lock:

                        previous_connected_status = player.connected

                        player.connected = False
                        if player.subscription_token:
                            if player.last_pending_timestamp:
                                pending_time = (
                                    now - player.last_pending_timestamp
                                )
                                if pending_time < player_timeout_seconds:
                                    player.connected = True
                            else:
                                player.connected = True

                        if player.connected != previous_connected_status:
                            state_changed = True
                            if not player.connected:
                                self.__logger.info(
                                    f"Disconnected from player#{player.name}. "
                                    f"(subscription_token: {player.subscription_token})"
                                )
                                player.subscription_token = ""
                                if not self.__started:
                                    self.__players.remove(player)

                if state_changed:
                    self.broadcast(self.get_game_state_event())


game = Game()
