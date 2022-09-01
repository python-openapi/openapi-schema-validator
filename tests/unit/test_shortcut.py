from unittest import TestCase

from openapi_schema_validator import validate


class ValidateTest(TestCase):
    def test_validate_does_not_mutate_schema_adding_nullable_key(self):
        schema = {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "enabled": {
                    "type": "boolean",
                },
            },
            "example": {"enabled": False, "email": "foo@bar.com"},
        }

        validate({"email": "foo@bar.com"}, schema)

        self.assertTrue("nullable" not in schema["properties"]["email"].keys())
