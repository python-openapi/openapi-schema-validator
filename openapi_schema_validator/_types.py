from typing import Any
from typing import cast

from jsonschema._types import TypeChecker
from jsonschema._types import draft202012_type_checker
from jsonschema._types import is_array
from jsonschema._types import is_bool
from jsonschema._types import is_integer
from jsonschema._types import is_number
from jsonschema._types import is_object


def is_string(checker: Any, instance: Any) -> bool:
    return isinstance(instance, (str, bytes))


oas30_type_checker = TypeChecker(
    cast(
        Any,
        {
            "string": is_string,
            "number": is_number,
            "integer": is_integer,
            "boolean": is_bool,
            "array": is_array,
            "object": is_object,
        },
    ),
)
oas31_type_checker = draft202012_type_checker
