from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Literal, Self

from tuno.client.components.LoadingScreen import LoadingScreen

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


class LoadingContext(AbstractContextManager["LoadingContext"]):

    message: str
    app: "UnoApp"
    loading_screen: LoadingScreen | None

    def __init__(self, message: str, *, app: "UnoApp") -> None:
        self.message = message
        self.app = app
        self.loading_screen = None

    def __enter__(self) -> Self:
        if self.loading_screen is not None:
            raise RuntimeError("LoadingContext entered more than once")
        self.loading_screen = LoadingScreen(self.message)
        self.app.call_from_thread(
            self.app.push_screen,
            self.loading_screen,
        )
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        if self.loading_screen is None:
            raise RuntimeError("LoadingContext exited without entering")
        self.app.call_from_thread(self.loading_screen.dismiss)
        self.loading_screen = None
        return False  # propagate exceptions
