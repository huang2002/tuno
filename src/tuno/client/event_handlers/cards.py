from typing import TYPE_CHECKING

from tuno.shared.deck import Deck

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp


def handler(parsed_data: Deck, app: "UnoApp") -> None:

    assert app.client is not None
    app.client.cards = parsed_data

    app.post_message(app.CardsUpdate(parsed_data))
