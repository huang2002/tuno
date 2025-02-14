from textual.app import ComposeResult
from textual.containers import HorizontalScroll
from textual.reactive import reactive
from textual.widgets import Button

from tuno.shared.sse_events import GameStateEvent


class Actions(HorizontalScroll):

    BORDER_TITLE = "Actions"
    DEFAULT_CSS = """
    Actions {
        padding: 1 2;
        align: center middle;

        Button {
            min-width: 11;
            margin: 0 3;
        }

        Button#action-show-rules {
            border-top: tall $secondary-lighten-2;
            border-bottom: tall $secondary-darken-2;
            background: $secondary;

            &:hover {
                background: $secondary-darken-1;
                border-top: tall $primary;
            }
        }
    }
    """

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
