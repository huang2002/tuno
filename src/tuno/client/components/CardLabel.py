from textual.reactive import reactive
from textual.widgets import Label

from tuno.shared.deck import Card


class CardLabel(Label):

    DEFAULT_CSS = """
    CardLabel {
        width: 100%;
        height: 100%;
        content-align-horizontal: center;
        color: $text;
    }
    """

    data: reactive[Card | None] = reactive(None)

    def watch_data(self, data: Card | None) -> None:

        if data is None:
            self.styles.background = "gray"
            self.update("???")
            self.tooltip = None
            return

        self.styles.background = data["color"]

        content = ""
        if data["color"] == "black":
            content += ""
        else:
            content += data["color"].title() + " "
        if data["type"] == "number":
            content += str(data["number"])
        else:
            content += data["effect"]
        self.update(content)
        self.tooltip = content
