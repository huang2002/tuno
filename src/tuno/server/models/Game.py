from collections.abc import Mapping, Sequence
from random import shuffle
from threading import RLock, Thread
from time import monotonic
from typing import TYPE_CHECKING, Literal, assert_never

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
    NotCurrentPlayerException,
    NotEnoughPlayersException,
    PlayerNotFoundException,
    RuleUpdateOnStartedGameException,
)
from tuno.server.utils.create_deck import create_deck
from tuno.server.utils.format_optional_operator import format_optional_operator
from tuno.server.utils.Logger import Logger
from tuno.shared.check_play import check_play
from tuno.shared.constraints import (
    DEFAULT_INITIAL_HAND_SIZE,
    DEFAULT_PLAYER_CAPACITY,
    MIN_PLAYER_CAPACITY,
)
from tuno.shared.deck import BasicCardColor, Card, Deck, format_card
from tuno.shared.loop import loop
from tuno.shared.rules import GameRules, check_rule_update
from tuno.shared.sse_events import (
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
    __direction: Literal[-1, 1]
    __lead_card: Card | None
    __lead_color: BasicCardColor | None
    __draw_counter: int
    __skip_counter: int
    __logger: Logger

    def __init__(self) -> None:

        self.__players = []
        self.__started = False
        self.__rules = GameRules(
            player_capacity=DEFAULT_PLAYER_CAPACITY,
            initial_hand_size=DEFAULT_INITIAL_HAND_SIZE,
            shuffle_players=False,
            any_last_play=False,
        )
        self.__draw_pile = []
        self.__discard_pile = []
        self.__current_player_index = -1
        self.__direction = 1
        self.__lead_card = None
        self.__lead_color = None
        self.__draw_counter = 0
        self.__skip_counter = 0
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
                player.message_queue.put(event)

    def get_game_state_event(self) -> GameStateEvent:
        with self.lock:
            started = self.__started
            return GameStateEvent(
                GameStateEvent.DataType(
                    started=started,
                    rules=self.__rules,
                    draw_pile_size=(len(self.__draw_pile) if started else -1),
                    discard_pile_size=(len(self.__discard_pile) if started else -1),
                    players=[
                        GameStateEvent.PlayerDataType(
                            name=player.name,
                            connected=player.connected,
                            card_count=(
                                len(player.cards) if started else player.last_result
                            ),
                        )
                        for player in self.__players
                    ],
                    current_player_index=self.__current_player_index,
                    direction=self.__direction,
                    lead_card=self.__lead_card,
                    lead_color=self.__lead_color,
                    draw_counter=self.__draw_counter,
                    skip_counter=self.__skip_counter,
                )
            )

    def update_rules(
        self,
        modified_rules: Mapping[str, object],
        *,
        operator_name: str | None,
        operator_is_player: bool,
    ) -> None:

        with self.lock:

            if self.started:
                debug_message = format_optional_operator(
                    "Rejected rule update",
                    operator_name,
                    is_player=operator_is_player,
                )
                self.__logger.debug(debug_message)
                raise RuleUpdateOnStartedGameException()

            rules = self.__rules.copy()
            for key, value in modified_rules.items():
                check_rule_update(key, value)
                rules[key] = value  # type: ignore[literal-required]
            self.__rules = rules

            message = format_optional_operator(
                "Game rules updated",
                operator_name,
                is_player=operator_is_player,
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
                        excess_player.message_queue.put(
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
        operator_is_player: bool,
    ) -> None:

        with self.lock:

            target_player = self.get_player(target_name)
            target_player.connected = False
            target_player.message_queue.put(
                EndOfConnectionEvent(
                    format_optional_operator(
                        "Sorry, you are kicked out",
                        operator_name,
                        is_player=operator_is_player,
                    )
                )
            )
            self.__players.remove(target_player)

            if self.started:
                self.__discard_pile.extend(target_player.cards)
                target_player.cards.clear()

        self.__logger.info(
            format_optional_operator(
                f"player#{target_name} is kicked out",
                operator_name,
                is_player=operator_is_player,
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
                self.__lead_color = lead_card["color"]
            self.__lead_card = lead_card

    def draw_cards(
        self,
        count: int,
        *,
        player: Player | None,
        allow_shuffle: bool = False,
    ) -> Deck | None:

        drawn_cards: Deck = []

        with self.lock:

            for _ in range(count):

                if not len(self.__draw_pile):

                    if allow_shuffle:
                        self.__draw_pile = self.__discard_pile
                        self.__discard_pile = []
                        self.__logger.debug("Shuffled piles for card drawing.")
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
                        self.stop(
                            operator_name=None,
                            operator_is_player=False,
                            state_check_required=False,
                        )
                        return None

                drawn_card = self.__draw_pile.pop()
                drawn_cards.append(drawn_card)

            if player:
                with player.lock:
                    player.cards.extend(drawn_cards)
                    player.message_queue.put(player.get_cards_event())
                self.__logger.debug(
                    f"Cards drawn by player#{player.name}: {drawn_cards!r}"
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

            # -- shuffle players if needed --
            if self.__rules["shuffle_players"]:
                self.__logger.debug("Shuffled players.")
                shuffle(self.__players)

            # -- dispatch initial cards --
            initial_hand_size = self.__rules["initial_hand_size"]
            for player in self.__players:
                player.cards.clear()
            for player in self.__players:
                if not self.draw_cards(initial_hand_size, player=player):
                    return
                player.message_queue.put(player.get_cards_event())

            # -- set lead card --
            lead_card: Card | None = None
            while (lead_card is None) or (lead_card["type"] != "number"):
                lead_card_drawn = self.draw_cards(1, player=None)
                if not lead_card_drawn:
                    return
                else:
                    assert len(lead_card_drawn) == 1
                    lead_card = lead_card_drawn[0]
                    self.__discard_pile.append(lead_card)
            self.set_lead_card_info(lead_card)

            # -- initialize other states --
            self.__current_player_index = 0
            self.__direction = 1
            self.__draw_counter = 0
            self.__skip_counter = 0
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

    def play(
        self,
        player_name: str,
        card_ids: Sequence[str],
        play_color: BasicCardColor | None,
    ) -> None:
        with self.lock:

            player = self.get_player(player_name)
            expected_player = self.__players[self.__current_player_index]
            if player != expected_player:
                raise NotCurrentPlayerException(expected_player.name)

            player_cards_backup = player.cards.copy()
            cards_out = player.give_out_cards(card_ids)
            n_cards_out = len(cards_out)

            lead_color = self.__lead_color
            lead_card = self.__lead_card
            rules = self.__rules

            if n_cards_out > 0:

                try:
                    if not (lead_color and lead_card):
                        raise InvalidLeadCardInfoException(lead_card, lead_color)
                    check_play(
                        cards_out,
                        play_color,
                        lead_color=lead_color,
                        lead_card=lead_card,
                        skip_counter=self.__skip_counter,
                        rules=rules,
                    )
                    self.set_lead_card_info(cards_out[-1], lead_color=play_color)
                except:
                    player.cards = player_cards_backup
                    raise
                else:

                    play_color_message = (
                        f" (change color to {play_color})" if play_color else ""
                    )
                    self.__logger.info(
                        f"Player#{player.name} played: {cards_out!r}"
                        + play_color_message
                    )
                    self.broadcast(
                        NotificationEvent(
                            NotificationEvent.DataType(
                                title=f"{player.name}'s Play",
                                message=(
                                    ", ".join(map(format_card, cards_out))
                                    + play_color_message
                                ),
                            )
                        )
                    )

                    assert n_cards_out > 0

                    for card in cards_out:
                        if card["type"] == "number":
                            continue
                        elif card["type"] == "function":
                            if card["effect"] == "+2":
                                self.__draw_counter += 2
                                self.__skip_counter += 1
                            elif card["effect"] == "skip":
                                self.__skip_counter += 1
                            elif card["effect"] == "reverse":
                                self.__direction = -self.__direction
                            else:
                                assert_never(card["effect"])
                        elif card["type"] == "wild":
                            if card["effect"] == "+4":
                                self.__draw_counter += 4
                                self.__skip_counter += 1
                            elif card["effect"] == "color":
                                pass
                            else:
                                assert_never(card["effect"])
                        else:
                            assert_never(card["type"])

                    self.__discard_pile.extend(cards_out)

            else:  # n_cards_out == 0
                self.__logger.info(f"Player#{player.name} passed.")
                self.draw_cards(1, player=player, allow_shuffle=True)
                self.broadcast(
                    NotificationEvent(
                        NotificationEvent.DataType(
                            title=f"{player.name}'s Play",
                            message="Pass",
                        )
                    )
                )

            if len(player.cards) == 0:
                if (
                    (not rules["any_last_play"])
                    and (n_cards_out == 1)
                    and (cards_out[0]["type"] != "number")
                ):
                    self.draw_cards(1, player=player, allow_shuffle=True)
                else:
                    self.broadcast(
                        NotificationEvent(
                            NotificationEvent.DataType(
                                title="Game Ended",
                                message=f"Player#{player.name} won!",
                            )
                        )
                    )
                    return self.stop(operator_name=None, operator_is_player=False)

            player_count = len(self.__players)

            if self.__draw_counter > 0:
                next_player_index = (
                    self.__current_player_index + self.__direction
                ) % player_count
                next_player = self.__players[next_player_index]
                self.draw_cards(
                    self.__draw_counter,
                    player=next_player,
                    allow_shuffle=True,
                )
                self.__draw_counter = 0

            self.__current_player_index = (
                self.__current_player_index
                + self.__direction * (self.__skip_counter + 1)
            ) % player_count
            self.__skip_counter = 0

            player.message_queue.put(player.get_cards_event())
            self.broadcast(self.get_game_state_event())

    def stop(
        self,
        operator_name: str | None,
        operator_is_player: bool,
        state_check_required: bool = True,
    ) -> None:
        with self.lock:

            if state_check_required:
                if not self.__started:
                    raise GameNotStartedException()

            self.__started = False
            self.__lead_color = None
            self.__lead_card = None

            for player in self.__players:
                player.last_result = len(player.cards)

            message = format_optional_operator(
                "Game stopped",
                operator_name,
                is_player=operator_is_player,
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
                                pending_time = now - player.last_pending_timestamp
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
