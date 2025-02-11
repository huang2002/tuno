from dataclasses import dataclass
from functools import partialmethod

from textual import on
from textual.app import App
from textual.message import Message

from tuno.client.config import (
    NOTIFICATION_TIMEOUT_DEFAULT,
    NOTIFICATION_TIMEOUT_ERROR,
)
from tuno.shared.deck import Deck
from tuno.shared.sse_events import GameStateEvent

from .components.ConnectScreen import ConnectScreen
from .components.InGameScreen import InGameScreen
from .UnoClient import UnoClient


class UnoApp(App[object]):

    NOTIFICATION_TIMEOUT = NOTIFICATION_TIMEOUT_DEFAULT.total_seconds()
    MODES = {
        "connect": ConnectScreen,
        "in-game": InGameScreen,
    }

    @dataclass
    class GameStateUpdate(Message):
        game_state: GameStateEvent.DataType

    @dataclass
    class CardsUpdate(Message):
        cards: Deck

    client: UnoClient | None

    notify_error = partialmethod(
        App.notify,
        severity="error",
        timeout=NOTIFICATION_TIMEOUT_ERROR.total_seconds(),
    )

    def on_mount(self) -> None:
        self.client = UnoClient(self)
        self.switch_mode("connect")

    def on_unmount(self) -> None:
        client = self.client
        assert client is not None
        with client.subscription_lock:
            if client.subscription:
                client.subscription.close()
                client.subscription = None
                self.log.debug("Subscription detached.")

    @on(ConnectScreen.Connected)
    def on_connected(self) -> None:

        self.switch_mode("in-game")

        screen = self.screen
        assert isinstance(screen, InGameScreen)

        client = self.client
        assert client is not None

        screen.game_state = client.game_state

    @on(GameStateUpdate)
    def on_game_state_update(self, message: GameStateUpdate) -> None:
        screen = self.screen
        if isinstance(screen, InGameScreen):
            screen.game_state = message.game_state
            self.log.debug("Updated game state on InGameScreen.")

    @on(CardsUpdate)
    def on_cards_update(self, message: CardsUpdate) -> None:
        screen = self.screen
        if isinstance(screen, InGameScreen):
            screen.cards = message.cards
            self.log.debug("Updated game state on InGameScreen.")
