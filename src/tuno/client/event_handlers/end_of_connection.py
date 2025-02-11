from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


def handler(parsed_data: str, app: "UnoApp") -> None:

    client = app.client
    assert client

    client.reset(parsed_data)
    app.switch_mode("connect")

    app.notify_error(
        parsed_data,
        title="Connection Stopped",
    )
