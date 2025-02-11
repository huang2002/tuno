from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator


class LoadingScreen(ModalScreen[object]):

    CSS_PATH = "styles.tcss"

    message: str

    def __init__(self, message: str = "Loading...") -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.message, id="loading-message"),
            LoadingIndicator(),
            id="loading-container",
        )
