from typing import Any, Hashable, Mapping, Type

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator

from openapi_schema_validator.validators import OAS31Validator


def validate(
    instance: Any,
    schema: Mapping[Hashable, Any],
    cls: Type[Validator] = OAS31Validator,
    *args: Any,
    **kwargs: Any
) -> None:
    """
    Validate an instance against a given schema using the specified validator class

    Args:
        instance: The instance to validate.
        schema: The schema to validate against
        cls: The validator class to use (defaults to OAS31Validator)
        *args: Additional positional arguments to pass to the validator
        **kwargs: Additional keyword arguments to pass to the validator

    Raises:
        jsonschema.exceptions.ValidationError: If the instance is invalid according to the schema
    """
    cls.check_schema(schema)
    validator = cls(schema, *args, **kwargs)
    errors = list(validator.evolve(schema=schema).iter_errors(instance))

    if errors:
        error = best_match(errors)
        error.message = f"Validation failed: {error.message}"
        raise error
