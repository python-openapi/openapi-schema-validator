"""Local reference targets for OpenAPI 3.0 schema checks.

In OpenAPI 3.0 an object with ``$ref`` is a Reference Object and its other
keys are ignored, so the structural schema check does not descend into
them. A local reference can still point at a schema the structural check
never visited (for example a key next to a root ``$ref``, or a non-schema
key such as ``components``). This module finds those targets so they can
be checked with the same metaschema.

Only JSON pointer references (``#`` and ``#/...``) resolved against the
root document are followed. References that depend on runtime resolution
context are left to instance validation: external and anchor references,
references inside a subschema that sets its own ``id``, and schemas that
declare a different dialect with ``$schema``.
"""

from typing import Any
from typing import Iterator
from typing import Mapping
from urllib.parse import unquote

from jsonschema.validators import validator_for

# Draft 4 keywords whose values are a schema, a list of schemas, or a
# mapping of schemas.
_SCHEMA_KEYWORDS = ("additionalItems", "additionalProperties", "items", "not")
_SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "items", "oneOf")
_SCHEMA_MAP_KEYWORDS = ("dependencies", "patternProperties", "properties")


def declares_other_dialect(schema: Any) -> bool:
    """Whether ``schema`` switches jsonschema to another validator class.

    A ``$schema`` next to a ``$ref`` is an ignored sibling and does not
    count.
    """
    return (
        isinstance(schema, Mapping)
        and "$ref" not in schema
        and isinstance(schema.get("$schema"), str)
        and validator_for(schema, default=None) is not None
    )


def _children(
    schema: Mapping[str, Any], *, include_definitions: bool
) -> Iterator[Mapping[str, Any]]:
    for keyword in _SCHEMA_KEYWORDS:
        value = schema.get(keyword)
        if isinstance(value, Mapping):
            yield value
    for keyword in _SCHEMA_LIST_KEYWORDS:
        value = schema.get(keyword)
        if isinstance(value, list):
            yield from (item for item in value if isinstance(item, Mapping))
    map_keywords: tuple[str, ...] = _SCHEMA_MAP_KEYWORDS
    if include_definitions:
        map_keywords = (*map_keywords, "definitions")
    for keyword in map_keywords:
        value = schema.get(keyword)
        if isinstance(value, Mapping):
            yield from (
                item for item in value.values() if isinstance(item, Mapping)
            )


def _mark_covered(schema: Mapping[str, Any], covered: set[int]) -> None:
    # Mirror what the structural check visits: every subschema, including
    # definitions, but nothing inside a Reference Object.
    pending = [schema]
    while pending:
        current = pending.pop()
        if id(current) in covered:
            continue
        covered.add(id(current))
        if "$ref" not in current:
            pending.extend(_children(current, include_definitions=True))


def _sets_scope(schema: Any) -> bool:
    return (
        isinstance(schema, Mapping)
        and "$ref" not in schema
        and isinstance(schema.get("id"), str)
    )


def _resolve_pointer(
    document: Mapping[str, Any], ref: str
) -> tuple[Any, bool]:
    """Return the pointer target and whether an ``id`` on the way to it
    changes its resolution scope."""
    target: Any = document
    scoped = False
    if ref == "#":
        return target, scoped
    for token in unquote(ref[2:]).split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(target, list):
            target = target[int(token)]
        else:
            target = target[token]
        scoped = scoped or _sets_scope(target)
    return target, scoped


def iter_unchecked_reference_targets(
    schema: Mapping[str, Any],
) -> Iterator[Mapping[str, Any]]:
    """Yield reachable local reference targets the structural check missed.

    Each target is yielded once. Targets inside a yielded target are
    treated as covered by that target's check.
    """
    covered: set[int] = set()
    _mark_covered(schema, covered)

    pending: list[tuple[Mapping[str, Any], bool]] = [(schema, False)]
    visited: set[tuple[int, bool]] = set()
    while pending:
        current, scoped = pending.pop()
        key = (id(current), scoped)
        if key in visited:
            continue
        visited.add(key)

        if "$ref" not in current:
            if current is not schema and declares_other_dialect(current):
                continue
            # Definitions become reachable through references only.
            for child in _children(current, include_definitions=False):
                pending.append((child, scoped or _sets_scope(child)))
            continue

        ref = current["$ref"]
        if scoped or not isinstance(ref, str):
            continue
        if ref != "#" and not ref.startswith("#/"):
            continue
        try:
            target, target_scoped = _resolve_pointer(schema, ref)
        except (LookupError, TypeError, ValueError):
            # Unresolvable references are reported during validation.
            continue
        if not isinstance(target, Mapping) or declares_other_dialect(target):
            continue
        if id(target) not in covered:
            _mark_covered(target, covered)
            yield target
        pending.append((target, target_scoped))
