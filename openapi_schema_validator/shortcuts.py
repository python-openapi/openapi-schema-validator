from typing import Any
from typing import Mapping
from typing import cast

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator

from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator.validators import OAS31Validator
from openapi_schema_validator.validators import check_openapi_schema


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

    meta_schema = getattr(cls, "META_SCHEMA", None)
    # jsonschema's default check_schema path does not accept a custom
    # registry, so for the OAS 3.1 dialect we use the package registry
    # explicitly to keep metaschema resolution local and deterministic.
    if (
        isinstance(meta_schema, dict)
        and meta_schema.get("$id") == OAS31_BASE_DIALECT_ID
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
