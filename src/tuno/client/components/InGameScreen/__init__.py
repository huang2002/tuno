from typing import cast

from textual import work
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header

from tuno.client.components.RulesScreen import RulesScreen
from tuno.client.utils.LoadingContext import LoadingContext
from tuno.shared.deck import Deck
from tuno.shared.sse_events import GameStateEvent

from .Actions import Actions
from .Players import Players
from .Sidebar import Sidebar


class InGameScreen(Screen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+g", "start_game", "Start"),
        ("ctrl+r", "show_rules", "Rules"),
    ]

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)
    cards: reactive[Deck] = reactive([])

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Sidebar().data_bind(InGameScreen.game_state)
        yield Players().data_bind(InGameScreen.game_state)
        yield Actions().data_bind(InGameScreen.game_state)
        yield Footer()

    def on_screen_resume(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        self.sub_title = client.get_connection_display()

    def action_show_rules(self) -> None:
        self.app.push_screen(RulesScreen())

    @work(thread=True)
    def action_start_game(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        with LoadingContext("Starting game...", app=app):
            client.start_game()

    @work(thread=True)
    def action_stop_game(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        with LoadingContext("Stopping game...", app=app):
            client.stop_game()
