from unittest.mock import patch

import pytest

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
