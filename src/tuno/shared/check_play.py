from tuno.server.exceptions import ApiException
from tuno.shared.deck import BasicCardColor, Card, Deck
from tuno.shared.rules import GameRules


class InvalidPlayException(ApiException):

    def __init__(self, message: str) -> None:
        super().__init__(400, message)


def check_play(
    play: Deck,
    *,
    lead_color: BasicCardColor,
    lead_card: Card,
    rules: GameRules,
) -> None:

    if len(play) == 0:
        raise InvalidPlayException("At least one card must be given in a play.")

    if len(play) > 1:
        raise InvalidPlayException("Only one card can be played at a time.")

    played_card = play[0]

    if played_card["type"] != "wild":

        if played_card["color"] == lead_color:
            return

        if (
            (lead_card["type"] == "number")
            and (played_card["type"] == "number")
            and (played_card["number"] == lead_card["number"])
        ):
            return

        if (
            (lead_card["type"] == "function")
            and (played_card["type"] == "function")
            and (played_card["effect"] == lead_card["effect"])
        ):
            return

        raise InvalidPlayException(
            "Non-wild-card play must match the lead color, number or effect."
        )

    else:

        return

    raise NotImplementedError()
