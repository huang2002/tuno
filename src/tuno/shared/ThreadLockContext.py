from collections.abc import Generator
from contextlib import contextmanager
from threading import Lock, RLock
from typing import Final

DEFAULT_LOCK_TIMEOUT_SECONDS: Final[float] = 60.0


@contextmanager
def ThreadLockContext(
    lock: Lock | RLock,
    timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> Generator[None, None, None]:
    lock.acquire(timeout=timeout_seconds)
    try:
        yield
    finally:
        lock.release()
