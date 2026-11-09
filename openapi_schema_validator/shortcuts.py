from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import cast

from jsonschema.exceptions import best_match
from jsonschema.protocols import Validator
from referencing import Registry

from openapi_schema_validator._caches import ValidatorCache
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS32_BASE_DIALECT_ID
from openapi_schema_validator._references import declares_other_dialect
from openapi_schema_validator.validators import OAS32Validator
from openapi_schema_validator.validators import (
    build_enforce_properties_required_validator,
)
from openapi_schema_validator.validators import check_openapi_schema
from openapi_schema_validator.validators import supports_reference_check

_LOCAL_ONLY_REGISTRY = Registry()
_VALIDATOR_CACHE = ValidatorCache()


def _check_schema(
    cls: type[Validator],
    schema: dict[str, Any],
    *,
    legacy_resolver: bool,
) -> None:
    meta_schema = getattr(cls, "META_SCHEMA", None)
    # jsonschema's default check_schema path does not accept a custom
    # registry, so for OAS dialects we use the package registry
    # explicitly to keep metaschema resolution local and deterministic.
    if isinstance(meta_schema, dict) and meta_schema.get("$id") in (
        OAS31_BASE_DIALECT_ID,
        OAS32_BASE_DIALECT_ID,
    ):
        check_openapi_schema(cls, schema)
    elif supports_reference_check(cls):
        # Local references are resolved against ``schema`` only when it is
        # the reference root: a legacy resolver can carry another document,
        # and a root ``$schema`` hands validation to that dialect.
        check_references = not (
            legacy_resolver or declares_other_dialect(schema)
        )
        cls.check_schema(schema, check_references=check_references)
    else:
        cls.check_schema(schema)


def validate(
    instance: Any,
    schema: Mapping[str, Any],
    cls: type[Validator] = OAS32Validator,
    *args: Any,
    allow_remote_references: bool = False,
    check_schema: bool = True,
    enforce_properties_required: bool = False,
    **kwargs: Any,
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
        check_schema: If ``True`` (default), validate the provided schema
            before validating ``instance``. If ``False``, skip schema
            validation and run instance validation directly.
        enforce_properties_required: If ``True``, all properties declared in
            the schema's ``properties`` object are strictly required to be
            present in the instance (except those marked as ``writeOnly`` or
            ``readOnly`` where appropriate), regardless of the schema's
            ``required`` array. Defaults to ``False``.
        **kwargs: Keyword arguments forwarded to ``cls`` constructor
            (for example ``registry`` and ``format_checker``). If omitted,
            a local-only empty ``Registry`` is used to avoid implicit remote
            reference retrieval.

    Raises:
        jsonschema.exceptions.SchemaError: If ``schema`` is invalid.
        jsonschema.exceptions.ValidationError: If ``instance`` is invalid.
    """
    if enforce_properties_required:
        cls = build_enforce_properties_required_validator(cls)  # type: ignore[arg-type]

    schema_dict = cast(dict[str, Any], schema)

    validator_kwargs = kwargs.copy()
    if not allow_remote_references:
        validator_kwargs.setdefault("registry", _LOCAL_ONLY_REGISTRY)

    legacy_resolver = validator_kwargs.get("resolver") is not None or bool(
        args and args[0] is not None
    )

    key = _VALIDATOR_CACHE.build_key(
        schema=schema_dict,
        cls=cls,
        args=args,
        kwargs=validator_kwargs,
        allow_remote_references=allow_remote_references,
    )

    cached = _VALIDATOR_CACHE.get(key)

    if cached is None:
        if check_schema:
            _check_schema(cls, schema_dict, legacy_resolver=legacy_resolver)

        validator = cls(schema_dict, *args, **validator_kwargs)
        cached = _VALIDATOR_CACHE.set(
            key,
            validator=validator,
            schema_checked=check_schema,
        )
    elif check_schema and not cached.schema_checked:
        _check_schema(cls, schema_dict, legacy_resolver=legacy_resolver)
        _VALIDATOR_CACHE.mark_schema_checked(key)
    else:
        _VALIDATOR_CACHE.touch(key)

    error = best_match(
        cached.validator.evolve(schema=schema_dict).iter_errors(instance)
    )
    if error is not None:
        raise error


def clear_validate_cache() -> None:
    _VALIDATOR_CACHE.clear()
