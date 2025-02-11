from textual.app import ComposeResult
from textual.containers import HorizontalScroll
from textual.reactive import reactive
from textual.widgets import Button

from tuno.shared.sse_events import GameStateEvent


class Actions(HorizontalScroll):

    BORDER_TITLE = "Actions"

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)
    game_started: reactive[bool] = reactive(False, recompose=True)

    def compose(self) -> ComposeResult:
        if self.game_started:
            yield Button(
                "Stop",
                id="action-stop-game",
                variant="error",
                action="screen.stop_game",
            )
        else:
            yield Button(
                "Start",
                id="action-start-game",
                variant="success",
                action="screen.start_game",
            )
            yield Button(
                "Rules",
                id="action-show-rules",
                action="screen.show_rules",
            )

    def watch_game_state(
        self,
        game_state: GameStateEvent.DataType | None,
    ) -> None:
        self.game_started = game_state["started"] if game_state else False
        self.disabled = game_state is None
