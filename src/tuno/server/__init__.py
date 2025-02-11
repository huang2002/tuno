import click
from flask import Flask

from tuno.server.utils.Logger import Logger, LogLevel
from tuno.shared.constraints import (
    DEFAULT_PLAYER_CAPACITY,
    MAX_PLAYER_CAPACITY,
    MIN_PLAYER_CAPACITY,
)

from .config import DEFAULT_HOST, DEFAULT_PORT


def create_app() -> Flask:

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
    envvar="UNO_LOG_LEVEL",
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

    Logger.level = LogLevel[log_level]

    from .models.Game import game

    game.update_rules(
        {
            "player_capacity": capacity,
        },
        operator_name=None,
    )

    app = create_app()
    app.run(host=host, port=port)
