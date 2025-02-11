from typing import TYPE_CHECKING

from tuno.shared.sse_events import NotificationEvent

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


def handler(parsed_data: NotificationEvent.DataType, app: "UnoApp") -> None:
    app.notify(
        parsed_data["message"],
        title=parsed_data["title"],
    )
