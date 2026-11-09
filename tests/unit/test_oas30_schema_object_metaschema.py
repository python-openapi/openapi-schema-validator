import json
from typing import Any

import pytest
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator
from referencing import Registry
from referencing.jsonschema import DRAFT4

from openapi_schema_validator import OAS31Validator
from openapi_schema_validator import OAS32Validator
from openapi_schema_validator import validate
from openapi_schema_validator._dialects import OAS30_SCHEMA_ID
from openapi_schema_validator._specifications import (
    REGISTRY as OPENAPI_SPECIFICATIONS,
)
from openapi_schema_validator.validators import _OAS30_CHECK_SCHEMA
from openapi_schema_validator.validators import OAS30ReadValidator
from openapi_schema_validator.validators import OAS30StrictValidator
from openapi_schema_validator.validators import OAS30Validator
from openapi_schema_validator.validators import OAS30WriteValidator

OAS30_VALIDATORS = [
    OAS30Validator,
    OAS30StrictValidator,
    OAS30ReadValidator,
    OAS30WriteValidator,
]

FULL_SCHEMA: dict[str, Any] = {
    "title": "Pet",
    "description": "A pet",
    "type": "object",
    "required": ["name", "kind"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 64,
            "pattern": "^[a-z]+$",
            "nullable": True,
            "default": "rex",
            "example": "rex",
        },
        "age": {
            "type": "integer",
            "minimum": 0,
            "exclusiveMinimum": True,
            "maximum": 30,
            "exclusiveMaximum": False,
            "multipleOf": 1,
            "readOnly": True,
        },
        "tags": {
            "type": "array",
            "items": {"type": "string", "enum": ["a", "b"]},
            "minItems": 0,
            "maxItems": 3,
            "uniqueItems": True,
            "xml": {"name": "tag", "wrapped": True},
        },
        "kind": {"$ref": "#/properties/name", "description": "ignored"},
        "owner": {
            "allOf": [{"$ref": "#/properties/name"}],
            "anyOf": [{"type": "string"}],
            "oneOf": [{"type": "string"}],
            "not": {"type": "integer"},
            "writeOnly": True,
            "deprecated": True,
        },
    },
    "additionalProperties": {"type": "string", "format": "email"},
    "minProperties": 1,
    "maxProperties": 10,
    "discriminator": {"propertyName": "kind", "mapping": {"dog": "#/x"}},
    "externalDocs": {"url": "https://example.com/docs"},
    "xml": {"name": "pet", "x-extra": True},
    "x-internal": {"anything": ["goes"]},
}


def test_vendored_document_is_the_official_oas30_schema() -> None:
    document = OPENAPI_SPECIFICATIONS.contents(OAS30_SCHEMA_ID)

    assert document["id"] == OAS30_SCHEMA_ID
    assert document["$schema"] == "http://json-schema.org/draft-04/schema#"
    assert document["definitions"]["Schema"]["additionalProperties"] is False


def test_check_schema_rewrites_only_schema_or_reference_alternatives() -> None:
    serialized = json.dumps(_OAS30_CHECK_SCHEMA)

    assert "#/definitions/Schema" in serialized
    assert '"oneOf": [' not in serialized


@pytest.mark.parametrize("cls", OAS30_VALIDATORS)
def test_accepts_all_schema_object_fields(cls: Any) -> None:
    cls.check_schema(FULL_SCHEMA)


@pytest.mark.parametrize(
    "schema, message",
    [
        (
            {"type": ["string", "null"]},
            "['string', 'null'] is not of type 'string'",
        ),
        ({"type": "null"}, "'null' is not one of"),
        ({"items": [{"type": "string"}]}, "is not of type 'object'"),
        ({"definitions": {"Name": {}}}, "'definitions' does not match"),
        ({"id": "https://example.com/pet"}, "'id' does not match"),
        (
            {"$schema": "http://json-schema.org/draft-04/schema#"},
            "'$schema' does not match",
        ),
        ({"patternProperties": {"^a": {}}}, "'patternProperties' does not"),
        ({"additionalItems": False}, "'additionalItems' does not match"),
        ({"dependencies": {"a": ["b"]}}, "'dependencies' does not match"),
        ({"const": 1}, "'const' does not match"),
        ({"examples": [1]}, "'examples' does not match"),
        ({"unknownKeyword": 1}, "'unknownKeyword' does not match"),
    ],
)
def test_rejects_keywords_oas30_does_not_support(
    schema: dict[str, Any], message: str
) -> None:
    # The Draft 4 metaschema used previously accepts all of these.
    Draft4Validator.check_schema(schema)

    with pytest.raises(SchemaError) as excinfo:
        OAS30Validator.check_schema(schema)
    assert message in excinfo.value.message


