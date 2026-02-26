from typing import Any
from typing import Mapping
from typing import cast

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator

from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS32_BASE_DIALECT_ID
from openapi_schema_validator.validators import OAS32Validator
from openapi_schema_validator.validators import check_openapi_schema


def validate(
    instance: Any,
    schema: Mapping[str, Any],
    cls: type[Validator] = OAS32Validator,
    *args: Any,
    **kwargs: Any
) -> None:
    """
    Validate an instance against a given schema using the specified
    validator class.

    Unlike direct ``Validator(schema).validate(instance)`` usage, this helper
    checks schema validity first.
    Invalid schemas therefore raise ``SchemaError`` before any instance
    validation occurs.

    Args:
        instance: Value to validate against ``schema``.
        schema: OpenAPI schema mapping used for validation.
        cls: Validator class to use. Defaults to ``OAS32Validator``.
        *args: Positional arguments forwarded to ``cls`` constructor.
        **kwargs: Keyword arguments forwarded to ``cls`` constructor.

    Raises:
        jsonschema.exceptions.SchemaError: If ``schema`` is invalid.
        jsonschema.exceptions.ValidationError: If ``instance`` is invalid.
    """
    schema_dict = cast(dict[str, Any], schema)

    meta_schema = getattr(cls, "META_SCHEMA", None)
    # jsonschema's default check_schema path does not accept a custom
    # registry, so for OAS dialects we use the package registry
    # explicitly to keep metaschema resolution local and deterministic.
    if isinstance(meta_schema, dict) and meta_schema.get("$id") in (
        OAS31_BASE_DIALECT_ID,
        OAS32_BASE_DIALECT_ID,
    ):
        check_openapi_schema(cls, schema_dict)
    else:
        cls.check_schema(schema_dict)

    validator = cls(schema_dict, *args, **kwargs)
    error = best_match(
        validator.evolve(schema=schema_dict).iter_errors(instance)
    )
    if error is not None:
        raise error
