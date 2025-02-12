from dataclasses import dataclass
from typing import Final, cast

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Right, Vertical, VerticalScroll
from textual.events import DescendantBlur, DescendantFocus
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import Function as FunctionValidator
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, Switch

from tuno.client.utils.LoadingContext import LoadingContext
from tuno.shared.rules import (
    GameRules,
    RuleValidationException,
    get_rule_annotation,
)


class RulesFormItem(Widget):

    __CLASS_FOCUS: Final = "focus"
    __CLASS_INVALID: Final = "invalid"

    rule_key: str
    rule_type: type
    rule_hint: str
    textual_validator: FunctionValidator | None
    focused_descendants: set[Widget]

    def __init__(self, rule_key: str) -> None:
        super().__init__()

        self.rule_key = rule_key
        self.focused_descendants = set()

        rule_annotation = get_rule_annotation(rule_key)
        self.rule_type = rule_annotation.type
        self.rule_hint = rule_annotation.hint

        rule_validator = rule_annotation.validator
        if rule_validator:

            def validator_wrapper(value: str | bool) -> bool:
                if isinstance(value, str):
                    if value != "":
                        value = rule_annotation.type(value)
                    else:
                        value = rule_annotation.type()
                try:
                    assert rule_validator is not None
                    rule_validator.validate(value)
                except RuleValidationException as exception:
                    textual_validator.failure_description = exception.message
                    return False
                else:
                    return True

            textual_validator = FunctionValidator(validator_wrapper)
            self.textual_validator = textual_validator

        else:
            self.textual_validator = None

    def compose(self) -> ComposeResult:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        assert client.game_state is not None

        rule_key = self.rule_key
        rule_hint = self.rule_hint
        rule_text = f"{rule_key} ({rule_hint})"
        yield Label(rule_text)

        self.tooltip = rule_text

        rule_type = self.rule_type
        current_rules = client.game_state["rules"]
        current_value = current_rules[rule_key]  # type: ignore[literal-required]
        input_widget: Widget
        if rule_type is int:
            input_widget = Input(
                value=str(current_value),
                type="integer",
                classes="rule-input",
                validators=self.textual_validator,
                placeholder=rule_hint,
                tooltip=rule_hint,
            )
        elif rule_type is bool:
            input_widget = Switch(
                value=current_value,
                classes="rule-input",
                tooltip=rule_hint,
            )
        else:
            raise NotImplementedError()
        yield Right(input_widget)

    @on(DescendantFocus)
    def on_descendant_focus(self, event: DescendantFocus) -> None:
        self.focused_descendants.add(event.control)
        self.set_class(len(self.focused_descendants) > 0, self.__CLASS_FOCUS)

    @on(DescendantBlur)
    def on_descendant_blur(self, event: DescendantBlur) -> None:
        self.focused_descendants.discard(event.control)
        self.set_class(len(self.focused_descendants) > 0, self.__CLASS_FOCUS)

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        event.control.set_class(
            not event.control.is_valid,
            self.__CLASS_INVALID,
        )

    @on(DescendantFocus)
    def get_rule_value(self) -> object:
        input_widget = self.query_exactly_one(".rule-input")
        if isinstance(input_widget, Input):
            if input_widget.is_valid:
                return self.rule_type(input_widget.value)
            else:
                return None
        elif isinstance(input_widget, Switch):
            return input_widget.value
        else:
            return None

    def set_rule_value(self, value: object) -> None:
        input_widget = self.query_exactly_one(".rule-input")
        if isinstance(input_widget, Input):
            assert isinstance(value, self.rule_type)
            input_widget.value = str(value)
        elif isinstance(input_widget, Switch):
            assert isinstance(value, bool)
            input_widget.value = value
        else:
            raise NotImplementedError()


class RulesForm(VerticalScroll):

    @dataclass
    class FormValidationChanged(Message):
        all_valid: bool

    invalid_inputs: reactive[set[Input]] = reactive(set, init=False)
    all_valid: reactive[bool] = reactive(True, init=False)

    def compute_all_valid(self) -> bool:
        return len(self.invalid_inputs) == 0

    def compose(self) -> ComposeResult:
        for key in GameRules.__annotations__.keys():
            yield RulesFormItem(key)

    def on_mount(self) -> None:
        invalid_input_detected = False
        for input_widget in self.query(Input):
            if not input_widget.is_valid:
                invalid_input_detected = True
                self.invalid_inputs.add(input_widget)
        if invalid_input_detected:
            self.mutate_reactive(RulesForm.invalid_inputs)

    @on(Input.Changed)
    def on_input_changed(self, message: Input.Changed) -> None:
        if message.control.is_valid:
            self.invalid_inputs.discard(message.control)
        else:
            self.invalid_inputs.add(message.control)
        self.mutate_reactive(RulesForm.invalid_inputs)

    def watch_all_valid(self, all_valid: bool) -> None:
        self.post_message(self.FormValidationChanged(all_valid))


class RulesScreen(ModalScreen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+s", "screen.submit", "Submit"),
        ("escape", "screen.dismiss", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(
            Label("Game Rules", id="rules-title"),
            RulesForm(),
            Horizontal(
                Button(
                    "Submit",
                    id="rules-submit",
                    variant="primary",
                    action="screen.submit",
                ),
                Button("Reset", variant="error", action="screen.reset"),
                Button("Cancel", action="screen.dismiss"),
                id="rules-actions",
            ),
            id="rules-window",
        )
        yield Footer()

    async def on_screen_resume(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        self.sub_title = client.get_connection_display()

        await self.query_exactly_one(RulesForm).recompose()

    @on(RulesForm.FormValidationChanged)
    def on_form_validation_changed(
        self,
        message: RulesForm.FormValidationChanged,
    ) -> None:
        self.query_exactly_one("#rules-submit", Button).disabled = (
            not message.all_valid
        )

    @work(thread=True)
    def action_submit(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        assert client.game_state is not None

        current_rules = client.game_state["rules"]
        modified_rules: dict[str, object] = {}
        for form_item in self.query(RulesFormItem):
            rule_key = form_item.rule_key
            old_value = current_rules[rule_key]  # type: ignore[literal-required]
            new_value = form_item.get_rule_value()
            if new_value != old_value:
                modified_rules[rule_key] = new_value

        if len(modified_rules) == 0:
            self.app.notify(
                "Rules are unchanged.",
                title="Submission Ignored",
                severity="warning",
            )
            return

        with LoadingContext("Updating rules...", app=app):
            client.update_rules(modified_rules)

    def action_reset(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)

        client = app.client
        assert client is not None
        assert client.game_state is not None

        current_rules = client.game_state["rules"]
        for form_item in self.query(RulesFormItem):
            rule_key = form_item.rule_key
            rule_value = current_rules[rule_key]  # type: ignore[literal-required]
            form_item.set_rule_value(rule_value)
