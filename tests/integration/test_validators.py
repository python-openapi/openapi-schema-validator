from base64 import b64encode

import pytest
from jsonschema import ValidationError
from referencing import Registry
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from openapi_schema_validator import OAS30ReadValidator
from openapi_schema_validator import OAS30Validator
from openapi_schema_validator import OAS30WriteValidator
from openapi_schema_validator import OAS31Validator
from openapi_schema_validator import oas30_format_checker
from openapi_schema_validator import oas31_format_checker


class TestOAS30ValidatorFormatChecker:
    @pytest.fixture
    def format_checker(self):
        return OAS30Validator.FORMAT_CHECKER

    def test_required_checkers(self, format_checker):
        required_formats_set = {
            "int32",
            "int64",
            "float",
            "double",
            "byte",
            "binary",
            "date",
            "date-time",
            "password",
        }
        assert required_formats_set.issubset(
            set(format_checker.checkers.keys())
        )


class BaseTestOASValidatorValidate:
    @pytest.mark.parametrize(
        "format,value",
        [
            ("int32", "test"),
            ("int32", True),
            ("int32", 3.12),
            ("int32", ["test"]),
            ("int64", "test"),
            ("int64", True),
            ("int64", 3.12),
            ("int64", ["test"]),
            ("float", "test"),
            ("float", 3),
            ("float", True),
            ("float", ["test"]),
            ("double", "test"),
            ("double", 3),
            ("double", True),
            ("double", ["test"]),
            ("password", 3.12),
            ("password", True),
            ("password", 3),
            ("password", ["test"]),
        ],
    )
    def test_formats_ignored(
        self, format, value, validator_class, format_checker
    ):
        schema = {"format": format}
        validator = validator_class(schema, format_checker=format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize("format", ["float", "double"])
    @pytest.mark.parametrize("value", [3, 3.14, 1.0])
    def test_number_float_and_double_valid(
        self, format, value, validator_class, format_checker
    ):
        schema = {"type": "number", "format": format}
        validator = validator_class(schema, format_checker=format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize("value", ["test"])
    def test_string(self, validator_class, value):
        schema = {"type": "string"}
        validator = validator_class(schema)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize("value", [True, 3, 3.12, None])
    def test_string_invalid(self, validator_class, value):
        schema = {"type": "string"}
        validator = validator_class(schema)

        with pytest.raises(ValidationError):
            validator.validate(value)

    def test_referencing(self, validator_class):
        name_schema = Resource.from_contents(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "string",
            }
        )
        age_schema = DRAFT202012.create_resource(
            {
                "type": "integer",
                "format": "int32",
                "minimum": 0,
                "maximum": 120,
            }
        )
        birth_date_schema = Resource.from_contents(
            {
                "type": "string",
                "format": "date",
            },
            default_specification=DRAFT202012,
        )
        registry = Registry().with_resources(
            [
                ("urn:name-schema", name_schema),
                ("urn:age-schema", age_schema),
                ("urn:birth-date-schema", birth_date_schema),
            ],
        )
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"$ref": "urn:name-schema"},
                "age": {"$ref": "urn:age-schema"},
                "birth-date": {"$ref": "urn:birth-date-schema"},
            },
            "additionalProperties": False,
        }

        validator = validator_class(schema, registry=registry)
        result = validator.validate({"name": "John", "age": 23}, schema)

        assert result is None


