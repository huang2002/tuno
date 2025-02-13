from collections.abc import Mapping
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from textual import log

if TYPE_CHECKING:
    from tuno.client.UnoApp import UnoApp

__handler_dir = Path(__file__).parent


@runtime_checkable
class EventHandler(Protocol):
    def __call__(self, parsed_data: object, app: "UnoApp") -> None: ...


type EventHandlerMap = Mapping[str, EventHandler]


def load_event_handler_map() -> EventHandlerMap:

    event_handler_map: dict[str, EventHandler] = {}

    for entry in __handler_dir.iterdir():

        if entry.name.startswith("_"):
            continue

        module_name: str
        if entry.is_file():
            if entry.suffix != ".py":
                continue
            module_name = entry.stem
        else:
            if not (entry / "__init__.py").exists():
                continue
            module_name = entry.name

        module = import_module(f".{module_name}", __name__)
        if not (
            hasattr(module, "handler") and isinstance(module.handler, EventHandler)
        ):
            raise RuntimeError(f"Invalid event handler module: {entry}")

        if module_name in event_handler_map:
            raise RuntimeError(f"Duplicate event handler module: {entry}")

        event_handler_map[module_name] = module.handler
        log.debug(f"Loaded event handler: {module_name}")

    return event_handler_map
