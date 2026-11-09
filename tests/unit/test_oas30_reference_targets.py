from typing import Any

import pytest
from jsonschema.exceptions import SchemaError
from jsonschema.exceptions import ValidationError

from openapi_schema_validator import validate
from openapi_schema_validator._references import (
    iter_unchecked_reference_targets,
)
from openapi_schema_validator.shortcuts import clear_validate_cache
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
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    clear_validate_cache()


@pytest.mark.parametrize("cls", OAS30_VALIDATORS)
def test_rejects_malformed_target_under_non_schema_key(cls: Any) -> None:
    schema = {
        "properties": {"name": {"$ref": "#/components/Name"}},
        "components": {"Name": {"type": "string", "minLength": "invalid"}},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        cls.check_schema(schema)
    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        validate({"name": "abc"}, schema, cls=cls)


def test_rejects_malformed_definition_next_to_root_ref() -> None:
    schema = {
        "$ref": "#/definitions/Name",
        "definitions": {"Name": {"type": "string", "minLength": "invalid"}},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        OAS30Validator.check_schema(schema)


def test_rejects_malformed_target_reached_transitively() -> None:
    schema = {
        "$ref": "#/x-a",
        "x-a": {"properties": {"b": {"$ref": "#/x-b"}}},
        "x-b": {"items": {"$ref": "#/x-c/0"}},
        "x-c": [{"maxItems": -1}],
    }

    with pytest.raises(SchemaError, match="less than the minimum"):
        OAS30Validator.check_schema(schema)


def test_rejects_malformed_target_reached_from_definition() -> None:
    schema = {
        "properties": {"a": {"$ref": "#/definitions/A"}},
        "definitions": {"A": {"$ref": "#/x-target"}},
        "x-target": {"type": "string", "minLength": "invalid"},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        OAS30Validator.check_schema(schema)


def test_resolves_escaped_pointer_tokens() -> None:
    schema = {
        "$ref": "#/x-paths/~1pets~0id/my%20schema",
        "x-paths": {"/pets~id": {"my schema": {"minLength": "invalid"}}},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        OAS30Validator.check_schema(schema)


def test_ignores_unreferenced_non_schema_keys() -> None:
    schema = {
        "type": "object",
        "x-unused": {"minLength": "invalid"},
        "properties": {"name": {"$ref": "#/x-name"}},
        "x-name": {"type": "string"},
    }

    OAS30Validator.check_schema(schema)
    validate({"name": "abc"}, schema, cls=OAS30Validator)


def test_ignores_unused_siblings_of_reached_reference() -> None:
    schema = {
        "properties": {
            "name": {"$ref": "#/x-name", "x-ignored": {"$ref": "#/x-bad"}},
        },
        "x-name": {"type": "string"},
        "x-bad": {"minLength": "invalid"},
    }

    OAS30Validator.check_schema(schema)


def test_terminates_on_recursive_references() -> None:
    schema = {
        "$ref": "#/definitions/Node",
        "definitions": {
            "Node": {
                "type": "object",
                "properties": {
                    "self": {"$ref": "#"},
                    "children": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Node"},
                    },
                },
            },
        },
    }

    OAS30Validator.check_schema(schema)
    validate({"children": [{"children": []}]}, schema, cls=OAS30Validator)


def test_checks_each_target_once() -> None:
    target: dict[str, Any] = {"type": "string"}
    schema = {
        "allOf": [{"$ref": "#/x-target"}, {"$ref": "#/x-target"}],
        "properties": {"a": {"$ref": "#/x-target"}},
        "x-target": target,
    }

    assert list(iter_unchecked_reference_targets(schema)) == [target]


def test_skips_targets_already_covered_by_structural_check() -> None:
    schema = {
        "properties": {"a": {"$ref": "#/definitions/A"}},
        "definitions": {"A": {"type": "string"}},
    }

    assert list(iter_unchecked_reference_targets(schema)) == []


@pytest.mark.parametrize(
    "ref",
    [
        "#/missing",
        "#/x-list/5",
        "#/x-list/not-an-index",
        "#/x-name/type/deeper",
    ],
)
def test_leaves_unresolvable_references_to_validation(ref: str) -> None:
    schema = {
        "properties": {"name": {"$ref": ref}},
        "x-list": [],
        "x-name": {"type": "string"},
    }

    OAS30Validator.check_schema(schema)


@pytest.mark.parametrize(
    "ref", ["https://example.com/schema.json", "other.json", "#anchor"]
)
def test_does_not_follow_non_pointer_references(ref: str) -> None:
    schema = {"properties": {"name": {"$ref": ref}}}

    OAS30Validator.check_schema(schema)


def test_skips_references_inside_id_scope() -> None:
    # At runtime the reference resolves against the nested ``id`` scope,
    # not the root document, so the root's ``x-name`` must not be checked.
    schema = {
        "properties": {
            "wrapper": {
                "id": "https://example.com/wrapper.json",
                "properties": {"name": {"$ref": "#/x-name"}},
                "x-name": {"type": "string"},
            },
        },
        "x-name": {"minLength": "invalid"},
    }

    OAS30Validator.check_schema(schema)


def test_skips_target_declaring_other_dialect() -> None:
    schema = {
        "properties": {"count": {"$ref": "#/x-count"}},
        "x-count": {"$schema": DRAFT_2020_12, "exclusiveMinimum": 0},
    }

    OAS30Validator.check_schema(schema)
    validate({"count": 1}, schema, cls=OAS30Validator)
    with pytest.raises(ValidationError, match="less than or equal to"):
        validate({"count": 0}, schema, cls=OAS30Validator)


def test_direct_check_follows_references_under_root_dialect() -> None:
    schema = {
        "$schema": DRAFT_2020_12,
        "properties": {"name": {"$ref": "#/x-target"}},
        "x-target": {"minLength": "invalid"},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        OAS30Validator.check_schema(schema)


def test_shortcut_defers_to_declared_root_dialect() -> None:
    # The shortcut evolves the root, so a root ``$schema`` selects that
    # dialect for the whole validation.
    schema = {
        "$schema": DRAFT_2020_12,
        "properties": {"count": {"$ref": "#/x-count"}},
        "x-count": {"exclusiveMinimum": 0},
    }

    validate({"count": 1}, schema, cls=OAS30Validator)


@pytest.mark.parametrize("legacy", ["keyword", "positional"])
def test_shortcut_defers_to_legacy_resolver(legacy: str) -> None:
    # Local references resolve against the legacy resolver's document.
    schema = {"$ref": "#/x-target", "x-target": {"minLength": "invalid"}}
    with pytest.deprecated_call():
        resolver = OAS30Validator({"x-target": {"type": "string"}}).resolver
    args = (resolver,) if legacy == "positional" else ()
    kwargs = {"resolver": resolver} if legacy == "keyword" else {}

    validate("abc", schema, OAS30Validator, *args, **kwargs)
    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        validate(
            "abc", {"minLength": "invalid"}, OAS30Validator, *args, **kwargs
        )


@pytest.mark.parametrize("cls", OAS30_VALIDATORS)
def test_check_references_can_be_disabled(cls: Any) -> None:
    schema = {"$ref": "#/x-target", "x-target": {"minLength": "invalid"}}

    cls.check_schema(schema, check_references=False)


def test_enforce_properties_required_keeps_reference_check() -> None:
    schema = {
        "properties": {"name": {"$ref": "#/x-name"}},
        "x-name": {"minLength": "invalid"},
    }

    with pytest.raises(SchemaError, match="is not of type 'integer'"):
        validate(
            {"name": "abc"},
            schema,
            cls=OAS30Validator,
            enforce_properties_required=True,
        )
