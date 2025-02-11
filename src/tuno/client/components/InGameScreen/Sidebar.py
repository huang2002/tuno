from typing import Final

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label

from tuno.shared.sse_events import GameStateEvent

# TODO: display pile sizes


class Sidebar(VerticalScroll):

    __CLASS_GAME_STATUS_STARTED: Final = "started"
    __CLASS_GAME_STATUS_PENDING: Final = "pending"
    __CLASS_CURRENT_PLAYER_ACTIVE: Final = "active"
    __CLASS_CURRENT_PLAYER_WAITING: Final = "waiting"

    BORDER_TITLE = "Game Info"

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)

    def compose(self) -> ComposeResult:

        label_status = Label(
            "...",
            id="sidebar-info-status",
            classes="sidebar-info-section",
        )
        label_status.border_title = "Game Status"
        yield label_status

        label_capacity = Label(
            "-/-",
            id="sidebar-info-capacity",
            classes="sidebar-info-section",
        )
        label_capacity.border_title = "Capacity"
        yield label_capacity

        label_current_player = Label(
            "-/-",
            id="sidebar-info-current-player",
            classes="sidebar-info-section",
        )
        label_current_player.border_title = "Current"
        yield label_current_player

    def watch_game_state(
        self,
        game_state: GameStateEvent.DataType | None,
    ) -> None:

        from tuno.client.UnoApp import UnoApp

        app = self.app
        assert isinstance(app, UnoApp)
        assert app.client is not None

        # -- Game Status --
        label_game_status = self.query_exactly_one(
            "#sidebar-info-status",
            Label,
        )
        if game_state:
            if game_state["started"]:
                game_status_display = "Started"
                label_game_status.add_class(self.__CLASS_GAME_STATUS_STARTED)
                label_game_status.remove_class(self.__CLASS_GAME_STATUS_PENDING)
            else:
                game_status_display = "Pending"
                label_game_status.remove_class(self.__CLASS_GAME_STATUS_STARTED)
                label_game_status.add_class(self.__CLASS_GAME_STATUS_PENDING)
        else:
            game_status_display = "..."
            label_game_status.remove_class(
                self.__CLASS_GAME_STATUS_STARTED,
                self.__CLASS_GAME_STATUS_PENDING,
            )
        label_game_status.update(game_status_display)

        # -- Player Capacity --
        label_player_capacity = self.query_exactly_one(
            "#sidebar-info-capacity",
            Label,
        )
        if game_state:
            player_count = len(game_state["players"])
            player_capacity = game_state["rules"]["player_capacity"]
            label_player_capacity.update(f"{player_count}/{player_capacity}")
        else:
            label_player_capacity.update("-/-")

        # -- Current Player --
        label_current_player = self.query_exactly_one(
            "#sidebar-info-current-player",
            Label,
        )
        current_player_name = "N/A"
        if game_state and game_state["started"]:
            current_player_index = game_state["current_player_index"]
            players = game_state["players"]
            if 0 <= current_player_index < len(players):
                current_player_name = players[current_player_index]["name"]
            else:
                self.log.error(
                    "Invalid value for `current_player_index`:",
                    current_player_index,
                )
            if current_player_name == app.client.player_name:
                label_current_player.add_class(
                    self.__CLASS_CURRENT_PLAYER_ACTIVE
                )
                label_current_player.remove_class(
                    self.__CLASS_CURRENT_PLAYER_WAITING
                )
            else:
                label_current_player.remove_class(
                    self.__CLASS_CURRENT_PLAYER_ACTIVE
                )
                label_current_player.add_class(
                    self.__CLASS_CURRENT_PLAYER_WAITING
                )
        else:
            label_current_player.remove_class(
                self.__CLASS_CURRENT_PLAYER_ACTIVE,
                self.__CLASS_CURRENT_PLAYER_WAITING,
            )
        label_current_player.update(current_player_name)