class TestOAS30ValidatorValidate(BaseTestOASValidatorValidate):
    @pytest.fixture
    def validator_class(self):
        return OAS30Validator

    @pytest.fixture
    def format_checker(self):
        return oas30_format_checker

    @pytest.mark.parametrize(
        "format,value",
        [
            ("binary", True),
            ("binary", 3),
            ("binary", 3.12),
            ("binary", ["test"]),
            ("byte", True),
            ("byte", 3),
            ("byte", 3.12),
            ("byte", ["test"]),
        ],
    )
    def test_oas30_formats_ignored(
        self, format, value, validator_class, format_checker
    ):
        schema = {"format": format}
        validator = validator_class(schema, format_checker=format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.xfail(reason="OAS 3.0 string type checker allows byte")
    @pytest.mark.parametrize("value", [b"test"])
    def test_string_disallow_binary(self, validator_class, value):
        schema = {"type": "string"}
        validator = validator_class(schema)

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize("value", [b"test"])
    def test_string_binary_valid(self, validator_class, format_checker, value):
        schema = {"type": "string", "format": "binary"}
        validator = validator_class(schema, format_checker=format_checker)

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize("value", ["test", True, 3, 3.12, None])
    def test_string_binary_invalid(
        self, validator_class, format_checker, value
    ):
        schema = {"type": "string", "format": "binary"}
        validator = validator_class(schema, format_checker=format_checker)

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize(
        "schema_type",
        [
            "boolean",
            "array",
            "integer",
            "number",
            "string",
        ],
    )
    def test_null(self, validator_class, schema_type):
        schema = {"type": schema_type}
        validator = validator_class(schema)
        value = None

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize("is_nullable", [True, False])
    def test_nullable_untyped(self, validator_class, is_nullable):
        schema = {"nullable": is_nullable}
        validator = validator_class(schema)
        value = None

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize(
        "schema_type",
        [
            "boolean",
            "array",
            "integer",
            "number",
            "string",
        ],
    )
    def test_nullable(self, validator_class, schema_type):
        schema = {"type": schema_type, "nullable": True}
        validator = validator_class(schema)
        value = None

        result = validator.validate(value)

        assert result is None

    def test_nullable_enum_without_none(self, validator_class):
        schema = {"type": "integer", "nullable": True, "enum": [1, 2, 3]}
        validator = validator_class(schema)
        value = None

        with pytest.raises(ValidationError):
            validator.validate(value)

    def test_nullable_enum_with_none(self, validator_class):
        schema = {"type": "integer", "nullable": True, "enum": [1, 2, 3, None]}
        validator = validator_class(schema)
        value = None

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize(
        "value",
        [
            b64encode(b"string"),
            b64encode(b"string").decode(),
        ],
    )
    def test_string_format_byte_valid(self, validator_class, value):
        schema = {"type": "string", "format": "byte"}
        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize("value", ["string", b"string"])
    def test_string_format_byte_invalid(self, validator_class, value):
        schema = {"type": "string", "format": "byte"}
        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )

        with pytest.raises(ValidationError, match="is not a 'byte'"):
            validator.validate(value)

    def test_allof_required(self, validator_class):
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"some_prop": {"type": "string"}},
                },
                {"type": "object", "required": ["some_prop"]},
            ]
        }
        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )
        with pytest.raises(
            ValidationError, match="'some_prop' is a required property"
        ):
            validator.validate({"another_prop": "bla"})

    def test_required(self, validator_class):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string"}},
            "required": ["some_prop"],
        }

        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )
        with pytest.raises(
            ValidationError, match="'some_prop' is a required property"
        ):
            validator.validate({"another_prop": "bla"})
        assert validator.validate({"some_prop": "hello"}) is None

    def test_oneof_required(self, validator_class):
        instance = {
            "n3IwfId": "string",
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
        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )
        result = validator.validate(instance)
        assert result is None

    @pytest.mark.parametrize(
        "schema_type",
        [
            "oneOf",
            "anyOf",
            "allOf",
        ],
    )
    def test_oneof_discriminator(self, validator_class, schema_type):
        # We define a few components schemas
        components = {
            "MountainHiking": {
                "type": "object",
                "properties": {
                    "discipline": {
                        "type": "string",
                        # we allow both the explicitely matched mountain_hiking discipline
                        # and the implicitely matched MoutainHiking discipline
                        "enum": ["mountain_hiking", "MountainHiking"],
                    },
                    "length": {
                        "type": "integer",
                    },
                },
                "required": ["discipline", "length"],
            },
            "AlpineClimbing": {
                "type": "object",
                "properties": {
                    "discipline": {
                        "type": "string",
                        "enum": ["alpine_climbing"],
                    },
                    "height": {
                        "type": "integer",
                    },
                },
                "required": ["discipline", "height"],
            },
            "Route": {
                # defined later
            },
        }
        components["Route"][schema_type] = [
            {"$ref": "#/components/schemas/MountainHiking"},
            {"$ref": "#/components/schemas/AlpineClimbing"},
        ]

        # Add the compoments in a minimalis schema
        schema = {
            "$ref": "#/components/schemas/Route",
            "components": {"schemas": components},
        }

        if schema_type != "allOf":
            # use jsonschema validator when no discriminator is defined
            validator = validator_class(
                schema, format_checker=oas30_format_checker
            )
            with pytest.raises(
                ValidationError,
                match="is not valid under any of the given schemas",
            ):
                validator.validate(
                    {"something": "matching_none_of_the_schemas"}
                )
                assert False

        if schema_type == "anyOf":
            # use jsonschema validator when no discriminator is defined
            validator = validator_class(
                schema, format_checker=oas30_format_checker
            )
            with pytest.raises(
                ValidationError,
                match="is not valid under any of the given schemas",
            ):
                validator.validate(
                    {"something": "matching_none_of_the_schemas"}
                )
                assert False

        discriminator = {
            "propertyName": "discipline",
            "mapping": {
                "mountain_hiking": "#/components/schemas/MountainHiking",
                "alpine_climbing": "#/components/schemas/AlpineClimbing",
            },
        }
        schema["components"]["schemas"]["Route"][
            "discriminator"
        ] = discriminator

        # Optional: check we return useful result when the schema is wrong
        validator = validator_class(
            schema, format_checker=oas30_format_checker
        )
        with pytest.raises(
            ValidationError, match="does not contain discriminating property"
        ):
            validator.validate({"something": "missing"})
            assert False

        # Check we get a non-generic, somehow usable, error message when a discriminated schema is failing
        with pytest.raises(
            ValidationError, match="'bad_string' is not of type 'integer'"
        ):
            validator.validate(
                {"discipline": "mountain_hiking", "length": "bad_string"}
            )
            assert False

        # Check explicit MountainHiking resolution
        validator.validate({"discipline": "mountain_hiking", "length": 10})

        # Check implicit MountainHiking resolution
        validator.validate({"discipline": "MountainHiking", "length": 10})

        # Check non resolvable implicit schema
        with pytest.raises(
            ValidationError,
            match="reference '#/components/schemas/other' could not be resolved",
        ):
            result = validator.validate({"discipline": "other"})
            assert False

    @pytest.mark.parametrize("is_nullable", [True, False])
    def test_nullable_ref(self, validator_class, is_nullable):
        """
        Tests that a field that points to a schema reference is null checked based on the $ref schema rather than
        on this schema
        :param is_nullable:  if the schema is marked as nullable. If not, validate an exception is raised on None
        """
        schema = {
            "$ref": "#/$defs/Pet",
            "$defs": {
                "NullableText": {"type": "string", "nullable": is_nullable},
                "Pet": {
                    "properties": {
                        "testfield": {"$ref": "#/$defs/NullableText"},
                    },
                },
            },
        }
        validator = validator_class(
            schema,
            format_checker=oas30_format_checker,
        )

        result = validator.validate({"testfield": "John"})
        assert result is None

        if is_nullable:
            result = validator.validate({"testfield": None})
            assert result is None
        else:
            with pytest.raises(
                ValidationError,
                match="None for not nullable",
            ):
                validator.validate({"testfield": None})
                assert False

    @pytest.mark.parametrize(
        "schema_type, not_nullable_regex",
        [
            ("oneOf", "None is not valid under any of the given schemas"),
            ("anyOf", "None is not valid under any of the given schemas"),
            ("allOf", "None for not nullable"),
        ],
    )
    @pytest.mark.parametrize("is_nullable", [True, False])
    def test_nullable_schema_combos(
        self, validator_class, is_nullable, schema_type, not_nullable_regex
    ):
        """
        This test ensures that nullablilty semantics are correct for oneOf, anyOf and allOf
        Specifically, nullable should checked on the children schemas
        :param is_nullable:  if the schema is marked as nullable. If not, validate an exception is raised on None
        :param schema_type: the schema type to validate
        :param not_nullable_regex: the expected raised exception if fields are marked as not nullable
        """
        schema = {
            "$ref": "#/$defs/Pet",
            "$defs": {
                "NullableText": {
                    "type": "string",
                    "nullable": (
                        False if schema_type == "oneOf" else is_nullable
                    ),
                },
                "NullableEnum": {
                    "type": "string",
                    "nullable": is_nullable,
                    "enum": ["John", "Alice", None],
                },
                "Pet": {
                    "properties": {
                        "testfield": {
                            schema_type: [
                                {"$ref": "#/$defs/NullableText"},
                                {"$ref": "#/$defs/NullableEnum"},
                            ]
                        }
                    },
                },
            },
        }
        validator = validator_class(
            schema,
            format_checker=oas30_format_checker,
        )

        if is_nullable:
            result = validator.validate({"testfield": None})
            assert result is None
        else:
            with pytest.raises(ValidationError, match=not_nullable_regex):
                validator.validate({"testfield": None})
                assert False


