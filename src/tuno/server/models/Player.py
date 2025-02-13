from collections.abc import Generator
from contextlib import contextmanager
from queue import Queue
from threading import RLock
from time import monotonic

from tuno.server.config import PLAYER_MESSAGE_QUEUE_SIZE
from tuno.server.utils.Logger import Logger
from tuno.shared.deck import Deck
from tuno.shared.sse_events import ServerSentEvent


class Player:

    name: str
    cards: Deck
    message_queue: Queue[ServerSentEvent]
    lock: RLock
    connected: bool  # set by game watcher
    subscription_token: str
    __logger: Logger
    __last_pending_timestamp: float | None
    __last_sent_timestamp: float | None

    def __init__(self, name: str) -> None:

        self.name = name
        self.cards = []
        self.message_queue = Queue(PLAYER_MESSAGE_QUEUE_SIZE)
        self.lock = RLock()
        self.connected = False
        self.subscription_token = ""
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
