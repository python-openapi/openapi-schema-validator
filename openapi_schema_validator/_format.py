import binascii
from base64 import b64decode
from base64 import b64encode
from datetime import datetime
from typing import Any
from typing import Tuple
from typing import Union
from uuid import UUID

from jsonschema._format import FormatChecker
from jsonschema.exceptions import FormatError

DATETIME_HAS_RFC3339_VALIDATOR = False
DATETIME_HAS_STRICT_RFC3339 = False
DATETIME_HAS_ISODATE = False
DATETIME_RAISES: Tuple[Exception, ...] = ()

try:
    import isodate
except ImportError:
    pass
else:
    DATETIME_HAS_ISODATE = True
    DATETIME_RAISES += (ValueError, isodate.ISO8601Error)

try:
    from rfc3339_validator import validate_rfc3339
except ImportError:
    pass
else:
    DATETIME_HAS_RFC3339_VALIDATOR = True
    DATETIME_RAISES += (ValueError, TypeError)

try:
    import strict_rfc3339
except ImportError:
    pass
else:
    DATETIME_HAS_STRICT_RFC3339 = True
    DATETIME_RAISES += (ValueError, TypeError)


def is_int32(instance: Any) -> bool:
    return isinstance(instance, int)


def is_int64(instance: Any) -> bool:
    return isinstance(instance, int)


def is_float(instance: Any) -> bool:
    return isinstance(instance, float)


def is_double(instance: Any) -> bool:
    # float has double precision in Python
    # It's double in CPython and Jython
    return isinstance(instance, float)


def is_binary(instance: Any) -> bool:
    return isinstance(instance, bytes)


def is_byte(instance: Union[str, bytes]) -> bool:
    if isinstance(instance, str):
        instance = instance.encode()

    try:
        encoded = b64encode(b64decode(instance))
    except TypeError:
        return False
    else:
        return encoded == instance


def is_datetime(instance: str) -> bool:
    if not isinstance(instance, (bytes, str)):
        return False

    if DATETIME_HAS_RFC3339_VALIDATOR:
        return bool(validate_rfc3339(instance))

    if DATETIME_HAS_STRICT_RFC3339:
        return bool(strict_rfc3339.validate_rfc3339(instance))

    if DATETIME_HAS_ISODATE:
        return bool(isodate.parse_datetime(instance))

    return True


def is_date(instance: Any) -> bool:
    if not isinstance(instance, (bytes, str)):
        return False

    if isinstance(instance, bytes):
        instance = instance.decode()

    return bool(datetime.strptime(instance, "%Y-%m-%d"))


def is_uuid(instance: Any) -> bool:
    if not isinstance(instance, (bytes, str)):
        return False

    if isinstance(instance, bytes):
        instance = instance.decode()

    return str(UUID(instance)).lower() == instance.lower()


def is_password(instance: Any) -> bool:
    return True


class OASFormatChecker(FormatChecker):  # type: ignore

    checkers = {
        "int32": (is_int32, ()),
        "int64": (is_int64, ()),
        "float": (is_float, ()),
        "double": (is_double, ()),
        "byte": (is_byte, (binascii.Error, TypeError)),
        "binary": (is_binary, ()),
        "date": (is_date, (ValueError,)),
        "date-time": (is_datetime, DATETIME_RAISES),
        "password": (is_password, ()),
        # non standard
        "uuid": (is_uuid, (AttributeError, ValueError)),
    }

    def check(self, instance: Any, format: str) -> Any:
        if format not in self.checkers:
            raise FormatError(
                f"Format checker for {format!r} format not found"
            )

        func, raises = self.checkers[format]
        result, cause = None, None
        try:
            result = func(instance)
        except raises as e:  # type: ignore
            cause = e

        if not result:
            raise FormatError(
                f"{instance!r} is not a {format!r}",
                cause=cause,
            )
        return result


oas30_format_checker = OASFormatChecker()
oas31_format_checker = oas30_format_checker
