from typing import cast

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalScroll, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, Select

from tuno.client.components.CardLabel import CardLabel
from tuno.client.components.CheckboxContainer import CheckboxContainer
from tuno.client.utils.LoadingContext import LoadingContext
from tuno.shared.deck import Card, basic_card_colors


class CardCheckbox(CheckboxContainer):

    card_data: Card

    def __init__(self, card_data: Card) -> None:
        super().__init__(CardLabel())
        self.card_data = card_data

    def on_mount(self) -> None:
        self.query_exactly_one(CardLabel).data = self.card_data


class CardsScreen(ModalScreen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+s", "screen.submit", "Submit"),
        ("escape", "screen.dismiss", "Cancel"),
    ]

    def compose(self) -> ComposeResult:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        yield Header(show_clock=True)
        with Vertical(id="cards-window"):
            yield Label("Select cards to play:", id="cards-title")
            yield VerticalScroll(id="cards-container")
            with Horizontal(id="cards-color-select-container"):
                yield Label(
                    "Change color: ",
                    id="cards-color-select-label",
                )
                yield Select[str](
                    ((color, color) for color in basic_card_colors),
                    id="cards-color-select",
                    prompt="(none)",
                    tooltip="Color to change to.",
                )
            with HorizontalScroll(id="cards-actions"):
                yield Button(
                    "Submit",
                    id="rules-submit",
                    variant="primary",
                    action="screen.submit",
                )
                yield Button(
                    "Reset",
                    variant="warning",
                    action="screen.reset",
                )
                yield Button(
                    "Cancel",
                    variant="error",
                    action="screen.dismiss",
                )
        yield Footer()

    def on_mount(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None

        self.sub_title = client.get_connection_display()

        cards_container = self.query_exactly_one("#cards-container", VerticalScroll)
        for card in client.cards:
            cards_container.mount(CardCheckbox(card))

    @work(thread=True)
    def action_submit(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        assert client.game_state is not None

        selected_cards = [
            card_widget.card_data
            for card_widget in self.query(CardCheckbox)
            if card_widget.checked
        ]

        selected_card_ids = [card["id"] for card in selected_cards]
        color_select_value = self.query_exactly_one(Select).value
        with LoadingContext("Playing...", app=app):
            client.play(
                selected_card_ids,
                color=(
                    None
                    if color_select_value is Select.BLANK
                    else cast(str, color_select_value)
                ),
            )
            self.app.call_from_thread(self.dismiss)

    def action_reset(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        assert client.game_state is not None

        for card_checkbox in self.query(CardCheckbox):
            card_checkbox.checked = False

        self.query_exactly_one("#cards-color-select", Select).value = Select.BLANK
