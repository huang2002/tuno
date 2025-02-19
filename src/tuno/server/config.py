from datetime import timedelta
from typing import Final

# -- Server Config --
DEFAULT_HOST: Final = "0.0.0.0"
DEFAULT_PORT: Final = 5000

# -- Environment Config --
ENV_KEY_LOG_LEVEL: str = "TUNO_LOG_LEVEL"

# -- Connection Config --
SUBSCRIPTION_TOKEN_BYTES: Final = 4  # each byte becomes 2 hex digits
SUBSCRIPTION_LOOP_INTERVAL = timedelta(milliseconds=200)
SUBSCRIPTION_LOOP_SLOW_THRESHOLD: Final = 3
MAX_MESSAGES_PER_LOOP: Final = 5
HEARTBEAT_GAP = timedelta(seconds=2)
PLAYER_TIMEOUT = timedelta(seconds=5)

# -- Game Config --
GAME_WATCHER_INTERVAL = timedelta(seconds=1)
GAME_WATCHER_SKIP_THRESHOLD: Final = 3

# -- Player Config --
PLAYER_MESSAGE_QUEUE_SIZE: Final = 20
