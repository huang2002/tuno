from collections.abc import Iterable

from tuno.shared.constraints import MIN_PLAYER_CAPACITY
from tuno.shared.deck import BasicCardColor, Card


class ApiException(Exception):

    http_code: int
    message: str

    def __init__(self, http_code: int, message: str) -> None:
        super().__init__(message)
        self.http_code = http_code
        self.message = message


class InvalidRequestBodyException(ApiException):
    def __init__(self, message: str) -> None:
        super().__init__(
            400,
            message,
        )


class InvalidPlayerNameException(ApiException):
    def __init__(self, player_name: str) -> None:
        super().__init__(
            400,
            f"Invalid player name: {player_name}",
        )


class PlayerNotFoundException(ApiException):
    def __init__(self, player_name: str) -> None:
        super().__init__(
            400,
            f"Player not found: {player_name}",
        )


class NewPlayerToStartedGameException(ApiException):
    def __init__(self, player_name: str) -> None:
        super().__init__(
            403,
            f"Cannot add new player to a started game. ({player_name})",
        )


class GameAlreadyStartedException(ApiException):
    def __init__(self) -> None:
        super().__init__(
            400,
            "The game has already started.",
        )


class RuleUpdateOnStartedGameException(ApiException):
    def __init__(self) -> None:
        super().__init__(
            400,
            "Cannot update rules on a started game.",
        )


class NotEnoughPlayersException(ApiException):
    def __init__(self) -> None:
        super().__init__(
            400,
            "Not enough players to start the game. "
            f"(At least {MIN_PLAYER_CAPACITY} players are required.)",
        )


class GameNotStartedException(ApiException):
    def __init__(self) -> None:
        super().__init__(
            400,
            "The game has not started yet.",
        )


class InvalidLeadCardInfoException(ApiException):
    def __init__(
        self,
        lead_card: Card | None,
        lead_color: BasicCardColor | None,
    ) -> None:
        super().__init__(
            400,
            f"Invalid lead card info: {lead_card!r}, {lead_color!r}",
        )


class CardIdsNotFoundException(ApiException):
    def __init__(self, card_ids: Iterable[str]) -> None:
        super().__init__(
            400,
            f"Card id(s) not found: {', '.join(card_ids)}",
        )


class NotCurrentPlayerException(ApiException):
    def __init__(self, current_player_name: str) -> None:
        super().__init__(
            400,
            "Sorry, you are not the current player "
            f"(which is {current_player_name}).",
        )