class TestOAS30ReadWriteValidatorValidate:
    def test_read_only(self):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string", "readOnly": True}},
        }

        validator = OAS30WriteValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        with pytest.raises(
            ValidationError,
            match="Tried to write read-only property with hello",
        ):
            validator.validate({"some_prop": "hello"})
        validator = OAS30ReadValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None
        validator = OAS30Validator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None

    def test_write_only(self):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string", "writeOnly": True}},
        }

        validator = OAS30ReadValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        with pytest.raises(
            ValidationError,
            match="Tried to read write-only property with hello",
        ):
            validator.validate({"some_prop": "hello"})
        validator = OAS30WriteValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None
        validator = OAS30Validator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None

    def test_required_read_only(self):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string", "readOnly": True}},
            "required": ["some_prop"],
        }

        validator = OAS30ReadValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        with pytest.raises(
            ValidationError, match="'some_prop' is a required property"
        ):
            validator.validate({"another_prop": "hello"})
        validator = OAS30WriteValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"another_prop": "hello"}) is None

    def test_required_write_only(self):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string", "writeOnly": True}},
            "required": ["some_prop"],
        }

        validator = OAS30WriteValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        with pytest.raises(
            ValidationError, match="'some_prop' is a required property"
        ):
            validator.validate({"another_prop": "hello"})
        validator = OAS30ReadValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"another_prop": "hello"}) is None


