import click


@click.command("client")
def start_client() -> None:
    """Start game client."""

    from .UnoApp import UnoApp

    app = UnoApp()
    app.run()
