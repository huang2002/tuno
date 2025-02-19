import click
from flask import Flask

from tuno.server.utils.Logger import Logger, LogLevel
from tuno.shared.constraints import (
    DEFAULT_PLAYER_CAPACITY,
    MAX_PLAYER_CAPACITY,
    MIN_PLAYER_CAPACITY,
)

from .config import DEFAULT_HOST, DEFAULT_PORT, ENV_KEY_LOG_LEVEL


def create_app(*, log_level: LogLevel | None = None) -> Flask:

    from os import environ

    if log_level is None:
        env_log_level = environ.get(ENV_KEY_LOG_LEVEL, "")
        if env_log_level:
            log_level = LogLevel[env_log_level]
    if log_level:
        Logger.level = log_level

    from .models.Game import game
    from .routes import load_routes

    game.watcher_thread.start()

    app = Flask(__name__)

    blueprint = load_routes()
    app.register_blueprint(blueprint, url_prefix="/api")

    return app


@click.command("server")
@click.option(
    "--host",
    default=DEFAULT_HOST,
    show_default=True,
    help="Server host",
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=DEFAULT_PORT,
    show_default=True,
    help="Server port",
)
@click.option(
    "-c",
    "--capacity",
    type=click.IntRange(
        min=MIN_PLAYER_CAPACITY,
        max=MAX_PLAYER_CAPACITY,
    ),
    default=DEFAULT_PLAYER_CAPACITY,
    show_default=True,
    help="Initial player capacity",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice([l.name for l in LogLevel], case_sensitive=False),
    envvar=ENV_KEY_LOG_LEVEL,
    default=LogLevel.INFO.name,
    show_default=True,
    show_envvar=True,
    show_choices=True,
    help="Log level",
)
def start_server(
    host: str,
    port: int,
    capacity: int,
    log_level: str,
) -> None:
    """Start game server."""

    from .models.Game import game

    game.update_rules(
        {
            "player_capacity": capacity,
        },
        operator_name="server setup",
        operator_is_player=False,
    )

    app = create_app(log_level=LogLevel[log_level])
    app.run(host=host, port=port)
