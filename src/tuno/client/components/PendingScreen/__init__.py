from typing import cast

from textual import work
from textual.app import ComposeResult
from textual.containers import HorizontalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header

from tuno.client.components.Players import Players
from tuno.client.components.RulesScreen import RulesScreen
from tuno.client.utils.LoadingContext import LoadingContext
from tuno.shared.sse_events import GameStateEvent


class PendingScreen(Screen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+g", "start_game", "Start"),
        ("ctrl+r", "show_rules", "Rules"),
    ]

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)

    def compose(self) -> ComposeResult:

        actions_container = HorizontalScroll(
            Button(
                "Start",
                id="action-start-game",
                variant="success",
                action="screen.start_game",
            ),
            Button(
                "Rules",
                id="action-show-rules",
                action="screen.show_rules",
            ),
            id="actions",
        )
        actions_container.border_title = "Actions"

        yield Header(show_clock=True)
        yield Players().data_bind(PendingScreen.game_state)
        yield actions_container
        yield Footer()

    def on_screen_resume(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        self.sub_title = client.get_connection_display()

    def action_show_rules(self) -> None:
        self.app.push_screen(RulesScreen(readonly=False))

    @work(thread=True)
    def action_start_game(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        with LoadingContext("Starting game...", app=app):
            client.start_game()
