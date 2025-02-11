from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from tuno.server.utils.checkers import check_player_name
from tuno.server.utils.Logger import Logger

logger = Logger(__name__)


def setup(blueprint: Blueprint) -> None:

    @blueprint.put("/start")
    def start() -> ResponseReturnValue:

        player_name = request.args.get("player_name", "")
        if player_name:
            check_player_name(player_name)
        else:
            player_name = "(anonymous)"

        from tuno.server.models.Game import game

        game.start(player_name)

        return ("Started!", 200)