@pytest.mark.parametrize(
    "wrap",
    [
        lambda s: {"properties": {"a": s}},
        lambda s: {"items": s},
        lambda s: {"allOf": [s]},
        lambda s: {"anyOf": [{"type": "string"}, s]},
        lambda s: {"oneOf": [s]},
        lambda s: {"not": s},
        lambda s: {"additionalProperties": s},
        lambda s: {"properties": {"a": {"items": {"not": s}}}},
    ],
)
def test_checks_every_schema_position(wrap: Any) -> None:
    OAS30Validator.check_schema(wrap({"type": "string"}))
    OAS30Validator.check_schema(wrap({"$ref": "#/x"}))

    with pytest.raises(SchemaError, match="'definitions' does not match"):
        OAS30Validator.check_schema(wrap({"definitions": {}}))


@pytest.mark.parametrize("value", [True, False])
def test_accepts_boolean_additional_properties(value: bool) -> None:
    OAS30Validator.check_schema({"additionalProperties": value})


@pytest.mark.parametrize(
    "schema, message",
    [
        ({"discriminator": {"mapping": {}}}, "'propertyName' is a required"),
        ({"xml": {"unknown": 1}}, "'unknown' does not match"),
        ({"externalDocs": {}}, "'url' is a required property"),
        ({"nullable": "yes"}, "'yes' is not of type 'boolean'"),
        ({"readOnly": 1}, "1 is not of type 'boolean'"),
        ({"exclusiveMinimum": 1}, "1 is not of type 'boolean'"),
        ({"minLength": -1}, "-1 is less than the minimum of 0"),
        ({"required": []}, "should be non-empty"),
        (True, "True is not of type 'object'"),
    ],
)
def test_rejects_malformed_fixed_fields(schema: Any, message: str) -> None:
    with pytest.raises(SchemaError) as excinfo:
        OAS30Validator.check_schema(schema)
    assert message in excinfo.value.message


def test_ignores_reference_siblings() -> None:
    schema = {
        "properties": {
            "a": {
                "$ref": "#/properties/b",
                "definitions": {},
                "type": ["string"],
            },
            "b": {"type": "string"},
        },
    }

    OAS30Validator.check_schema(schema)


def test_rejects_non_string_reference() -> None:
    with pytest.raises(SchemaError, match="is not of type 'string'"):
        OAS30Validator.check_schema({"$ref": 5})


def test_ignores_schema_next_to_reference() -> None:
    OAS30Validator.check_schema(
        {
            "$ref": "#/x",
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
    )


def test_keeps_format_checks() -> None:
    with pytest.raises(SchemaError, match="is not a 'regex'"):
        OAS30Validator.check_schema({"pattern": "("})


@pytest.mark.parametrize("cls", OAS30_VALIDATORS)
@pytest.mark.parametrize("enforce", [False, True])
def test_shortcut_checks_schema_object(cls: Any, enforce: bool) -> None:
    with pytest.raises(SchemaError, match="'definitions' does not match"):
        validate(
            "abc",
            {"type": "string", "definitions": {}},
            cls=cls,
            enforce_properties_required=enforce,
        )


def test_shortcut_skips_schema_object_check_when_disabled() -> None:
    validate(
        "abc",
        {"type": "string", "const": "abc"},
        cls=OAS30Validator,
        check_schema=False,
    )


@pytest.mark.parametrize("cls", [OAS31Validator, OAS32Validator])
def test_other_versions_keep_their_metaschema(cls: Any) -> None:
    validate("abc", {"type": ["string", "null"], "$defs": {}}, cls=cls)


@pytest.mark.parametrize(
    "schema",
    [
        {
            "oneOf": [{"$ref": "#/components/schemas/A"}],
            "components": {"schemas": {"A": {"type": "string"}}},
        },
        {
            "openapi": "3.0.3",
            "info": {"title": "API", "version": "1"},
            "paths": {},
        },
    ],
)
def test_rejects_non_schema_object_root(schema: dict[str, Any]) -> None:
    with pytest.raises(SchemaError, match="match any of the regexes"):
        validate("abc", schema, cls=OAS30Validator)


def test_shortcut_resolves_references_from_registry() -> None:
    registry = Registry().with_resource(
        "urn:name", DRAFT4.create_resource({"type": "string"})
    )
    schema = {"oneOf": [{"$ref": "urn:name"}]}

    validate("abc", schema, cls=OAS30Validator, registry=registry)
    with pytest.raises(ValidationError):
        validate(1, schema, cls=OAS30Validator, registry=registry)
