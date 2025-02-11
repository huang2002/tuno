from random import shuffle
from typing import Final

from ...shared.deck import (
    Deck,
    FunctionCard,
    NumberCard,
    WildCard,
    basic_card_colors,
    function_card_effects,
    wild_card_color,
    wild_card_effects,
)

INITIAL_DECK_SIZE: Final[int] = 108


def create_deck() -> Deck:
    """Create and return a non-shuffled deck."""

    deck: Deck = []

    ids = [str(x) for x in range(INITIAL_DECK_SIZE)]
    shuffle(ids)

    # number cards
    for color in basic_card_colors:
        for number in range(10):
            deck.append(
                NumberCard(
                    id=ids.pop(),
                    color=color,
                    type="number",
                    number=number,
                )
            )
            if number != 0:
                deck.append(
                    NumberCard(
                        id=ids.pop(),
                        color=color,
                        type="number",
                        number=number,
                    )
                )

    # function cards
    for color in basic_card_colors:
        for function_card_effect in function_card_effects:
            for _ in range(2):
                deck.append(
                    FunctionCard(
                        id=ids.pop(),
                        color=color,
                        type="function",
                        effect=function_card_effect,
                    )
                )

    # wild cards
    for _ in range(4):
        for wild_card_effect in wild_card_effects:
            deck.append(
                WildCard(
                    id=ids.pop(),
                    color=wild_card_color,
                    type="wild",
                    effect=wild_card_effect,
                )
            )

    assert len(ids) == 0
    assert len(deck) == INITIAL_DECK_SIZE

    return deck
