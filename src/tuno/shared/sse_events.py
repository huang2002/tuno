import json
from abc import ABC
from dataclasses import dataclass
from typing import Any, TypedDict

from tuno.shared.rules import GameRules

from .deck import BasicCardColor, Card, Deck


class ServerSentEvent(ABC):

    type: str
    data: Any = None

    def to_sse(self) -> str:
        result = f"event: {self.type}\n"
        if self.data != None:
            result += f"data: {json.dumps(self.data)}\n"
        return result + "\n"


@dataclass
class EndOfConnectionEvent(ServerSentEvent):
    """
    This event stops receiving player's subscription handler
    from processing any more messages the handler should end the connection
    right after sending this event.
    """

    type = "end_of_connection"
    data: str
    """A message that explains the end of connection."""


@dataclass
class NotificationEvent(ServerSentEvent):

    class DataType(TypedDict):
        title: str
        message: str

    type = "notification"
    data: DataType


@dataclass
class SubscriptionChangeEvent(ServerSentEvent):
    type = "subscription_change"


@dataclass
class GameStateEvent(ServerSentEvent):

    class PlayerDataType(TypedDict):
        name: str
        connected: bool
        card_count: int

    class DataType(TypedDict):
        started: bool
        rules: GameRules
        draw_pile_size: int
        discard_pile_size: int
        players: "list[GameStateEvent.PlayerDataType]"
        current_player_index: int
        lead_card: Card | None
        lead_color: BasicCardColor | None

    type = "game_state"
    data: DataType


@dataclass
class CardsEvent(ServerSentEvent):
    type = "cards"
    data: Deck
