from time import monotonic


class LazyTimer:

    timeout: float

    __start_time: float | None = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    @property
    def started(self) -> bool:
        return self.__start_time is not None

    @started.setter
    def started(self, value: bool) -> None:
        if value:
            self.__start_time = monotonic()
        else:
            self.__start_time = None

    @property
    def time_up(self) -> bool:
        start_time = self.__start_time
        if start_time is None:
            return False
        else:
            now = monotonic()
            return now - start_time >= self.timeout
