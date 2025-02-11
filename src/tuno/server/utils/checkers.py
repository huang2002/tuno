from tuno.server.exceptions import InvalidPlayerNameException
from tuno.shared.constraints import PLAYER_NAME_PATTERN


def check_player_name(player_name: str) -> None:
    if not PLAYER_NAME_PATTERN.fullmatch(player_name):
        raise InvalidPlayerNameException(player_name)
