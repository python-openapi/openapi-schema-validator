import inspect
from unittest.mock import patch

import pytest
from referencing import Registry
from referencing import Resource

from openapi_schema_validator import OAS32Validator
from openapi_schema_validator import validate


@pytest.fixture(scope="function")
def schema():
    return {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "enabled": {
                "type": "boolean",
            },
        },
        "example": {"enabled": False, "email": "foo@bar.com"},
    }


def test_validate_does_not_add_nullable_to_schema(schema):
    """
    Verify that calling validate does not add the 'nullable' key to the schema
    """
    validate({"email": "foo@bar.com"}, schema)
    assert "nullable" not in schema["properties"]["email"].keys()


def test_validate_does_not_mutate_schema(schema):
    """
    Verify that calling validate does not mutate the schema
    """
    original_schema = schema.copy()
    validate({"email": "foo@bar.com"}, schema)
    assert schema == original_schema


def test_validate_does_not_fetch_remote_metaschemas(schema):
    with patch("urllib.request.urlopen") as urlopen:
        validate({"email": "foo@bar.com"}, schema)

    urlopen.assert_not_called()


def test_validate_defaults_to_oas32_validator():
    signature = inspect.signature(validate)

    assert signature.parameters["cls"].default is OAS32Validator


def test_oas32_validate_does_not_fetch_remote_metaschemas(schema):
    with patch("urllib.request.urlopen") as urlopen:
        validate({"email": "foo@bar.com"}, schema, cls=OAS32Validator)

    urlopen.assert_not_called()


def test_validate_blocks_implicit_remote_http_references_by_default():
    schema = {"$ref": "http://example.com/remote-schema.json"}

    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(Exception, match="Unresolvable"):
            validate({}, schema)

    urlopen.assert_not_called()


def test_validate_blocks_implicit_file_references_by_default():
    schema = {"$ref": "file:///etc/hosts"}

    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(Exception, match="Unresolvable"):
            validate({}, schema)

    urlopen.assert_not_called()


def test_validate_local_references_still_work_by_default():
    schema = {"$defs": {"Value": {"type": "integer"}}, "$ref": "#/$defs/Value"}

    with patch("urllib.request.urlopen") as urlopen:
        result = validate(1, schema)

    assert result is None
    urlopen.assert_not_called()


def test_validate_honors_explicit_registry():
    schema = {
        "type": "object",
        "properties": {"name": {"$ref": "urn:name-schema"}},
    }
    name_schema = Resource.from_contents(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "string",
        }
    )
    registry = Registry().with_resources(
        [("urn:name-schema", name_schema)],
    )

    result = validate({"name": "John"}, schema, registry=registry)

    assert result is None


def test_validate_can_allow_implicit_remote_references():
    schema = {"$ref": "http://example.com/remote-schema.json"}

    with patch("urllib.request.urlopen") as urlopen:
        with pytest.raises(Exception):
            validate({}, schema, allow_remote_references=True)

    assert urlopen.called
