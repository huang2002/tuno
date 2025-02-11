from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Self

from requests import RequestException

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


class ApiContext(AbstractContextManager["ApiContext"]):

    error_title: str
    app: "UnoApp"

    def __init__(self, error_title: str, *, app: "UnoApp") -> None:
        self.error_title = error_title
        self.app = app

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> bool:

        if exception:

            if isinstance(exception, RequestException):

                error_message = "RequestException caught in ApiContext:"
                self.app.log.warning(
                    error_message,
                    exception,
                )

                if exception.response is not None:
                    error_message = exception.response.text
                else:
                    error_message = f"{error_message} {exception!r}"

                self.app.notify_error(
                    error_message,
                    title=self.error_title,
                )

                return True  # stop exception propagation

            else:

                error_message = "Unknown exception caught in ApiContext:"
                self.app.log.error(
                    error_message,
                    exception,
                )
                self.app.notify_error(
                    f"{error_message} {exception!r}",
                    title=self.error_title,
                )

        return False  #  propagate the exception
