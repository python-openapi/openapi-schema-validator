from jsonschema import ValidationError
import mock
import pytest
from six import u

from openapi_schema_validator import OAS30Validator, oas30_format_checker


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

    @pytest.mark.parametrize('value', [
        u('1989-01-02T00:00:00Z'),
        u('2018-01-02T23:59:59Z'),
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', True
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_ISODATE', False
    )
    def test_string_format_datetime_strict_rfc3339(self, value):
        schema = {"type": 'string', "format": 'date-time'}
        validator = OAS30Validator(
            schema, format_checker=oas30_format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize('value', [
        u('1989-01-02T00:00:00Z'),
        u('2018-01-02T23:59:59Z'),
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_ISODATE', True
    )
    def test_string_format_datetime_isodate(self, value):
        schema = {"type": 'string', "format": 'date-time'}
        validator = OAS30Validator(
            schema, format_checker=oas30_format_checker)

        result = validator.validate(value)

        assert result is None
