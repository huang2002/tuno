from typing import cast

from textual import work
from textual.app import ComposeResult
from textual.containers import HorizontalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header

from tuno.client.components.CardsScreen import CardsScreen
from tuno.client.components.Players import Players
from tuno.client.components.RulesScreen import RulesScreen
from tuno.client.utils.LoadingContext import LoadingContext
from tuno.shared.deck import Deck
from tuno.shared.sse_events import GameStateEvent

from .Sidebar import Sidebar


class InGameScreen(Screen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+t", "play", "Play"),
        ("ctrl+r", "show_rules", "Rules"),
    ]

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)
    cards: reactive[Deck] = reactive([])

    def compose(self) -> ComposeResult:

        actions_container = HorizontalScroll(
            Button(
                "Play",
                id="action-show-play",
                variant="primary",
                action="screen.play",
            ),
            Button(
                "Rules",
                id="action-show-rules",
                variant="warning",
                action="screen.show_rules",
            ),
            Button(
                "Stop",
                id="action-stop-game",
                variant="error",
                action="screen.stop_game",
            ),
            id="actions",
        )
        actions_container.border_title = "Actions"

        yield Header(show_clock=True)
        yield Sidebar().data_bind(InGameScreen.game_state)
        yield Players().data_bind(InGameScreen.game_state)
        yield actions_container
        yield Footer()

    def watch_game_state(self, game_state: GameStateEvent.DataType | None) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        self.sub_title = client.get_connection_display()

    def action_play(self) -> None:
        self.app.push_screen(CardsScreen())

    def action_show_rules(self) -> None:
        self.app.push_screen(RulesScreen(readonly=True))

    @work(thread=True)
    def action_stop_game(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        with LoadingContext("Stopping game...", app=app):
            client.stop_game()
