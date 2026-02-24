import warnings
from base64 import b64encode
from typing import Any
from typing import cast

import pytest
from jsonschema import ValidationError
from jsonschema.exceptions import (
    _WrappedReferencingError as WrappedReferencingError,
)
from jsonschema.validators import Draft202012Validator
from jsonschema.validators import extend
from jsonschema.validators import validator_for
from referencing import Registry
from referencing import Resource
from referencing.exceptions import InvalidAnchor
from referencing.exceptions import NoSuchAnchor
from referencing.exceptions import PointerToNowhere
from referencing.jsonschema import DRAFT202012

from openapi_schema_validator import OAS30ReadValidator
from openapi_schema_validator import OAS30StrictValidator
from openapi_schema_validator import OAS30Validator
from openapi_schema_validator import OAS30WriteValidator
from openapi_schema_validator import OAS31Validator
from openapi_schema_validator import OAS32Validator
from openapi_schema_validator import oas30_format_checker
from openapi_schema_validator import oas30_strict_format_checker
from openapi_schema_validator import oas31_format_checker
from openapi_schema_validator import oas32_format_checker
from openapi_schema_validator._dialects import OAS31_BASE_DIALECT_METASCHEMA
from openapi_schema_validator._dialects import register_openapi_dialect
from openapi_schema_validator.validators import OAS31_BASE_DIALECT_ID


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
        result = validator.validate({"name": "John", "age": 23})

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

    @pytest.mark.parametrize("value", [True, 3, 3.12, None])
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

    @pytest.mark.parametrize("value", ["string"])
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
        "mapping_ref",
        [
            "#/components/schemas/Missing",
            "#missing-anchor",
            "#bad/frag",
        ],
    )
    def test_discriminator_handles_unresolvable_reference_kinds(
        self, mapping_ref
    ):
        schema = {
            "oneOf": [{"$ref": "#/components/schemas/MountainHiking"}],
            "discriminator": {
                "propertyName": "discipline",
                "mapping": {"mountain_hiking": mapping_ref},
            },
            "components": {
                "schemas": {
                    "MountainHiking": {
                        "type": "object",
                        "properties": {
                            "discipline": {"type": "string"},
                            "length": {"type": "integer"},
                        },
                        "required": ["discipline", "length"],
                    },
                },
            },
        }

        validator = OAS30Validator(
            schema,
            format_checker=oas30_format_checker,
        )
        with pytest.raises(
            ValidationError,
            match=f"reference '{mapping_ref}' could not be resolved",
        ):
            validator.validate(
                {
                    "discipline": "mountain_hiking",
                    "length": 10,
                }
            )

    @pytest.mark.parametrize(
        "mapping_ref, expected_cause",
        [
            ("#/components/schemas/Missing", PointerToNowhere),
            ("#missing-anchor", NoSuchAnchor),
            ("#bad/frag", InvalidAnchor),
        ],
    )
    def test_discriminator_unresolvable_reference_causes(
        self, mapping_ref, expected_cause
    ):
        schema = {
            "oneOf": [{"$ref": "#/components/schemas/MountainHiking"}],
            "discriminator": {
                "propertyName": "discipline",
                "mapping": {"mountain_hiking": mapping_ref},
            },
            "components": {
                "schemas": {
                    "MountainHiking": {
                        "type": "object",
                        "properties": {
                            "discipline": {"type": "string"},
                            "length": {"type": "integer"},
                        },
                        "required": ["discipline", "length"],
                    },
                },
            },
        }

        validator = OAS30Validator(
            schema,
            format_checker=oas30_format_checker,
        )

        with pytest.raises(WrappedReferencingError) as exc_info:
            cast(Any, validator)._validate_reference(
                ref=mapping_ref,
                instance={"discipline": "mountain_hiking", "length": 10},
            )

        assert isinstance(exc_info.value.__cause__, expected_cause)

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
                        # we allow both the explicitly matched mountain_hiking discipline
                        # and the implicitly matched MoutainHiking discipline
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

        # Add the components in a minimalis schema
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
            ValidationError,
            match="is not of type 'object'",
        ):
            validator.validate("not-an-object")

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

    def test_read_only_false(self):
        schema = {
            "type": "object",
            "properties": {"some_prop": {"type": "string", "readOnly": False}},
        }

        validator = OAS30WriteValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None

    def test_write_only_false(self):
        schema = {
            "type": "object",
            "properties": {
                "some_prop": {"type": "string", "writeOnly": False}
            },
        }

        validator = OAS30ReadValidator(
            schema,
            format_checker=oas30_format_checker,
        )
        assert validator.validate({"some_prop": "hello"}) is None


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


