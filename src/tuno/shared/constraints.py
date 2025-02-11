import re
from typing import Final

PLAYER_NAME_PATTERN: Final = re.compile(r"^[A-Za-z0-9_-]{1,20}$")

MIN_PLAYER_CAPACITY: Final = 2
MAX_PLAYER_CAPACITY: Final = 20
DEFAULT_PLAYER_CAPACITY: Final = 8
assert MIN_PLAYER_CAPACITY <= DEFAULT_PLAYER_CAPACITY <= MAX_PLAYER_CAPACITY

MIN_INITIAL_HAND_SIZE: Final = 2
MAX_INITIAL_HAND_SIZE: Final = 16
DEFAULT_INITIAL_HAND_SIZE: Final = 7
assert (
    MIN_INITIAL_HAND_SIZE <= DEFAULT_INITIAL_HAND_SIZE <= MAX_INITIAL_HAND_SIZE
)
