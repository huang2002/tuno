from datetime import timedelta
from typing import Final

# -- Connection Config --
SSE_TIMEOUT = timedelta(seconds=30)

# -- Notification Config --
NOTIFICATION_TIMEOUT_DEFAULT = timedelta(seconds=3)
NOTIFICATION_TIMEOUT_ERROR = timedelta(seconds=10)

# -- Environment Config --
ENV_KEY_CONNECTION: Final = "UNO_CONNECTION"
ENV_KEY_PLAYER_NAME: Final = "UNO_PLAYER_NAME"
ENV_KEY_SERVER_ADDRESS: Final = "UNO_SERVER_ADDRESS"
