from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any
from typing import Hashable
from typing import Mapping

from jsonschema.protocols import Validator

from openapi_schema_validator.settings import get_settings


@dataclass
class CachedValidator:
    validator: Any
    schema_checked: bool


class ValidatorCache:
    def __init__(self) -> None:
        self._cache: OrderedDict[Hashable, CachedValidator] = OrderedDict()
        self._lock = RLock()

    def _freeze_value(self, value: Any) -> Hashable:
        if isinstance(value, dict):
            return tuple(
                sorted(
                    (str(key), self._freeze_value(item))
                    for key, item in value.items()
                )
            )
        if isinstance(value, list):
            return tuple(self._freeze_value(item) for item in value)
        if isinstance(value, tuple):
            return tuple(self._freeze_value(item) for item in value)
        if isinstance(value, set):
            return tuple(
                sorted(
                    (self._freeze_value(item) for item in value),
                    key=repr,
                )
            )
        if isinstance(value, (str, bytes, int, float, bool, type(None))):
            return value
        return ("id", id(value))

    def _schema_fingerprint(self, schema: Mapping[str, Any]) -> Hashable:
        return self._freeze_value(dict(schema))

    def build_key(
        self,
        schema: Mapping[str, Any],
        cls: type[Validator],
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
        allow_remote_references: bool,
    ) -> Hashable:
        return (
            cls,
            allow_remote_references,
            self._schema_fingerprint(schema),
            self._freeze_value(args),
            self._freeze_value(dict(kwargs)),
        )

    def get(self, key: Hashable) -> CachedValidator | None:
        with self._lock:
            return self._cache.get(key)

    def set(
        self,
        key: Hashable,
        *,
        validator: Any,
        schema_checked: bool,
    ) -> CachedValidator:
        cached = CachedValidator(
            validator=validator,
            schema_checked=schema_checked,
        )
        with self._lock:
            self._cache[key] = cached
            self._cache.move_to_end(key)
            self._prune_if_needed()
        return cached

    def mark_schema_checked(self, key: Hashable) -> None:
        with self._lock:
            cached = self._cache.get(key)
            if cached is None:
                return
            cached.schema_checked = True
            self._cache.move_to_end(key)

    def touch(self, key: Hashable) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def _prune_if_needed(self) -> None:
        max_size = get_settings().validate_cache_max_size
        while len(self._cache) > max_size:
            self._cache.popitem(last=False)
