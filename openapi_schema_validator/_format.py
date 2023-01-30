import binascii
from base64 import b64decode
from base64 import b64encode
from typing import Any
from typing import Union

from jsonschema._format import FormatChecker


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
    if not isinstance(instance, bytes):
        return False

    encoded = b64encode(b64decode(instance))
    return encoded == instance


def is_password(instance: Any) -> bool:
    if not isinstance(instance, (bytes, str)):
        return False

    return True


oas30_format_checker = FormatChecker()
oas30_format_checker.checks("int32")(is_int32)
oas30_format_checker.checks("int64")(is_int64)
oas30_format_checker.checks("float")(is_float)
oas30_format_checker.checks("double")(is_double)
oas30_format_checker.checks("binary")(is_binary)
oas30_format_checker.checks("byte", (binascii.Error, TypeError))(is_byte)
oas30_format_checker.checks("password")(is_password)

oas31_format_checker = FormatChecker()
oas31_format_checker.checks("int32")(is_int32)
oas31_format_checker.checks("int64")(is_int64)
oas31_format_checker.checks("float")(is_float)
oas31_format_checker.checks("double")(is_double)
oas31_format_checker.checks("password")(is_password)
