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
assert MIN_INITIAL_HAND_SIZE <= DEFAULT_INITIAL_HAND_SIZE <= MAX_INITIAL_HAND_SIZE

MIN_BOT_COUNT: Final = 0
MAX_BOT_COUNT: Final = 10
DEFAULT_BOT_COUNT: Final = 0
assert MIN_BOT_COUNT <= DEFAULT_BOT_COUNT <= MAX_BOT_COUNT

MIN_BOT_PLAY_DELAY_SECONDS: Final = 0.0
MAX_BOT_PLAY_DELAY_SECONDS: Final = 10.0
DEFAULT_BOT_PLAY_DELAY_SECONDS: Final = 2.5
assert (
    MIN_BOT_PLAY_DELAY_SECONDS
    <= DEFAULT_BOT_PLAY_DELAY_SECONDS
    <= MAX_BOT_PLAY_DELAY_SECONDS
)
