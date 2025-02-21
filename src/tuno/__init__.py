"""UNO right in your terminal, with both server and client."""

import click

from tuno.client import start_client
from tuno.server import start_server

__version__ = "0.2.1"


@click.group(
    help=__doc__,
    context_settings=dict(
        help_option_names=["-h", "--help"],
    ),
)
@click.version_option(
    __version__,
    "-v",
    "--version",
)
def tuno() -> None:
    pass


tuno.add_command(start_client)
tuno.add_command(start_server)
