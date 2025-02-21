from dataclasses import dataclass
from functools import partialmethod

from textual import on
from textual.app import App
from textual.message import Message
from textual.screen import ModalScreen

from tuno.client.config import (
    NOTIFICATION_TIMEOUT_DEFAULT,
    NOTIFICATION_TIMEOUT_ERROR,
)
from tuno.shared.deck import Deck
from tuno.shared.sse_events import GameStateEvent

from .components.ConnectScreen import ConnectScreen
from .components.InGameScreen import InGameScreen
from .components.PendingScreen import PendingScreen
from .UnoClient import UnoClient


class UnoApp(App[object]):

    NOTIFICATION_TIMEOUT = NOTIFICATION_TIMEOUT_DEFAULT.total_seconds()
    MODES = {
        "connect": ConnectScreen,
        "pending": PendingScreen,
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

    @on(GameStateUpdate)
    async def on_game_state_update(self, message: GameStateUpdate) -> None:

        game_state = message.game_state

        if game_state:
            target_mode = "in-game" if game_state["started"] else "pending"
            if self.current_mode != target_mode:
                await self.switch_mode(target_mode)
                for modal_screen in self.query(ModalScreen):
                    modal_screen.dismiss()
        else:
            await self.switch_mode("connect")

        for screen in self.screen_stack:
            if hasattr(screen, "game_state"):
                setattr(screen, "game_state", game_state)
                self.log.debug(f"Updated game state on current {screen.name}.")

    @on(CardsUpdate)
    def on_cards_update(self, message: CardsUpdate) -> None:
        screen = self.screen
        if isinstance(screen, InGameScreen):
            screen.cards = message.cards
            self.log.debug("Updated game state on InGameScreen.")
