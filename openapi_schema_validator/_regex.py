import re
from typing import Any

_REGEX_CLASS: Any = None
_REGRESS_ERROR: type[Exception] = Exception

try:
    from regress import Regex as _REGEX_CLASS
    from regress import RegressError as _REGRESS_ERROR
except ImportError:  # pragma: no cover - optional dependency
    pass


class ECMARegexSyntaxError(ValueError):
    pass


def has_ecma_regex() -> bool:
    return _REGEX_CLASS is not None


def is_valid_regex(pattern: str) -> bool:
    if _REGEX_CLASS is None:
        try:
            re.compile(pattern)
        except re.error:
            return False
        return True

    try:
        _REGEX_CLASS(pattern)
    except _REGRESS_ERROR:
        return False
    return True


def search(pattern: str, instance: str) -> bool:
    if _REGEX_CLASS is None:
        return re.search(pattern, instance) is not None

    try:
        return _REGEX_CLASS(pattern).find(instance) is not None
    except _REGRESS_ERROR as exc:
        raise ECMARegexSyntaxError(str(exc)) from exc
