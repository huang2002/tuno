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
    logger: Logger
    lock: RLock
    subscription_token: str
    last_pending_timestamp: float | None
    last_sent_timestamp: float | None
    connected: bool  # set by game watcher

    def __init__(self, name: str) -> None:

        self.name = name
        self.cards = []
        self.message_queue = Queue(PLAYER_MESSAGE_QUEUE_SIZE)
        self.logger = Logger(f"{__name__}#{name}")
        self.lock = RLock()
        self.subscription_token = ""
        self.last_pending_timestamp = None
        self.last_sent_timestamp = None
        self.connected = False

        self.logger.debug(f"player#{name} created")

    @contextmanager
    def message_context(self) -> Generator[None]:
        with self.lock:
            self.last_pending_timestamp = monotonic()
            yield
            self.last_pending_timestamp = None
            self.last_sent_timestamp = monotonic()
