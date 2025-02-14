from abc import abstractmethod
from typing import (
    Annotated,
    NamedTuple,
    Protocol,
    TypedDict,
    get_origin,
    runtime_checkable,
)

from tuno.server.exceptions import ApiException
from tuno.shared.constraints import (
    MAX_INITIAL_HAND_SIZE,
    MAX_PLAYER_CAPACITY,
    MIN_INITIAL_HAND_SIZE,
    MIN_PLAYER_CAPACITY,
)


@runtime_checkable
class RuleValidator(Protocol):

    rule_name: str

    def __init__(self, rule_name: str) -> None:
        super().__init__()
        self.rule_name = rule_name

    @abstractmethod
    def validate(self, value: object) -> None: ...


class RuleValidationException(ApiException):

    def __init__(self, message: str) -> None:
        super().__init__(400, message)


class IntRangeRuleValidator(RuleValidator):

    min: float
    max: float

    def __init__(self, rule_name: str, min: float, max: float) -> None:
        super().__init__(rule_name)
        self.min = min
        self.max = max

    def validate(self, value: object) -> None:
        if not isinstance(value, int):
            raise RuleValidationException(
                f"{self.rule_name} must be an integer, " f"got: {type(value).__name__}"
            )
        if not self.min <= value <= self.max:
            raise RuleValidationException(
                f"{self.rule_name} must be in range "
                f"[{self.min}, {self.max}], got: {value}"
            )


class GameRules(TypedDict):

    player_capacity: Annotated[
        int,
        f"{MIN_PLAYER_CAPACITY}~{MAX_PLAYER_CAPACITY}",
        IntRangeRuleValidator(
            "player_capacity",
            MIN_PLAYER_CAPACITY,
            MAX_PLAYER_CAPACITY,
        ),
    ]

    shuffle_players: Annotated[
        bool,
        "shuffle players before starting",
        None,
    ]

    initial_hand_size: Annotated[
        int,
        f"{MIN_INITIAL_HAND_SIZE}~{MAX_INITIAL_HAND_SIZE}",
        IntRangeRuleValidator(
            "initial_hand_size",
            MIN_INITIAL_HAND_SIZE,
            MAX_INITIAL_HAND_SIZE,
        ),
    ]

    any_last_play: Annotated[
        bool,
        "allow non-number card as last play",
        None,
    ]


class RuleAnnotation(NamedTuple):
    type: type
    hint: str
    validator: RuleValidator | None


def get_rule_annotation(key: str) -> RuleAnnotation:

    if key not in GameRules.__annotations__:
        raise RuleValidationException(f"Unknown rule: {key}")

    type_annotation = GameRules.__annotations__[key]
    if get_origin(type_annotation) is not Annotated:
        raise RuleValidationException(f"Invalid rule annotation: {type_annotation}")

    type_metadata: tuple[object, object, object] = type_annotation.__metadata__
    if (
        (len(type_metadata) != 2)
        or (not isinstance(type_metadata[0], str))
        or not (
            (type_metadata[1] is None) or isinstance(type_metadata[1], RuleValidator)
        )
    ):
        raise RuleValidationException(
            f"Invalid metadata for rule `{key}`: {type_metadata!r}"
        )

    return RuleAnnotation(
        type=type_annotation.__origin__,
        hint=type_metadata[0],
        validator=type_metadata[1],
    )


def check_rule_update(key: str, value: object) -> None:

    rule_annotation = get_rule_annotation(key)

    if not isinstance(value, rule_annotation.type):
        raise RuleValidationException(
            f"Invalid type for rule `{key}`: "
            f"expected {rule_annotation.type}, got {type(value)}"
        )

    if rule_annotation.validator:
        rule_annotation.validator.validate(value)
