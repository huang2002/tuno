from collections.abc import Generator, Iterable, Sequence
from contextlib import contextmanager
from queue import Queue
from random import choice
from threading import RLock
from time import monotonic

from tuno.server.config import PLAYER_MESSAGE_QUEUE_SIZE
from tuno.server.exceptions import CardIdsNotFoundException
from tuno.server.utils.Logger import Logger
from tuno.shared.check_play import InvalidPlayException, check_play
from tuno.shared.constraints import DEFAULT_BOT_PLAY_DELAY_SECONDS
from tuno.shared.deck import BasicCardColor, Card, Deck, basic_card_colors
from tuno.shared.LazyTimer import LazyTimer
from tuno.shared.rules import GameRules
from tuno.shared.sse_events import CardsEvent, ServerSentEvent


class Player:

    is_bot: bool
    name: str
    cards: Deck
    last_result: int
    message_queue: Queue[ServerSentEvent]
    lock: RLock
    connected: bool  # set by game watcher
    subscription_token: str
    bot_play_timer: LazyTimer | None
    __logger: Logger
    __last_pending_timestamp: float | None
    __last_sent_timestamp: float | None

    def __init__(self, name: str, *, is_bot: bool) -> None:

        self.is_bot = is_bot
        self.name = name
        self.cards = []
        self.last_result = -1
        self.message_queue = Queue(PLAYER_MESSAGE_QUEUE_SIZE)
        self.lock = RLock()
        self.connected = False
        self.subscription_token = ""
        self.bot_play_timer = (
            LazyTimer(DEFAULT_BOT_PLAY_DELAY_SECONDS) if is_bot else None
        )
        self.__logger = Logger(f"{__name__}#{name}")
        self.__last_pending_timestamp = None
        self.__last_sent_timestamp = None

        self.__logger.debug(f"player#{name} created")

    @property
    def last_pending_timestamp(self) -> float | None:
        return self.__last_pending_timestamp

    @property
    def last_sent_timestamp(self) -> float | None:
        return self.__last_sent_timestamp

    @contextmanager
    def message_context(self) -> Generator[None]:
        with self.lock:
            self.__last_pending_timestamp = monotonic()
            yield
            self.__last_pending_timestamp = None
            self.__last_sent_timestamp = monotonic()

    def get_cards_event(self) -> CardsEvent:
        return CardsEvent(self.cards)

    def give_out_cards(self, card_ids: Sequence[str]) -> Deck:

        if len(card_ids) == 0:
            return []

        cards_ids_remaining = set(card_ids)
        cards_left: Deck = []
        cards_out: Deck = []

        with self.lock:

            for card in self.cards:
                if card["id"] in cards_ids_remaining:
                    cards_ids_remaining.remove(card["id"])
                    cards_out.append(card)
                else:
                    cards_left.append(card)

            if len(cards_ids_remaining) > 0:
                raise CardIdsNotFoundException(cards_ids_remaining)

            self.cards = cards_left

        return cards_out

    def bot_play(
        self,
        *,
        lead_color: BasicCardColor,
        lead_card: Card,
        skip_counter: int,
        rules: GameRules,
    ) -> tuple[list[str], BasicCardColor | None]:
        with self.lock:

            candidates: list[tuple[list[str], BasicCardColor | None]] = []
            for card in self.cards:
                colors: Iterable[BasicCardColor | None] = (
                    basic_card_colors if card["type"] == "wild" else [None]
                )
                for color in colors:
                    try:
                        check_play(
                            [card],
                            color,
                            lead_color=lead_color,
                            lead_card=lead_card,
                            skip_counter=skip_counter,
                            rules=rules,
                        )
                    except InvalidPlayException:
                        continue
                    else:
                        candidates.append(([card["id"]], color))

            if len(candidates) == 0:
                return ([], None)  # pass
            else:
                return choice(candidates)
