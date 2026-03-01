from dataclasses import dataclass
from typing import Any

from referencing import Registry
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from openapi_schema_validator import OAS30Validator
from openapi_schema_validator import OAS31Validator
from openapi_schema_validator import OAS32Validator
from openapi_schema_validator import oas30_format_checker
from openapi_schema_validator import oas31_format_checker
from openapi_schema_validator import oas32_format_checker


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    validator_class: Any
    schema: dict[str, Any]
    instance: Any
    validator_kwargs: dict[str, Any]


def build_cases() -> list[BenchmarkCase]:
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
    registry = Registry().with_resources(
        [
            ("urn:name-schema", name_schema),
            ("urn:age-schema", age_schema),
        ]
    )

    return [
        BenchmarkCase(
            name="oas32_simple_object",
            validator_class=OAS32Validator,
            schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "enabled": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
            instance={"name": "svc", "enabled": True},
            validator_kwargs={"format_checker": oas32_format_checker},
        ),
        BenchmarkCase(
            name="oas31_prefix_items",
            validator_class=OAS31Validator,
            schema={
                "type": "array",
                "prefixItems": [
                    {"type": "number"},
                    {"type": "string"},
                    {"enum": ["Street", "Avenue", "Boulevard"]},
                    {"enum": ["NW", "NE", "SW", "SE"]},
                ],
                "items": False,
            },
            instance=[1600, "Pennsylvania", "Avenue", "NW"],
            validator_kwargs={"format_checker": oas31_format_checker},
        ),
        BenchmarkCase(
            name="oas30_nullable",
            validator_class=OAS30Validator,
            schema={"type": "string", "nullable": True},
            instance=None,
            validator_kwargs={"format_checker": oas30_format_checker},
        ),
        BenchmarkCase(
            name="oas30_discriminator",
            validator_class=OAS30Validator,
            schema={
                "$ref": "#/components/schemas/Route",
                "components": {
                    "schemas": {
                        "MountainHiking": {
                            "type": "object",
                            "properties": {
                                "discipline": {
                                    "type": "string",
                                    "enum": [
                                        "mountain_hiking",
                                        "MountainHiking",
                                    ],
                                },
                                "length": {"type": "integer"},
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
                                "height": {"type": "integer"},
                            },
                            "required": ["discipline", "height"],
                        },
                        "Route": {
                            "oneOf": [
                                {
                                    "$ref": (
                                        "#/components/schemas/"
                                        "MountainHiking"
                                    )
                                },
                                {
                                    "$ref": (
                                        "#/components/schemas/"
                                        "AlpineClimbing"
                                    )
                                },
                            ],
                            "discriminator": {
                                "propertyName": "discipline",
                                "mapping": {
                                    "mountain_hiking": (
                                        "#/components/schemas/"
                                        "MountainHiking"
                                    ),
                                    "alpine_climbing": (
                                        "#/components/schemas/"
                                        "AlpineClimbing"
                                    ),
                                },
                            },
                        },
                    }
                },
            },
            instance={"discipline": "mountain_hiking", "length": 10},
            validator_kwargs={"format_checker": oas30_format_checker},
        ),
        BenchmarkCase(
            name="oas32_registry_refs",
            validator_class=OAS32Validator,
            schema={
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"$ref": "urn:name-schema"},
                    "age": {"$ref": "urn:age-schema"},
                },
                "additionalProperties": False,
            },
            instance={"name": "John", "age": 23},
            validator_kwargs={
                "format_checker": oas32_format_checker,
                "registry": registry,
            },
        ),
    ]
