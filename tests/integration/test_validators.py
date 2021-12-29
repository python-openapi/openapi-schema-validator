from jsonschema import ValidationError
import pytest

from openapi_schema_validator import OAS30Validator, oas30_format_checker

try:
    from unittest import mock
except ImportError:
    import mock


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
        u'1989-01-02T00:00:00Z',
        u'2018-01-02T23:59:59Z',
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_STRICT_RFC3339', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_ISODATE', False
    )
    def test_string_format_no_datetime_validator(self, value):
        schema = {"type": 'string', "format": 'date-time'}
        validator = OAS30Validator(
            schema, format_checker=oas30_format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize('value', [
        u'1989-01-02T00:00:00Z',
        u'2018-01-02T23:59:59Z',
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', True
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_STRICT_RFC3339', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_ISODATE', False
    )
    def test_string_format_datetime_rfc3339_validator(self, value):
        schema = {"type": 'string', "format": 'date-time'}
        validator = OAS30Validator(
            schema, format_checker=oas30_format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize('value', [
        u'1989-01-02T00:00:00Z',
        u'2018-01-02T23:59:59Z',
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_STRICT_RFC3339', True
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
        u'1989-01-02T00:00:00Z',
        u'2018-01-02T23:59:59Z',
    ])
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_RFC3339_VALIDATOR', False
    )
    @mock.patch(
        'openapi_schema_validator._format.'
        'DATETIME_HAS_STRICT_RFC3339', False
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

    @pytest.mark.parametrize('value', [
        'f50ec0b7-f960-400d-91f0-c42a6d44e3d0',
        'F50EC0B7-F960-400D-91F0-C42A6D44E3D0',
    ])
    def test_string_uuid(self, value):
        schema = {"type": 'string', "format": 'uuid'}
        validator = OAS30Validator(schema, format_checker=oas30_format_checker)

        result = validator.validate(value)

        assert result is None

    def test_allof_required(self):
        schema = {
            "allOf": [
                {"type": "object",
                 "properties": {
                     "some_prop": {"type": "string"}}},
                {"type": "object", "required": ["some_prop"]},
            ]
        }
        validator = OAS30Validator(schema, format_checker=oas30_format_checker)
        with pytest.raises(ValidationError,
                           match="'some_prop' is a required property"):
            validator.validate({"another_prop": "bla"})

    def test_required(self):
        schema = {
            "type": "object",
            "properties": {
                "some_prop": {
                    "type": "string"
                }
            },
            "required": ["some_prop"]
        }

        validator = OAS30Validator(schema, format_checker=oas30_format_checker)
        with pytest.raises(ValidationError,
                           match="'some_prop' is a required property"):
            validator.validate({"another_prop": "bla"})
        assert validator.validate({"some_prop": "hello"}) is None

    def test_required_read_only(self):
        schema = {
            "type": "object",
            "properties": {
                "some_prop": {
                    "type": "string",
                    "readOnly": True
                }
            },
            "required": ["some_prop"]
        }

        validator = OAS30Validator(schema, format_checker=oas30_format_checker,
                                   read=True)
        with pytest.raises(ValidationError,
                           match="'some_prop' is a required property"):
            validator.validate({"another_prop": "hello"})
        validator = OAS30Validator(schema, format_checker=oas30_format_checker,
                                   write=True)
        assert validator.validate({"another_prop": "hello"}) is None

    def test_required_write_only(self):
        schema = {
            "type": "object",
            "properties": {
                "some_prop": {
                    "type": "string",
                    "writeOnly": True
                }
            },
            "required": ["some_prop"]
        }

        validator = OAS30Validator(schema, format_checker=oas30_format_checker,
                                   write=True)
        with pytest.raises(ValidationError,
                           match="'some_prop' is a required property"):
            validator.validate({"another_prop": "hello"})
        validator = OAS30Validator(schema, format_checker=oas30_format_checker,
                                   read=True)
        assert validator.validate({"another_prop": "hello"}) is None

    def test_oneof_required(self):
        instance = {
            'n3IwfId': 'string',
        }
        schema = {
            "type": "object",
            "properties": {
                "n3IwfId": {"type": "string"},
                "wagfId": {"type": "string"},
            },
            "oneOf": [
                {"required": ["n3IwfId"]},
                {"required": ["wagfId"]},
            ],
        }
        validator = OAS30Validator(schema, format_checker=oas30_format_checker)
        result = validator.validate(instance)
        assert result is None
