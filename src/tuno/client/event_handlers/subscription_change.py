from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


def handler(parsed_data: None, app: "UnoApp") -> None:
    app.notify(
        "Connection has been replaced by a new one.",
        title="Subscription Change",
        severity="warning",
    )
