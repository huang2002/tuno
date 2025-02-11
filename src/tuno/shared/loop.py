from collections.abc import Generator
from datetime import timedelta
from time import monotonic, sleep
from typing import Protocol


class LoopSkipCallback(Protocol):
    def __call__(self, continuous_slow_count: int) -> None: ...


def loop(
    interval_seconds: timedelta | float,
    *,
    allow_skip: bool = False,
    on_slow: LoopSkipCallback | None = None,
) -> Generator[float]:
    """A loop helper that yields at specific interval.

    Args:
        interval_seconds (timedelta | float): Expected interval between each yield.
        allow_skip (bool, optional): Whether to allow frame skip. Defaults to False.
        on_slow (LoopSkipCallback, optional): A callback function to be called when
            the duration of some iteration exceeds expected interval. The argument
            of the callback indicates the number of continuous slow iterations.
            Defaults to None.

    Yields:
        begin_timestamp (float): The timestamp when current loop begins, returned
            by `time.monotonic()`.
    """

    if isinstance(interval_seconds, timedelta):
        interval_seconds = interval_seconds.total_seconds()

    continuous_slow_count = 0

    while True:

        timestamp_begin = monotonic()
        yield timestamp_begin

        timestamp_end = monotonic()
        if timestamp_end - timestamp_begin < interval_seconds:

            loop_duration = timestamp_end - timestamp_begin
            sleep_time = interval_seconds - loop_duration

            if sleep_time < 0:
                continuous_slow_count += 1
                if on_slow:
                    on_slow(continuous_slow_count)
                    if allow_skip:
                        timestamp_skip = monotonic()
                        sleep_time = (
                            timestamp_skip - timestamp_begin
                        ) % interval_seconds
                    else:
                        sleep_time = 0
                else:
                    if allow_skip:
                        sleep_time %= interval_seconds
                    else:
                        sleep_time = 0
            else:
                continuous_slow_count = 0

            sleep(sleep_time)
