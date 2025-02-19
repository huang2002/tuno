from datetime import timedelta
from typing import Final

# -- Connection Config --
SSE_MAX_RETRIES: Final = 2
SSE_TIMEOUT = timedelta(seconds=10)

# -- Notification Config --
NOTIFICATION_TIMEOUT_DEFAULT = timedelta(seconds=3)
NOTIFICATION_TIMEOUT_ERROR = timedelta(seconds=10)

# -- Environment Config --
ENV_KEY_CONNECTION: Final = "TUNO_CONNECTION"
ENV_KEY_PLAYER_NAME: Final = "TUNO_PLAYER_NAME"
ENV_KEY_SERVER_ADDRESS: Final = "TUNO_SERVER_ADDRESS"
