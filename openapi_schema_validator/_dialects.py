from typing import Any

from jsonschema.validators import validates

from openapi_schema_validator._specifications import (
    REGISTRY as OPENAPI_SPECIFICATIONS,
)

__all__ = [
    "OAS31_BASE_DIALECT_ID",
    "OAS31_BASE_DIALECT_METASCHEMA",
    "OAS32_BASE_DIALECT_ID",
    "OAS32_BASE_DIALECT_METASCHEMA",
    "register_openapi_dialect",
]

OAS31_BASE_DIALECT_ID = "https://spec.openapis.org/oas/3.1/dialect/base"
OAS31_BASE_DIALECT_METASCHEMA = OPENAPI_SPECIFICATIONS.contents(
    OAS31_BASE_DIALECT_ID,
)
OAS32_BASE_DIALECT_ID = "https://spec.openapis.org/oas/3.2/dialect/2025-09-17"
OAS32_BASE_DIALECT_METASCHEMA = OPENAPI_SPECIFICATIONS.contents(
    OAS32_BASE_DIALECT_ID,
)

_REGISTERED_VALIDATORS: dict[tuple[str, str], Any] = {}


def register_openapi_dialect(
    *,
    validator: Any,
    dialect_id: str,
    version_name: str,
    metaschema: Any,
) -> Any:
    key = (dialect_id, version_name)
    registered_validator = _REGISTERED_VALIDATORS.get(key)

    if registered_validator is validator:
        return validator
    if registered_validator is not None:
        return registered_validator

    validator.META_SCHEMA = metaschema
    validator = validates(version_name)(validator)
    _REGISTERED_VALIDATORS[key] = validator
    return validator
