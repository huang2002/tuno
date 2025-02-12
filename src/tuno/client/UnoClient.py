import json
from collections.abc import Callable, Mapping
from threading import RLock, Thread
from typing import TYPE_CHECKING

from requests import RequestException, get, put
from requests_sse import EventSource
from textual import log

from tuno.client.config import SSE_TIMEOUT
from tuno.client.event_handlers import EventHandlerMap, load_event_handler_map
from tuno.client.utils.ApiContext import ApiContext
from tuno.shared.deck import Deck
from tuno.shared.sse_events import GameStateEvent

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


class UnoClient:

    app: "UnoApp"
    server_address: str
    player_name: str
    game_state: GameStateEvent.DataType | None
    cards: Deck
    subscription: EventSource | None
    subscription_lock: RLock
    subscription_thread: Thread | None
    event_handler_map: EventHandlerMap

    def __init__(self, app: "UnoApp") -> None:
        super().__init__()
        self.app = app
        self.server_address = ""
        self.player_name = ""
        self.game_state = None
        self.cards = []
        self.subscription = None
        self.subscription_lock = RLock()
        self.subscription_thread = None
        self.event_handler_map = load_event_handler_map()

    def get_connection_display(self) -> str:
        with self.subscription_lock:
            if self.subscription is None:
                raise RuntimeError("Server not connected!")
            assert self.player_name
            assert self.server_address
            return f"{self.player_name}@{self.server_address}"

    def reset(self, message: str | None) -> None:

        with self.subscription_lock:
            if self.subscription:
                self.subscription.close()
                self.subscription = None

        self.server_address = ""
        self.player_name = ""
        self.game_state = None
        self.cards = []

        log_message = "Client reset."
        if message:
            log_message += f" ({message})"
        self.app.log.info(log_message)

    def get_api_url(self, api_path: str) -> str:
        assert self.server_address
        return f"http://{self.server_address}/api{api_path}"

    def subscribe(
        self,
        *,
        server_address: str,
        player_name: str,
        on_success: Callable[[], None],
        on_failure: Callable[[str], None],
    ) -> None:

        self.server_address = server_address
        self.player_name = player_name

        url = self.get_api_url(f"/player/{player_name}")
        log.info(f'Connecting to "{url}"...')

        event_source = EventSource(
            url,
            max_connect_retry=3,
            timeout=SSE_TIMEOUT.total_seconds(),
        )

        with self.subscription_lock:
            self.subscription = event_source

        try:

            with event_source:

                log.info(f'Connected to "{server_address}".')
                on_success()

                for event in event_source:

                    if self.subscription != event_source:
                        break

                    log.debug("Received server-sent event:", event)

                    handler = self.event_handler_map.get(event.type or "")
                    if not handler:
                        error_message = f"Unexpected event type: {event.type!r}"
                        log.error(error_message)
                        self.app.notify_error(
                            error_message,
                            title="Unknown Event Type",
                        )
                        continue

                    parsed_data: object = None
                    if event.data:
                        try:
                            parsed_data = json.loads(event.data)
                        except json.JSONDecodeError as error:
                            error_message = f"Invalid JSON data: {event.data!r}"
                            log.error(error_message)
                            log.error(error)
                            self.app.notify_error(
                                error_message,
                                title="Invalid Event Data",
                            )
                            continue

                    handler(parsed_data, self.app)

        except RequestException as error:
            log.error(error)
            if error.response:
                error_message = error.response.text
            else:
                error_message = repr(error)
            on_failure(error_message)

        except AttributeError as error:
            if (error.obj is None) and (error.name == "read"):
                # HACK: After being closed, the SSE client may block until next
                # incoming line and raise an AttributeError for next read.
                # Therefore, this clause suppresses such error so that
                # the app can quit without error reported.
                event_source.close()
                pass
            else:
                raise  # propagate other errors

    def connect(
        self,
        *,
        server_address: str,
        player_name: str,
        on_success: Callable[[], None],
        on_failure: Callable[[str], None],
    ) -> None:
        self.subscription_thread = Thread(
            target=self.subscribe,
            kwargs=dict(
                server_address=server_address,
                player_name=player_name,
                on_success=on_success,
                on_failure=on_failure,
            ),
        )
        self.subscription_thread.start()

    def update_rules(self, modified_rules: Mapping[str, object]) -> None:
        api_url = self.get_api_url("/game/rules")
        assert self.player_name
        with ApiContext("Rule Update Failed", app=self.app):
            response = put(
                api_url,
                json=modified_rules,
                params={
                    "player_name": self.player_name,
                },
            )
            response.raise_for_status()

    def start_game(self) -> None:

        player_name = self.player_name
        assert player_name

        api_url = self.get_api_url(f"/game/start")

        with ApiContext("Start Failed", app=self.app):
            response = put(
                api_url,
                params={
                    "player_name": player_name,
                },
            )
            response.raise_for_status()

    def stop_game(self) -> None:

        player_name = self.player_name
        assert player_name

        api_url = self.get_api_url(f"/game/stop")

        with ApiContext("Stop Failed", app=self.app):
            response = put(
                api_url,
                params={
                    "player_name": player_name,
                },
            )
            response.raise_for_status()
