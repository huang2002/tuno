from typing import TYPE_CHECKING, cast

from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from tuno.server.exceptions import InvalidRequestBodyException
from tuno.server.utils.checkers import check_player_name
from tuno.server.utils.Logger import Logger
from tuno.shared.deck import BasicCardColor, basic_card_colors

logger = Logger(__name__)


def setup(blueprint: Blueprint) -> None:

    @blueprint.post("/<player_name>")
    def play(player_name: str) -> ResponseReturnValue:

        check_player_name(player_name)

        card_ids = request.json

        if not (
            isinstance(card_ids, list)
            and all(isinstance(card_id, str) for card_id in card_ids)
        ):
            raise InvalidRequestBodyException(
                f"expected a list of strings as card_ids, got {card_ids!r}."
            )

        play_color = request.args.get("color", None)
        if play_color is not None and play_color not in basic_card_colors:
            raise InvalidRequestBodyException(
                f"expected a valid card color, got {play_color!r}."
            )
        if TYPE_CHECKING:
            play_color = cast(BasicCardColor, play_color)

        from tuno.server.models.Game import game

        game.play(player_name, card_ids, play_color)

        return ("Play accepted.", 200)
