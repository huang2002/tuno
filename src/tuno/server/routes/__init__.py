from importlib import import_module
from pathlib import Path

from flask import Blueprint

from tuno.server.exceptions import ApiException
from tuno.server.utils.Logger import Logger

__logger = Logger(__name__)
__routes_dir = Path(__file__).parent


def __load_routes(blueprint_name: str, folder: Path) -> Blueprint:

    blueprint = Blueprint(blueprint_name, __name__)

    for entry in folder.iterdir():

        if entry.name.startswith("_"):
            continue

        if entry.is_file() or (entry / "__init__.py").exists():

            if entry.is_file() and entry.suffix.lower() != ".py":
                continue

            route_name = ".".join(
                entry.relative_to(__routes_dir).parts,
            )[:-3]
            module = import_module(f".{route_name}", __name__)

            if hasattr(module, "setup"):
                module.setup(blueprint)
                __logger.debug(f'Loaded route "{route_name}".')
            else:
                raise RuntimeError(
                    f'Route "{route_name}" does not have a setup function!'
                )

        else:

            sub_blueprint = __load_routes(entry.name, entry)
            blueprint.register_blueprint(
                sub_blueprint,
                url_prefix=f"/{entry.name}",
            )

    return blueprint


def load_routes() -> Blueprint:

    blueprint = __load_routes("backend", __routes_dir)

    @blueprint.errorhandler(ApiException)
    def handle_api_exception(exception: ApiException) -> tuple[str, int]:
        __logger.warn(f"ApiException({exception.http_code}): {exception.message}")
        return exception.message, exception.http_code

    return blueprint
