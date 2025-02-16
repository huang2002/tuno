from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class CheckboxContainer(Widget):

    DEFAULT_CSS = """
    CheckboxContainer {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 3 1fr;
        grid-gutter: 0 1;
        border: round $border-blurred;
        padding: 0 1;

        .checkbox-status {
            color: $foreground-muted;
        }

        &.checked {
            border: round $border;

            .checkbox-status {
                color: $text-success;
            }
        }
    }
    """

    __STATUS_CHECKED = "(@)"
    __STATUS_UNCHECKED = "( )"
    __CLASS_CHECKED = "checked"

    checked: reactive[bool] = reactive(False)

    content: Widget

    def __init__(self, content: Widget) -> None:
        super().__init__()
        self.content = content

    def compose(self) -> ComposeResult:
        yield Label(classes="checkbox-status", markup=False)
        yield self.content

    def watch_checked(self, checked: bool) -> None:
        label = self.query_exactly_one(".checkbox-status", Label)
        label.update(self.__STATUS_CHECKED if checked else self.__STATUS_UNCHECKED)
        self.set_class(checked, self.__CLASS_CHECKED)

    def on_click(self) -> None:
        self.checked = not self.checked
