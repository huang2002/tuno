from typing import TYPE_CHECKING

from tuno.shared.sse_events import GameStateEvent

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


def handler(parsed_data: GameStateEvent.DataType, app: "UnoApp") -> None:

    assert app.client is not None
    app.client.game_state = parsed_data

    app.post_message(app.GameStateUpdate(parsed_data))
