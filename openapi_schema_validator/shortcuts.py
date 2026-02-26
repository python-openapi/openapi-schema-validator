from typing import Any
from typing import Mapping
from typing import cast

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator
from referencing import Registry

from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS32_BASE_DIALECT_ID
from openapi_schema_validator.validators import OAS32Validator
from openapi_schema_validator.validators import check_openapi_schema


def validate(
    instance: Any,
    schema: Mapping[str, Any],
    cls: type[Validator] = OAS32Validator,
    *args: Any,
    allow_remote_references: bool = False,
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
        schema: OpenAPI schema mapping used for validation. Local references
            (``#/...``) are resolved against this mapping.
        cls: Validator class to use. Defaults to ``OAS32Validator``.
        *args: Positional arguments forwarded to ``cls`` constructor.
        allow_remote_references: If ``True`` and no explicit ``registry`` is
            provided, allow jsonschema's default remote reference retrieval
            behavior.
        **kwargs: Keyword arguments forwarded to ``cls`` constructor
            (for example ``registry`` and ``format_checker``). If omitted,
            a local-only empty ``Registry`` is used to avoid implicit remote
            reference retrieval.

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

    validator_kwargs = kwargs.copy()
    if not allow_remote_references:
        validator_kwargs.setdefault("registry", Registry())

    validator = cls(schema_dict, *args, **validator_kwargs)
    error = best_match(
        validator.evolve(schema=schema_dict).iter_errors(instance)
    )
    if error is not None:
        raise error
