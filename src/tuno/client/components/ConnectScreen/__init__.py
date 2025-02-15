from os import environ
from typing import cast

from textual.app import ComposeResult
from textual.screen import Screen
from textual.validation import Regex
from textual.widgets import Button, Footer, Header, Input

from tuno.client.config import (
    ENV_KEY_CONNECTION,
    ENV_KEY_PLAYER_NAME,
    ENV_KEY_SERVER_ADDRESS,
)
from tuno.shared.constraints import PLAYER_NAME_PATTERN

player_name_validator = Regex(PLAYER_NAME_PATTERN)


class ConnectScreen(Screen[object]):

    TITLE = "UNO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+j", "submit", "Submit"),
    ]

    def compose(self) -> ComposeResult:

        default_player_name = ""
        default_server_address = ""
        default_connection_info = environ.get(ENV_KEY_CONNECTION, "")
        if default_connection_info and "@" in default_connection_info:
            default_player_name, _, default_server_address = (
                default_connection_info.partition("@")
            )

        default_player_name = environ.get(
            ENV_KEY_PLAYER_NAME,
            default_player_name,
        )
        if not player_name_validator.validate(default_player_name).is_valid:
            default_player_name = ""
        if default_player_name:
            self.log.debug("Found default player name:", default_player_name)

        default_server_address = environ.get(
            ENV_KEY_SERVER_ADDRESS,
            default_server_address,
        )
        if default_server_address:
            self.log.debug(
                "Found default server address:",
                default_server_address,
            )

        player_name_pattern_display = PLAYER_NAME_PATTERN.pattern
        input_player_name = Input(
            id="player_name",
            classes="form-item",
            placeholder=f"Your name ({player_name_pattern_display})",
            validators=[player_name_validator],
            value=default_player_name,
        )
        input_player_name.border_title = "Player Name"

        input_server_address = Input(
            id="server_address",
            classes="form-item",
            placeholder="HOST:PORT",
            value=default_server_address,
        )
        input_server_address.border_title = "Server Address"

        yield Header(show_clock=True)
        yield input_player_name
        yield input_server_address
        yield Button(
            "JOIN",
            id="submit",
            classes="form-item",
            variant="primary",
            action="submit",
            disabled=True,
        )
        yield Footer()

    def action_submit(self) -> None:

        from tuno.client.UnoApp import UnoApp

        app = cast(UnoApp, self.app)
        assert isinstance(app, UnoApp)

        input_player_name = self.query_exactly_one("#player_name", Input)
        player_name = input_player_name.value
        if not player_name or not input_player_name.is_valid:
            self.log.warning(f"Invalid player name: {player_name}")
            return

        input_server_address = self.query_exactly_one("#server_address", Input)
        server_address = input_server_address.value
        if not server_address or not input_server_address.is_valid:
            self.log.warning(f"Invalid server address: {server_address}")
            return

        submit_button = self.query_exactly_one("#submit", Button)

        input_player_name.disabled = True
        input_server_address.disabled = True
        submit_button.disabled = True
        submit_button.loading = True

        def on_success() -> None:
            app.clear_notifications()
            app.notify("Connected to game server!")

        def on_failure(error_message: str) -> None:
            input_player_name.disabled = False
            input_server_address.disabled = False
            submit_button.disabled = False
            submit_button.loading = False

            app.notify_error(
                error_message,
                title="Connection Error",
            )

        assert app.client is not None
        app.client.connect(
            server_address=server_address,
            player_name=player_name,
            on_success=on_success,
            on_failure=on_failure,
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if not event.value or not event.input.is_valid:
            event.input.add_class("invalid")
        else:
            event.input.remove_class("invalid")
        self.query_exactly_one("#submit", Button).disabled = not all(
            (input.value and input.is_valid) for input in self.query(Input)
        )
