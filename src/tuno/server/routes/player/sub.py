from collections.abc import Generator
from queue import Empty
from secrets import token_hex
from time import monotonic

from flask import Blueprint, Response
from flask.typing import ResponseReturnValue

from tuno.server.config import (
    HEARTBEAT_GAP,
    MAX_MESSAGES_PER_LOOP,
    SUBSCRIPTION_LOOP_INTERVAL,
    SUBSCRIPTION_LOOP_SLOW_THRESHOLD,
    SUBSCRIPTION_TOKEN_BYTES,
)
from tuno.server.utils.checkers import check_player_name
from tuno.server.utils.Logger import Logger
from tuno.shared.loop import loop
from tuno.shared.sse_events import (
    EndOfConnectionEvent,
    GameStateEvent,
    SubscriptionChangeEvent,
)
from tuno.shared.ThreadLockContext import ThreadLockContext

logger = Logger(__name__)


def setup(blueprint: Blueprint) -> None:

    HEARTBEAT_GAP_SECONDS = HEARTBEAT_GAP.total_seconds()

    @blueprint.get("/<player_name>")
    def player_subscription(player_name: str) -> ResponseReturnValue:

        check_player_name(player_name)

        from tuno.server.models.Game import game

        player = game.get_player(player_name, allow_creation=True)
        subscription_token = token_hex(SUBSCRIPTION_TOKEN_BYTES)
        player.subscription_token = subscription_token

        def event_generator() -> Generator[str]:

            # send first heartbeat
            with player.message_context():
                yield f":\n\n"
            logger.info(
                f"Connected with player#{player_name}. "
                f"(subscription_token: {subscription_token})"
            )

            # send initial states
            with player.message_context():
                yield game.get_game_state_event().to_sse()
                yield player.get_cards_event().to_sse()
            logger.debug(
                f"Sent initial states to player#{player_name}. "
                f"(subscription_token: {subscription_token})"
            )

            # slow iteration detection
            def on_slow(continuous_slow_count: int) -> None:
                if continuous_slow_count >= SUBSCRIPTION_LOOP_SLOW_THRESHOLD:
                    logger.warn(
                        "The subscription loop seems to be slow. "
                        f"(subscription_token: {subscription_token}; "
                        f"continuous_slow_count: {continuous_slow_count})"
                    )

            # message loop
            for _ in loop(SUBSCRIPTION_LOOP_INTERVAL, on_slow=on_slow):
                with ThreadLockContext(player.lock):

                    for _ in range(MAX_MESSAGES_PER_LOOP):

                        if player.subscription_token != subscription_token:
                            break

                        try:
                            event = player.message_queue.get_nowait()
                        except Empty:
                            break
                        else:

                            with player.message_context():
                                yield event.to_sse()
                            player.message_queue.task_done()
                            logger.debug(
                                f"Event sent to player#{player_name} "
                                f"(subscription_token: {subscription_token}): "
                                + repr(event)
                            )

                            if isinstance(event, EndOfConnectionEvent):
                                player.subscription_token = ""
                                logger.debug(
                                    "Stopped subscription from "
                                    f"player#{player_name} due to the presence"
                                    f"of an {EndOfConnectionEvent.__name__}. "
                                    f"(subscription_token: {subscription_token})"
                                )
                                return

                    if player.subscription_token != subscription_token:
                        break

                    if (
                        monotonic() - (player.last_sent_timestamp or 0)
                        >= HEARTBEAT_GAP_SECONDS
                    ):
                        with player.message_context():
                            yield f":\n\n"  # heartbeat
                        # logger.debug(f"Heartbeat sent to player#{player_name}.")

            if player.subscription_token:  # replaced by another subscription
                event = SubscriptionChangeEvent()
                with player.message_context():
                    yield event.to_sse()
                logger.debug(
                    f"Event sent to player#{player_name} "
                    f"(subscription_token: {subscription_token}): " + repr(event)
                )

            logger.info(
                f"Subscription stopped for player#{player_name}. "
                f"(subscription_token: {subscription_token})"
            )

        response = Response(event_generator(), mimetype="text/event-stream")

        @response.call_on_close
        def on_close() -> None:
            with ThreadLockContext(player.lock):
                if player.subscription_token == subscription_token:
                    player.subscription_token = ""
                    logger.info(
                        f"Disconnected from player#{player_name}. "
                        f"(subscription_token: {subscription_token})"
                    )

        return response
