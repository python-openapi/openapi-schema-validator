from typing import Any
from typing import cast

from jsonschema import _keywords
from jsonschema import _legacy_keywords
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft202012Validator
from jsonschema.validators import create
from jsonschema.validators import extend
from jsonschema.validators import validator_for

from openapi_schema_validator import _format as oas_format
from openapi_schema_validator import _keywords as oas_keywords
from openapi_schema_validator import _types as oas_types
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_ID
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_METASCHEMA
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
        "pattern": _keywords.pattern,
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


def _build_oas30_validator() -> Any:
    return create(
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


def _build_oas31_validator() -> Any:
    validator = extend(
        Draft202012Validator,
        {
            # adjusted to OAS
            "allOf": oas_keywords.allOf,
            "oneOf": oas_keywords.oneOf,
            "anyOf": oas_keywords.anyOf,
            "description": oas_keywords.not_implemented,
            # fixed OAS fields
            "discriminator": oas_keywords.not_implemented,
            "xml": oas_keywords.not_implemented,
            "externalDocs": oas_keywords.not_implemented,
            "example": oas_keywords.not_implemented,
        },
        type_checker=oas31_type_checker,
        format_checker=oas_format.oas31_format_checker,
    )
    return register_openapi_dialect(
        validator=validator,
        dialect_id=OAS31_BASE_DIALECT_ID,
        version_name="oas31",
        metaschema=OAS31_BASE_DIALECT_METASCHEMA,
    )


OAS30Validator = _build_oas30_validator()
OAS30StrictValidator = extend(
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
OAS30ReadValidator = extend(
    OAS30Validator,
    validators={
        "required": oas_keywords.read_required,
        "writeOnly": oas_keywords.read_writeOnly,
    },
)
OAS30WriteValidator = extend(
    OAS30Validator,
    validators={
        "required": oas_keywords.write_required,
        "readOnly": oas_keywords.write_readOnly,
    },
)

OAS31Validator = _build_oas31_validator()

# OAS 3.2 uses JSON Schema Draft 2020-12 as its base dialect, same as
# OAS 3.1. The OAS-specific vocabulary differs slightly (e.g. xml keyword
# changes), but since xml is not_implemented in the current validators,
# the behavior is equivalent.
OAS32Validator = extend(
    OAS31Validator,
    {},
    format_checker=oas_format.oas32_format_checker,
)
