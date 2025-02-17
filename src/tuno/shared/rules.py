from abc import abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from inspect import get_annotations
from typing import (
    Annotated,
    Any,
    NamedTuple,
    Protocol,
    TypedDict,
    cast,
    get_origin,
    runtime_checkable,
)

from tuno.server.exceptions import ApiException
from tuno.shared.constraints import (
    DEFAULT_INITIAL_HAND_SIZE,
    DEFAULT_PLAYER_CAPACITY,
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


class RuleMetadataWithoutType(NamedTuple):
    default: object
    hint: str
    validator: RuleValidator | None


class GameRules(TypedDict):

    player_capacity: Annotated[
        int,
        RuleMetadataWithoutType(
            default=DEFAULT_PLAYER_CAPACITY,
            hint=f"{MIN_PLAYER_CAPACITY}~{MAX_PLAYER_CAPACITY}",
            validator=IntRangeRuleValidator(
                "player_capacity",
                MIN_PLAYER_CAPACITY,
                MAX_PLAYER_CAPACITY,
            ),
        ),
    ]

    shuffle_players: Annotated[
        bool,
        RuleMetadataWithoutType(
            default=True,
            hint="shuffle players before starting",
            validator=None,
        ),
    ]

    initial_hand_size: Annotated[
        int,
        RuleMetadataWithoutType(
            default=DEFAULT_INITIAL_HAND_SIZE,
            hint=f"{MIN_INITIAL_HAND_SIZE}~{MAX_INITIAL_HAND_SIZE}",
            validator=IntRangeRuleValidator(
                "initial_hand_size",
                MIN_INITIAL_HAND_SIZE,
                MAX_INITIAL_HAND_SIZE,
            ),
        ),
    ]

    any_last_play: Annotated[
        bool,
        RuleMetadataWithoutType(
            default=True,
            hint="allow non-number card as last play",
            validator=None,
        ),
    ]


@dataclass
class RuleMetadata:
    type: type
    default: object
    hint: str
    validator: RuleValidator | None


@runtime_checkable
class AnnotatedType(Protocol):
    """A partial type for interacting with builtin _AnnotatedAlias, which is not exported."""

    __origin__: type
    __metadata__: tuple[object, ...]


def __parse_rule_metadata(type_annotation: object) -> RuleMetadata:

    if get_origin(type_annotation) is not Annotated:
        raise RuleValidationException(f"Invalid rule annotation: {type_annotation}")
    assert isinstance(type_annotation, AnnotatedType)

    type_metadata = type_annotation.__metadata__
    if (len(type_metadata) != 1) or (
        not isinstance(
            rule_metadata_without_type := type_metadata[0],
            RuleMetadataWithoutType,
        )
    ):
        raise RuntimeError(f"Invalid metadata: {type_metadata!r}")

    return RuleMetadata(
        type=type_annotation.__origin__,
        default=rule_metadata_without_type.default,
        hint=rule_metadata_without_type.hint,
        validator=rule_metadata_without_type.validator,
    )


rule_metadata_map: Mapping[str, RuleMetadata] = {
    key: __parse_rule_metadata(type_annotation)
    for key, type_annotation in get_annotations(GameRules).items()
}


def create_game_rules() -> GameRules:
    return cast(
        GameRules,
        {
            key: cast(Any, metadata.default)
            for key, metadata in rule_metadata_map.items()
        },
    )


def check_rule_update(key: str, value: object) -> None:

    rule_metadata = rule_metadata_map.get(key, None)
    if not rule_metadata:
        raise RuleValidationException(f"Unknown rule: {key}")

    if not isinstance(value, rule_metadata.type):
        raise RuleValidationException(
            f"Invalid type for rule `{key}`: "
            f"expected {rule_metadata.type}, got {type(value)}"
        )

    if rule_metadata.validator:
        rule_metadata.validator.validate(value)