class TestOAS31ValidatorFormatChecker:
    @pytest.fixture
    def format_checker(self):
        return OAS31Validator.FORMAT_CHECKER

    def test_required_checkers(self, format_checker):
        required_formats_set = {
            # standard formats
            "int32",
            "int64",
            "float",
            "double",
            "password",
        }
        assert required_formats_set.issubset(
            set(format_checker.checkers.keys())
        )


class TestOAS31ValidatorValidate(BaseTestOASValidatorValidate):
    @pytest.fixture
    def validator_class(self):
        return OAS31Validator

    @pytest.fixture
    def format_checker(self):
        return oas31_format_checker

    @pytest.mark.parametrize("value", [b"test"])
    def test_string_disallow_binary(self, validator_class, value):
        schema = {"type": "string"}
        validator = validator_class(schema)

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize(
        "schema_type",
        [
            "boolean",
            "array",
            "integer",
            "number",
            "string",
        ],
    )
    def test_null(self, validator_class, schema_type):
        schema = {"type": schema_type}
        validator = validator_class(schema)
        value = None

        with pytest.raises(ValidationError):
            validator.validate(value)

    @pytest.mark.parametrize(
        "schema_type",
        [
            "boolean",
            "array",
            "integer",
            "number",
            "string",
        ],
    )
    def test_nullable(self, validator_class, schema_type):
        schema = {"type": [schema_type, "null"]}
        validator = validator_class(schema)
        value = None

        result = validator.validate(value)

        assert result is None

    def test_schema_validation(self, validator_class, format_checker):
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "age": {
                    "type": "integer",
                    "format": "int32",
                    "minimum": 0,
                    "nullable": True,
                },
                "birth-date": {
                    "type": "string",
                    "format": "date",
                },
            },
            "additionalProperties": False,
        }
        validator = validator_class(
            schema,
            format_checker=format_checker,
        )

        result = validator.validate({"name": "John", "age": 23})
        assert result is None

        with pytest.raises(ValidationError) as excinfo:
            validator.validate({"name": "John", "city": "London"})

        error = "Additional properties are not allowed ('city' was unexpected)"
        assert error in str(excinfo.value)

        with pytest.raises(ValidationError) as excinfo:
            validator.validate({"name": "John", "birth-date": "-12"})

        error = "'-12' is not a 'date'"
        assert error in str(excinfo.value)

    def test_schema_ref(self, validator_class, format_checker):
        schema = {
            "$ref": "#/$defs/Pet",
            "$defs": {
                "Pet": {
                    "required": ["id", "name"],
                    "properties": {
                        "id": {"type": "integer", "format": "int64"},
                        "name": {"type": "string"},
                        "tag": {"type": "string"},
                    },
                }
            },
        }
        validator = validator_class(
            schema,
            format_checker=format_checker,
        )

        result = validator.validate({"id": 1, "name": "John"})
        assert result is None

        with pytest.raises(ValidationError) as excinfo:
            validator.validate({"name": "John"})

        error = "'id' is a required property"
        assert error in str(excinfo.value)

    @pytest.mark.parametrize(
        "value",
        [
            [1600, "Pennsylvania", "Avenue", "NW"],
            [1600, "Pennsylvania", "Avenue"],
        ],
    )
    def test_array_prefixitems(self, validator_class, format_checker, value):
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "number"},
                {"type": "string"},
                {"enum": ["Street", "Avenue", "Boulevard"]},
                {"enum": ["NW", "NE", "SW", "SE"]},
            ],
            "items": False,
        }
        validator = validator_class(
            schema,
            format_checker=format_checker,
        )

        result = validator.validate(value)

        assert result is None

    @pytest.mark.parametrize(
        "value",
        [
            [1600, "Pennsylvania", "Avenue", "NW", "Washington"],
        ],
    )
    def test_array_prefixitems_invalid(self, validator_class, value):
        schema = {
            "type": "array",
            "prefixItems": [
                {"type": "number"},
                {"type": "string"},
                {"enum": ["Street", "Avenue", "Boulevard"]},
                {"enum": ["NW", "NE", "SW", "SE"]},
            ],
            "items": False,
        }
        validator = validator_class(
            schema,
            format_checker=oas31_format_checker,
        )

        with pytest.raises(ValidationError) as excinfo:
            validator.validate(value)

        errors = [
            # jsonschema < 4.20.0
            "Expected at most 4 items, but found 5",
            # jsonschema >= 4.20.0
            "Expected at most 4 items but found 1 extra",
        ]
        assert any(error in str(excinfo.value) for error in errors)
