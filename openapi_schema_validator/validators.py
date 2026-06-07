from functools import lru_cache
from typing import Any
from typing import Iterator
from typing import Mapping
from typing import cast

from jsonschema import _keywords
from jsonschema import _legacy_keywords
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError
from jsonschema.protocols import Validator
from jsonschema.validators import Draft202012Validator
from jsonschema.validators import create
from jsonschema.validators import extend
from jsonschema.validators import validator_for

from openapi_schema_validator import _format as oas_format
from openapi_schema_validator import _keywords as oas_keywords
from openapi_schema_validator import _types as oas_types
from openapi_schema_validator._binary import build_binary_format
from openapi_schema_validator._binary import build_binary_max_length
from openapi_schema_validator._binary import build_binary_min_length
from openapi_schema_validator._binary import build_binary_type
from openapi_schema_validator._binary import is_oas30_binary_schema
from openapi_schema_validator._binary import is_oas31_binary_schema
from openapi_schema_validator._binary import is_oas31_strict_binary_schema
from openapi_schema_validator._binary import is_oas32_binary_schema
from openapi_schema_validator._binary import is_oas32_strict_binary_schema
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_METASCHEMA
from openapi_schema_validator._dialects import OAS32_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS32_BASE_DIALECT_METASCHEMA
from openapi_schema_validator._dialects import register_openapi_dialect
from openapi_schema_validator._specifications import (
    REGISTRY as OPENAPI_SPECIFICATIONS,
)
from openapi_schema_validator._types import oas31_type_checker

_CHECK_SCHEMA_UNSET = object()


def check_openapi_schema(
    cls: Any,
    schema: Any,
    format_checker: Any = _CHECK_SCHEMA_UNSET,
) -> None:
    if format_checker is _CHECK_SCHEMA_UNSET:
        format_checker = cls.FORMAT_CHECKER

    validator_class = validator_for(cls.META_SCHEMA, default=cls)

    validator_for_metaschema = validator_class(
        cls.META_SCHEMA,
        format_checker=format_checker,
        registry=OPENAPI_SPECIFICATIONS,
    )

    for error in validator_for_metaschema.iter_errors(schema):
        raise SchemaError.create_from(error)


def _oas30_id_of(schema: Any) -> str:
    if isinstance(schema, dict):
        return schema.get("id", "")  # type: ignore[no-any-return]
    return ""


OAS30_VALIDATORS = cast(
    Any,
    {
        "multipleOf": _keywords.multipleOf,
        # exclusiveMaximum supported inside maximum_draft3_draft4
        "maximum": _legacy_keywords.maximum_draft3_draft4,
        # exclusiveMinimum supported inside minimum_draft3_draft4
        "minimum": _legacy_keywords.minimum_draft3_draft4,
        "maxLength": _keywords.maxLength,
        "minLength": _keywords.minLength,
        "pattern": oas_keywords.pattern,
        "maxItems": _keywords.maxItems,
        "minItems": _keywords.minItems,
        "uniqueItems": _keywords.uniqueItems,
        "maxProperties": _keywords.maxProperties,
        "minProperties": _keywords.minProperties,
        "enum": _keywords.enum,
        # adjusted to OAS
        "type": oas_keywords.type,
        "allOf": oas_keywords.allOf,
        "oneOf": oas_keywords.oneOf,
        "anyOf": oas_keywords.anyOf,
        "not": _keywords.not_,
        "items": oas_keywords.items,
        "properties": _keywords.properties,
        "required": oas_keywords.required,
        "additionalProperties": oas_keywords.additionalProperties,
        # TODO: adjust description
        "format": oas_keywords.format,
        # TODO: adjust default
        "$ref": _keywords.ref,
        # fixed OAS fields
        "discriminator": oas_keywords.not_implemented,
        "readOnly": oas_keywords.not_implemented,
        "writeOnly": oas_keywords.not_implemented,
        "xml": oas_keywords.not_implemented,
        "externalDocs": oas_keywords.not_implemented,
        "example": oas_keywords.not_implemented,
        "deprecated": oas_keywords.not_implemented,
    },
)


def _binary_aware_oas30_keywords(predicate: Any) -> dict[str, Any]:
    """Binary-aware wrappers over the OAS 3.0 keyword callables.

    ``type`` accepts ``bytes`` for opaque binary schemas, ``maxLength`` / ``minLength``
    enforce octet length, and ``format`` is skipped on opaque binary ``bytes``. The
    originals are the OAS 3.0 callables so the strict variants do not inherit the
    default predicate's acceptance.
    """
    return {
        "type": build_binary_type(OAS30_VALIDATORS["type"], predicate),
        "maxLength": build_binary_max_length(
            OAS30_VALIDATORS["maxLength"], predicate
        ),
        "minLength": build_binary_min_length(
            OAS30_VALIDATORS["minLength"], predicate
        ),
        "format": build_binary_format(OAS30_VALIDATORS["format"], predicate),
    }


def _binary_aware_draft202012_keywords(predicate: Any) -> dict[str, Any]:
    """Binary-aware wrappers over the native draft-2020-12 keyword callables.

    Used for the OAS 3.1 / 3.2 validators (default and strict). ``type`` accepts
    ``bytes`` for opaque binary schemas, ``maxLength`` / ``minLength`` enforce
    octet length, and ``format`` is skipped on opaque binary ``bytes``. The
    originals are the native draft-2020-12 callables so the strict variants do
    not inherit the default predicate's acceptance.
    """
    return {
        "type": build_binary_type(
            Draft202012Validator.VALIDATORS["type"], predicate
        ),
        "maxLength": build_binary_max_length(
            Draft202012Validator.VALIDATORS["maxLength"], predicate
        ),
        "minLength": build_binary_min_length(
            Draft202012Validator.VALIDATORS["minLength"], predicate
        ),
        "format": build_binary_format(
            Draft202012Validator.VALIDATORS["format"], predicate
        ),
    }


