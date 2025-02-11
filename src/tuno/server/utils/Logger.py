from enum import IntEnum
from functools import partialmethod
from threading import RLock
from time import strftime

import click


class LogLevel(IntEnum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class Logger:

    name: str
    level: LogLevel = LogLevel.INFO
    lock = RLock()  # cross-thread io lock

    def __init__(self, name: str) -> None:
        self.name = name

    def __log(
        self,
        content: str,
        *,
        level: LogLevel,
        label: str,
        fg: str,
        bg: str,
    ) -> None:
        if level < self.level:
            return
        timestamp = strftime("%Y-%m-%d %H:%M:%S")
        message = (
            click.style(
                f"[{timestamp}] {label:>5s} ({self.name})",
                fg=fg,
                bg=bg,
            )
            + " "
            + content
        )
        with self.lock:
            click.echo(message)

    debug = partialmethod(
        __log,
        level=LogLevel.DEBUG,
        label="DEBUG",
        fg="blue",
        bg="black",
    )

    info = partialmethod(
        __log,
        level=LogLevel.INFO,
        label="INFO",
        fg="green",
        bg="black",
    )

    warn = partialmethod(
        __log,
        level=LogLevel.WARN,
        label="WARN",
        fg="yellow",
        bg="black",
    )

    error = partialmethod(
        __log,
        level=LogLevel.ERROR,
        label="ERROR",
        fg="red",
        bg="yellow",
    )
