from textual.reactive import reactive
from textual.widgets import Label

from tuno.shared.deck import BasicCardColor


class CardColorLabel(Label):

    DEFAULT_CSS = """
    CardColorLabel {
        width: 100%;
        height: 100%;
        content-align-horizontal: center;
        color: $text;
    }
    """

    data: reactive[BasicCardColor | None] = reactive(None)

    def watch_data(self, data: BasicCardColor | None) -> None:
        if data is None:
            self.styles.background = "gray"
            self.update("???")
            self.tooltip = None
        else:
            self.styles.background = data
            self.update(data)
            self.tooltip = data