def extend_openapi_validator(
    validator_class: Any,
    validators: Mapping[str, Any] | None = None,
    type_checker: Any | None = None,
    format_checker: Any | None = None,
) -> type[Validator]:
    """Extend an OpenAPI-aware Validator with custom behavior while preserving
    OpenAPI metaschema checking and FORMAT_CHECKER.

    jsonschema extend() builds a fresh class via create() and drops the custom check_schema, so there
    is no simpler hook to inject registry-aware schema checking while preserving class's FORMAT_CHECKER.
    """
    extended_validator = cast(
        type[Validator],
        extend(
            validator_class,
            validators=validators or {},
            type_checker=type_checker,
            format_checker=format_checker,
        ),
    )
    extended_validator.check_schema = classmethod(check_openapi_schema)
    return extended_validator


BaseOAS30Validator = create(
    meta_schema=OPENAPI_SPECIFICATIONS.contents(
        "http://json-schema.org/draft-04/schema#",
    ),
    validators=OAS30_VALIDATORS,
    type_checker=oas_types.oas30_type_checker,
    format_checker=oas_format.oas30_format_checker,
    # NOTE: version causes conflict with global jsonschema validator
    # See https://github.com/python-openapi/openapi-schema-validator/pull/12
    # version="oas30",
    id_of=_oas30_id_of,
)
OAS30Validator = extend_openapi_validator(
    BaseOAS30Validator,
    _binary_aware_oas30_keywords(is_oas30_binary_schema),
)
OAS30StrictValidator = extend_openapi_validator(
    OAS30Validator,
    validators={
        "type": oas_keywords.strict_type,
    },
    type_checker=oas_types.oas30_type_checker,
    format_checker=oas_format.oas30_strict_format_checker,
    # NOTE: version causes conflict with global jsonschema validator
    # See https://github.com/python-openapi/openapi-schema-validator/pull/12
    # version="oas30-strict",
)
OAS30ReadValidator = extend_openapi_validator(
    OAS30Validator,
    validators={
        "required": oas_keywords.read_required,
        "writeOnly": oas_keywords.read_writeOnly,
    },
)
OAS30WriteValidator = extend_openapi_validator(
    OAS30Validator,
    validators={
        "required": oas_keywords.write_required,
        "readOnly": oas_keywords.write_readOnly,
    },
)

BaseOAS31Validator = extend_openapi_validator(
    Draft202012Validator,
    validators={
        # adjusted to OAS
        "pattern": oas_keywords.pattern,
        "description": oas_keywords.not_implemented,
        # fixed OAS fields
        # discriminator is annotation-only in OAS 3.1+
        "discriminator": oas_keywords.not_implemented,
        "xml": oas_keywords.not_implemented,
        "externalDocs": oas_keywords.not_implemented,
        "example": oas_keywords.not_implemented,
    },
)
OAS31Validator = extend_openapi_validator(
    BaseOAS31Validator,
    _binary_aware_draft202012_keywords(is_oas31_binary_schema),
    format_checker=oas_format.oas31_format_checker,
)
register_openapi_dialect(
    validator=OAS31Validator,
    dialect_id=OAS31_BASE_DIALECT_ID,
    version_name="oas31",
    metaschema=OAS31_BASE_DIALECT_METASCHEMA,
)

OAS32Validator = extend_openapi_validator(
    OAS31Validator,
    _binary_aware_draft202012_keywords(is_oas32_binary_schema),
    format_checker=oas_format.oas32_format_checker,
)
register_openapi_dialect(
    validator=OAS32Validator,
    dialect_id=OAS32_BASE_DIALECT_ID,
    version_name="oas32",
    metaschema=OAS32_BASE_DIALECT_METASCHEMA,
)

# Strict OAS 3.1 / 3.2 validators: explicit opt-ins that preserve JSON Schema
# string typing. They accept canonical typeless raw binary but reject ``bytes``
# whenever a schema asserts ``type: string`` (even with a non-text
# ``contentMediaType``). Built with the strict predicates rather than inheriting
# the default binary wrappers, and intentionally NOT registered as the dialect
# default, so validator_for keeps resolving the OAS 3.1 / 3.2 dialect ids to the
# runtime-friendly OAS31Validator / OAS32Validator.
OAS31StrictValidator = extend_openapi_validator(
    OAS31Validator,
    _binary_aware_draft202012_keywords(is_oas31_strict_binary_schema),
)
OAS32StrictValidator = extend_openapi_validator(
    OAS32Validator,
    _binary_aware_draft202012_keywords(is_oas32_strict_binary_schema),
    format_checker=oas_format.oas32_format_checker,
)


@lru_cache(maxsize=None)
def build_enforce_properties_required_validator(
    validator_class: Any,
) -> type[Validator]:
    properties_validator = validator_class.VALIDATORS.get("properties")
    required_validator = validator_class.VALIDATORS.get("required")

    def enforce_properties(
        validator: Any,
        properties: Any,
        instance: Any,
        schema: Mapping[str, Any],
    ) -> Iterator[Any]:
        if properties_validator is not None:
            yield from properties_validator(
                validator, properties, instance, schema
            )

        if not validator.is_type(instance, "object"):
            return

        if required_validator is not None:
            schema_required = (
                schema.get("required", []) if isinstance(schema, dict) else []
            )
            missing_props = [
                p for p in properties.keys() if p not in schema_required
            ]
            if missing_props:
                yield from required_validator(
                    validator, missing_props, instance, schema
                )

    return extend_openapi_validator(
        validator_class,
        validators={"properties": enforce_properties},
    )
