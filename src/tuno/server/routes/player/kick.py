from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from tuno.server.utils.checkers import check_player_name
from tuno.server.utils.Logger import Logger

logger = Logger(__name__)


def setup(blueprint: Blueprint) -> None:

    @blueprint.delete("/<target_player_name>")
    def kick_out(target_player_name: str) -> ResponseReturnValue:

        check_player_name(target_player_name)

        operator_name = request.args.get("operator", "")
        if operator_name:
            check_player_name(operator_name)
        else:
            operator_name = "(anonymous)"

        from tuno.server.models.Game import game

        game.kick_out_player(
            target_name=target_player_name,
            operator_name=operator_name,
        )

        return ("Player kicked out.", 200)
