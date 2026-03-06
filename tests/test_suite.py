"""
Test runner for the openapi-schema-test-suite.

This module integrates the external test suite from
https://github.com/python-openapi/openapi-schema-test-suite
to validate OAS 3.1 and OAS 3.2 schema validators against
the canonical test cases.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema.exceptions import ValidationError

from openapi_schema_validator import OAS31Validator
from openapi_schema_validator import OAS32Validator
from openapi_schema_validator import oas31_format_checker
from openapi_schema_validator import oas32_format_checker

SUITE_ROOT = (
    Path(__file__).parent.parent
    / "vendor"
    / "openapi-schema-test-suite"
    / "tests"
)

# Each entry is (dialect, relative_path, case_description, test_description).
_KNOWN_FAILURES: dict[tuple[str, str, str, str], str] = {
    (
        "oas31",
        "optional/format/format-assertion.json",
        "format uri with assertion",
        "a relative URI is not a valid URI",
    ): "uri format checker does not validate RFC 3986 absolute-URI requirement",
    (
        "oas31",
        "optional/format/format-assertion.json",
        "format uri with assertion",
        "an invalid URI is not valid",
    ): "uri format checker does not validate RFC 3986 absolute-URI requirement",
    (
        "oas32",
        "optional/format/format-assertion.json",
        "format uri with assertion",
        "a relative URI is not a valid URI",
    ): "uri format checker does not validate RFC 3986 absolute-URI requirement",
    (
        "oas32",
        "optional/format/format-assertion.json",
        "format uri with assertion",
        "an invalid URI is not valid",
    ): "uri format checker does not validate RFC 3986 absolute-URI requirement",
}

_DIALECT_CONFIG: dict[str, dict[str, Any]] = {
    "oas31": {
        "validator_class": OAS31Validator,
        "format_checker": oas31_format_checker,
    },
    "oas32": {
        "validator_class": OAS32Validator,
        "format_checker": oas32_format_checker,
    },
}


def _collect_params() -> list[pytest.param]:
    params: list[pytest.param] = []

    for dialect, config in _DIALECT_CONFIG.items():
        dialect_dir = SUITE_ROOT / dialect
        if not dialect_dir.is_dir():
            continue

        for json_path in sorted(dialect_dir.rglob("*.json")):
            rel_path = json_path.relative_to(dialect_dir)
            is_in_optional_dir = rel_path.parts[0] == "optional"
            format_checker = (
                config["format_checker"] if is_in_optional_dir else None
            )

            test_cases: list[dict[str, Any]] = json.loads(
                json_path.read_text(encoding="utf-8")
            )
            for case in test_cases:
                case_desc: str = case["description"]
                schema: dict[str, Any] = case["schema"]
                for test in case["tests"]:
                    test_desc: str = test["description"]
                    data: Any = test["data"]
                    expected_valid: bool = test["valid"]

                    param_id = f"{dialect}/{rel_path}/{case_desc}/{test_desc}"
                    failure_key = (
                        dialect,
                        str(rel_path),
                        case_desc,
                        test_desc,
                    )
                    marks: list[pytest.MarkDecorator] = []
                    if failure_key in _KNOWN_FAILURES:
                        marks.append(
                            pytest.mark.xfail(
                                reason=_KNOWN_FAILURES[failure_key],
                                strict=True,
                            )
                        )
                    params.append(
                        pytest.param(
                            config["validator_class"],
                            schema,
                            format_checker,
                            data,
                            expected_valid,
                            id=param_id,
                            marks=marks,
                        )
                    )

    return params


@pytest.mark.parametrize(
    "validator_class,schema,format_checker,data,expected_valid",
    _collect_params(),
)
def test_suite(
    validator_class: Any,
    schema: dict[str, Any],
    format_checker: Any,
    data: Any,
    expected_valid: bool,
) -> None:
    validator = validator_class(schema, format_checker=format_checker)
    errors = list(validator.iter_errors(data))
    is_valid = len(errors) == 0
    assert is_valid == expected_valid, (
        f"Expected valid={expected_valid}, got valid={is_valid}. "
        f"Errors: {[e.message for e in errors]}"
    )
