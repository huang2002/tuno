from typing import cast

from flask import Blueprint, request
from flask.typing import ResponseReturnValue

from tuno.server.utils.checkers import check_player_name
from tuno.server.utils.Logger import Logger

logger = Logger(__name__)


def setup(blueprint: Blueprint) -> None:

    @blueprint.put("/rules")
    def set_rules() -> ResponseReturnValue:

        player_name = request.args.get("player_name", "")
        if player_name:
            check_player_name(player_name)
        else:
            player_name = "(anonymous)"

        modified_rules = request.json
        if not isinstance(modified_rules, dict):
            return (f"Invalid request body: {modified_rules!r}", 400)

        from tuno.server.models.Game import game

        game.update_rules(
            cast(dict[str, object], modified_rules),
            operator_name=player_name,
            operator_is_player=True,
        )

        return ("Rule updated.", 200)
