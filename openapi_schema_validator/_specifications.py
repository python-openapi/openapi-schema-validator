import json
from importlib.resources import files
from typing import Any
from typing import Iterator

from jsonschema_specifications import REGISTRY as JSONSCHEMA_REGISTRY
from referencing import Resource

__all__ = ["REGISTRY"]


def _iter_schema_files() -> Iterator[Any]:
    schema_root = files(__package__).joinpath("schemas")
    stack = [schema_root]

    while stack:
        current = stack.pop()
        for child in current.iterdir():
            if child.name.startswith("."):
                continue
            if child.is_dir():
                stack.append(child)
                continue
            yield child


def _load_schemas() -> Iterator[Resource]:
    for path in _iter_schema_files():
        contents = json.loads(path.read_text(encoding="utf-8"))
        yield Resource.from_contents(contents)


#: A `referencing.Registry` containing all official jsonschema resources
#: plus openapi resources.
REGISTRY = (_load_schemas() @ JSONSCHEMA_REGISTRY).crawl()
