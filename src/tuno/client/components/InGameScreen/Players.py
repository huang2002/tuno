from typing import TYPE_CHECKING, Final, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from tuno.shared.sse_events import GameStateEvent


class PlayerCard(Widget):

    __CLASS_PLAYER_ACTIVE: Final = "active"
    __CLASS_PLAYER_CONNECTED: Final = "connected"
    __CLASS_PLAYER_DISCONNECTED: Final = "disconnected"

    DEFAULT_CSS = """
    PlayerCard {
        height: 4;
        border: round $panel;
        padding: 0 1;
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1 1;
        grid-columns: 2 1fr;

        &.active {
            border: heavy $success;
        }

        .player-card-connected {
            width: 1;
            color: $foreground-muted;

            &.connected {
                color: $text-success;
            }
            &.disconnected {
                color: $text-error;
            }
        }

        .player-card-name {
            width: 100%;
        }

        .player-card-count {
            column-span: 2;
            align-horizontal: right;

            .player-card-count-label {
                color: $foreground-muted;
            }
        }
    }
    """

    active: reactive[bool] = reactive(False)
    data: reactive[GameStateEvent.PlayerDataType | None] = reactive(None)

    def compose(self) -> ComposeResult:

        label_connected = Label("●", classes="player-card-connected")
        label_connected.tooltip = "Connection: N/A"

        label_name = Label("???", classes="player-card-name")
        label_name.tooltip = "Player name"

        yield label_connected
        yield label_name
        yield Horizontal(
            Label(
                "Cards: ",
                classes="player-card-count-label",
            ),
            Label(
                "...",
                classes="player-card-count-value",
            ),
            classes="player-card-count",
        )

    def watch_active(self, active: bool) -> None:
        if active:
            self.add_class(self.__CLASS_PLAYER_ACTIVE)
        else:
            self.remove_class(self.__CLASS_PLAYER_ACTIVE)

    def watch_data(self, data: GameStateEvent.PlayerDataType | None) -> None:

        label_name = self.query_exactly_one(
            ".player-card-name",
            Label,
        )
        if data:
            label_name.update(data["name"])
            label_name.tooltip = f"Player name: {data["name"]}"
            if data["connected"]:
                label_name.add_class(self.__CLASS_PLAYER_CONNECTED)
                label_name.remove_class(self.__CLASS_PLAYER_DISCONNECTED)
            else:
                label_name.remove_class(self.__CLASS_PLAYER_CONNECTED)
                label_name.add_class(self.__CLASS_PLAYER_DISCONNECTED)
        else:
            label_name.update("???")
            label_name.remove_class(self.__CLASS_PLAYER_CONNECTED)
            label_name.add_class(self.__CLASS_PLAYER_DISCONNECTED)
            label_name.tooltip = "Player name"

        label_connected = self.query_exactly_one(
            ".player-card-connected",
            Label,
        )
        if data:
            if data["connected"]:
                label_connected.tooltip = "Connected"
                label_connected.add_class(self.__CLASS_PLAYER_CONNECTED)
                label_connected.remove_class(self.__CLASS_PLAYER_DISCONNECTED)
            else:
                label_connected.tooltip = "Disconnected"
                label_connected.remove_class(self.__CLASS_PLAYER_CONNECTED)
                label_connected.add_class(self.__CLASS_PLAYER_DISCONNECTED)
        else:
            label_connected.tooltip = "Connection: N/A"
            label_connected.remove_class(
                self.__CLASS_PLAYER_CONNECTED,
                self.__CLASS_PLAYER_DISCONNECTED,
            )

        label_card_count_value = self.query_exactly_one(
            ".player-card-count-value",
            Label,
        )
        card_count_display = "N/A"
        if data:
            card_count = data["card_count"]
            if card_count >= 0:
                card_count_display = str(card_count)
        label_card_count_value.update(card_count_display)


class Players(VerticalScroll):

    BORDER_TITLE = "Players"
    DEFAULT_CSS = """
    Players {
        padding: 1 2;
        layout: grid;
        grid-size: 3;
        grid-rows: 4;
        grid-gutter: 0 1;

        LoadingIndicator {
            background: transparent;
        }
    }
    """

    game_state: reactive[GameStateEvent.DataType | None] = reactive(None)

    async def watch_game_state(
        self,
        game_state: GameStateEvent.DataType | None,
    ) -> None:

        if not game_state:
            self.remove_children()
            self.loading = True
            return

        self.loading = False

        async with self.batch():

            children = self.children
            assert all(isinstance(child, PlayerCard) for child in children)
            if TYPE_CHECKING:
                children = cast(list[PlayerCard], children)

            players = game_state["players"]
            current_child_count = len(children)
            for i, player_data in enumerate(players[:current_child_count]):
                children[i].data = player_data
                children[i].active = i == game_state["current_player_index"]

            player_count = len(players)
            if player_count > current_child_count:
                new_players = players[current_child_count:]
                new_children: list[PlayerCard] = []
                for player_data in new_players:
                    new_children.append(PlayerCard())
                await self.mount(*new_children)
                for i, (child, data) in enumerate(
                    zip(new_children, new_players, strict=True)
                ):
                    child.data = data
                    child.active = i == game_state["current_player_index"]
            elif player_count < current_child_count:
                self.remove_children(children[player_count:])
