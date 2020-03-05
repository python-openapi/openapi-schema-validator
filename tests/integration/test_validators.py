from jsonschema import ValidationError
import pytest

from openapi_schema_validator import OAS30Validator


class TestOAS30ValidatorValidate(object):

    @pytest.mark.parametrize('schema_type', [
        'boolean', 'array', 'integer', 'number', 'string',
    ])
    def test_null(self, schema_type):
        schema = {"type": schema_type}
        validator = OAS30Validator(schema)
        value = None

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize('schema_type', [
        'boolean', 'array', 'integer', 'number', 'string',
    ])
    def test_nullable(self, schema_type):
        schema = {"type": schema_type, "nullable": True}
        validator = OAS30Validator(schema)
        value = None

        result = validator.validate(value)

        assert result is None