class TestOAS32ValidatorValidate(TestOAS31ValidatorValidate):
    """OAS 3.2 uses the same JSON Schema dialect as 3.1."""

    @pytest.fixture
    def validator_class(self):
        return OAS32Validator

    @pytest.fixture
    def format_checker(self):
        return oas32_format_checker

    def test_validator_is_distinct_from_oas31(self):
        assert OAS32Validator is not OAS31Validator

    def test_format_checker_is_distinct_from_oas31(self):
        assert oas32_format_checker is not oas31_format_checker

    def test_validator_shares_oas31_behavior(self):
        assert OAS32Validator.VALIDATORS == OAS31Validator.VALIDATORS

    def test_format_validation_int32(self, validator_class):
        schema = {"type": "integer", "format": "int32"}
        validator = validator_class(
            schema, format_checker=oas32_format_checker
        )

        result = validator.validate(42)
        assert result is None

        with pytest.raises(ValidationError):
            validator.validate(9999999999)

    def test_format_validation_date(self, validator_class):
        schema = {"type": "string", "format": "date"}
        validator = validator_class(
            schema, format_checker=oas32_format_checker
        )

        result = validator.validate("2024-01-15")
        assert result is None

        with pytest.raises(ValidationError):
            validator.validate("not-a-date")

    def test_schema_with_allof(self, validator_class):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"id": {"type": "integer"}}},
                {"type": "object", "properties": {"name": {"type": "string"}}},
            ]
        }
        validator = validator_class(schema)

        result = validator.validate({"id": 1, "name": "test"})
        assert result is None

        with pytest.raises(ValidationError):
            validator.validate({"id": "not-an-integer"})


class TestOAS30StrictValidator:
    """
    Tests for OAS30StrictValidator which follows OAS spec strictly:
    - type: string only accepts str (not bytes)
    - format: binary also only accepts str (no special bytes handling)
    """

    def test_strict_string_rejects_bytes(self):
        """Strict validator rejects bytes for plain string type."""
        schema = {"type": "string"}
        validator = OAS30StrictValidator(schema)

        with pytest.raises(ValidationError):
            validator.validate(b"test")

    def test_strict_string_accepts_str(self):
        """Strict validator accepts str for string type."""
        schema = {"type": "string"}
        validator = OAS30StrictValidator(schema)

        result = validator.validate("test")
        assert result is None

    def test_strict_binary_format_rejects_bytes(self):
        """Strict validator rejects bytes even with binary format."""
        schema = {"type": "string", "format": "binary"}
        validator = OAS30StrictValidator(
            schema, format_checker=oas30_format_checker
        )

        with pytest.raises(ValidationError):
            validator.validate(b"test")

    def test_strict_binary_format_rejects_str(self):
        """
        Strict validator with binary format rejects strings.
        Binary format is for bytes in OAS, not plain strings.
        """
        schema = {"type": "string", "format": "binary"}
        validator = OAS30StrictValidator(
            schema, format_checker=oas30_strict_format_checker
        )

        # Binary format expects actual binary data (bytes in Python)
        # Plain strings fail format validation because they are not valid base64
        # Note: "test" is actually valid base64, so use "not base64" which is not
        with pytest.raises(ValidationError, match="is not a 'binary'"):
            validator.validate("not base64")


class TestValidatorForDiscovery:
    def test_oas31_base_dialect_resolves_to_oas31_validator(self):
        schema = {"$schema": OAS31_BASE_DIALECT_ID}

        validator_class = validator_for(schema)

        assert validator_class is OAS31Validator

    def test_oas31_base_dialect_discovery_has_no_deprecation_warning(self):
        schema = {"$schema": OAS31_BASE_DIALECT_ID}

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validator_for(schema)

        assert not any(
            issubclass(warning.category, DeprecationWarning)
            for warning in caught
        )

    def test_oas31_base_dialect_keeps_oas_keyword_behavior(self):
        schema = {
            "$schema": OAS31_BASE_DIALECT_ID,
            "type": "object",
            "required": ["kind"],
            "properties": {"kind": {"type": "string"}},
            "discriminator": {"propertyName": "kind"},
            "xml": {"name": "Pet"},
            "example": {"kind": "cat"},
        }

        validator_class = validator_for(schema)
        validator = validator_class(
            schema, format_checker=oas31_format_checker
        )

        result = validator.validate({"kind": "cat"})

        assert result is None

    def test_draft_2020_12_discovery_is_unchanged(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}

        validator_class = validator_for(schema)

        assert validator_class is Draft202012Validator

    def test_openapi_dialect_registration_is_idempotent(self):
        register_openapi_dialect(
            validator=OAS31Validator,
            dialect_id=OAS31_BASE_DIALECT_ID,
            version_name="oas31",
            metaschema=OAS31_BASE_DIALECT_METASCHEMA,
        )
        register_openapi_dialect(
            validator=OAS31Validator,
            dialect_id=OAS31_BASE_DIALECT_ID,
            version_name="oas31",
            metaschema=OAS31_BASE_DIALECT_METASCHEMA,
        )

        validator_class = validator_for({"$schema": OAS31_BASE_DIALECT_ID})

        assert validator_class is OAS31Validator

    def test_openapi_dialect_registration_does_not_replace_validator(self):
        another_oas31_validator = extend(OAS31Validator, {})

        registered_validator = register_openapi_dialect(
            validator=another_oas31_validator,
            dialect_id=OAS31_BASE_DIALECT_ID,
            version_name="oas31",
            metaschema=OAS31_BASE_DIALECT_METASCHEMA,
        )

        assert registered_validator is OAS31Validator
        assert (
            validator_for({"$schema": OAS31_BASE_DIALECT_ID}) is OAS31Validator
        )
