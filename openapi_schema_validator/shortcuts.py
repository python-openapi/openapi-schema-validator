from typing import Any
from typing import Mapping
from typing import cast

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator

from openapi_schema_validator.validators import OAS31Validator


def validate(
    instance: Any,
    schema: Mapping[str, Any],
    cls: type[Validator] = OAS31Validator,
    *args: Any,
    **kwargs: Any
) -> None:
    """
    Validate an instance against a given schema using the specified validator class.
    """
    schema_dict = cast(dict[str, Any], schema)
    cls.check_schema(schema_dict)
    validator = cls(schema_dict, *args, **kwargs)
    error = best_match(
        validator.evolve(schema=schema_dict).iter_errors(instance)
    )
    if error is not None:
        raise error
