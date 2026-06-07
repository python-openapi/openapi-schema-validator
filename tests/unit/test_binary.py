"""Unit coverage for the per-version opaque-binary schema predicates.

These predicates are pure functions on the schema mapping, so they are asserted
directly without invoking validation. That is important for the OAS 3.0 array
``type`` case, which would otherwise crash the 3.0 ``type`` keyword.
"""

import pytest

from openapi_schema_validator._binary import is_oas30_binary_schema
from openapi_schema_validator._binary import is_oas31_binary_schema
from openapi_schema_validator._binary import is_oas31_strict_binary_schema
from openapi_schema_validator._binary import is_oas32_binary_schema
from openapi_schema_validator._binary import is_oas32_strict_binary_schema

OCTET = "application/octet-stream"

ALL_PREDICATES = [
    is_oas30_binary_schema,
    is_oas31_binary_schema,
    is_oas32_binary_schema,
    is_oas31_strict_binary_schema,
    is_oas32_strict_binary_schema,
]


@pytest.mark.parametrize("predicate", ALL_PREDICATES)
@pytest.mark.parametrize("schema", [True, False, None, "x", 1, ["string"]])
def test_non_mapping_schema_is_false(predicate, schema):
    # Boolean / non-mapping schemas are never classified as binary.
    assert predicate(schema) is False


class TestIsOAS30BinarySchema:
    @pytest.mark.parametrize(
        "schema",
        [
            {"type": "string", "format": "binary"},
            {"format": "binary"},
        ],
    )
    def test_binary_marker_is_true(self, schema):
        assert is_oas30_binary_schema(schema) is True

    @pytest.mark.parametrize(
        "schema",
        [
            {"type": "string"},
            {"type": "string", "format": "byte"},
            {"type": "string", "format": "base64"},
            {"type": "integer", "format": "binary"},
            {"type": "string", "format": "date"},
            {},
        ],
    )
    def test_non_binary_is_false(self, schema):
        assert is_oas30_binary_schema(schema) is False

    def test_array_type_is_false(self):
        # Array-valued type is out of scope for OAS 3.0. The predicate must not
        # mask the (separately latent) crashing schema -- assert directly,
        # never via validation.
        schema = {"type": ["string", "null"], "format": "binary"}

        assert is_oas30_binary_schema(schema) is False

    def test_encoding_co_presence_excludes(self):
        # format: binary alongside a real contentEncoding is encoded text -- the
        # encoding wins, so this is not classified as binary.
        schema = {
            "type": "string",
            "format": "binary",
            "contentEncoding": "base64",
        }

        assert is_oas30_binary_schema(schema) is False

    def test_non_mapping_is_false(self):
        assert is_oas30_binary_schema(True) is False


class TestIsOAS31BinarySchema:
    @pytest.mark.parametrize(
        "schema",
        [
            {},
            {"contentMediaType": OCTET},
            {"type": "string", "contentMediaType": OCTET},
            {"type": ["string", "null"], "contentMediaType": OCTET},
            {"contentMediaType": "application/pdf"},
            {"contentMediaType": "image/png"},
            {"contentMediaType": "audio/mpeg"},
            {"contentMediaType": "video/mp4"},
            # no-op identity encodings do not count as encoded text
            {"contentMediaType": OCTET, "contentEncoding": "identity"},
            {"contentMediaType": OCTET, "contentEncoding": "binary"},
            {"contentMediaType": OCTET, "contentEncoding": "7bit"},
            {"contentMediaType": OCTET, "contentEncoding": "8bit"},
            # case-insensitive media-type matching, parameter stripping
            {"type": "string", "contentMediaType": "Image/PNG"},
            {
                "type": "string",
                "contentMediaType": "application/pdf; version=1",
            },
        ],
    )
    def test_binary_is_true(self, schema):
        assert is_oas31_binary_schema(schema) is True

    @pytest.mark.parametrize(
        "schema",
        [
            # typeless text is NOT binary (tightened phrasing)
            {"contentMediaType": "application/json"},
            {"contentMediaType": "application/ld+json"},
            {"contentMediaType": "image/svg+xml"},
            {"contentMediaType": "text/plain"},
            # plain string assertion, no binary marker
            {"type": "string"},
            {"type": "string", "contentMediaType": "application/json"},
            {
                "type": "string",
                "contentMediaType": "application/problem+json; charset=utf-8",
            },
            # format: binary is not a 3.1 binary marker
            {"type": "string", "format": "binary"},
            # encoded text is never opaque binary
            {"type": "string", "format": "byte"},
            {"type": "string", "format": "base64"},
            {
                "type": "string",
                "contentMediaType": OCTET,
                "contentEncoding": "base64",
            },
            {
                "type": "string",
                "contentMediaType": OCTET,
                "contentEncoding": "base64url",
            },
            {
                "type": "string",
                "contentMediaType": OCTET,
                "contentEncoding": "base16",
            },
            {
                "type": "string",
                "contentMediaType": OCTET,
                "contentEncoding": "base32",
            },
            {
                "type": "string",
                "contentMediaType": OCTET,
                "contentEncoding": "quoted-printable",
            },
            # typeless encoded schema: excluded by the encoded-text gate
            {"contentMediaType": OCTET, "contentEncoding": "base16"},
            # type without "string" is not a candidate
            {"type": "integer", "contentMediaType": OCTET},
        ],
    )
    def test_non_binary_is_false(self, schema):
        assert is_oas31_binary_schema(schema) is False

    def test_non_mapping_is_false(self):
        assert is_oas31_binary_schema(True) is False


class TestIsOAS31StrictBinarySchema:
    @pytest.mark.parametrize(
        "schema",
        [
            {},
            {"contentMediaType": OCTET},
            {"contentMediaType": "application/pdf"},
            {"contentMediaType": "application/pdf; version=1"},
        ],
    )
    def test_typeless_raw_binary_is_true(self, schema):
        assert is_oas31_strict_binary_schema(schema) is True

    @pytest.mark.parametrize(
        "schema",
        [
            # any type assertion stays on the string path under strict mode
            {"type": "string", "contentMediaType": OCTET},
            {"type": ["string", "null"], "contentMediaType": OCTET},
            {"type": "string", "format": "binary"},
            {"type": "string"},
            # encoded / textual typeless schemas are not raw binary
            {"contentMediaType": OCTET, "contentEncoding": "base16"},
            {"contentMediaType": "application/json"},
            {"contentMediaType": "image/svg+xml"},
        ],
    )
    def test_non_raw_binary_is_false(self, schema):
        assert is_oas31_strict_binary_schema(schema) is False


class TestMediaTypeClassification:
    @pytest.mark.parametrize(
        "media_type",
        [
            "text/plain",
            "text/csv",
            "application/json",
            "application/xml",
            "application/x-www-form-urlencoded",
            "application/javascript",
            "application/ecmascript",
            "application/yaml",
            "application/x-yaml",
            "application/graphql",
            "application/x-ndjson",
            "application/csv",
            "application/ld+json",
            "application/problem+json",
            "image/svg+xml",
            "application/vnd.api+yaml",
            # case-insensitive + parameters
            "Application/JSON",
            "application/json; charset=utf-8",
            "application/problem+json; charset=utf-8",
        ],
    )
    def test_textual_media_types_are_not_binary(self, media_type):
        # Under a type: string assertion, textual content stays on the string
        # path, so the default predicate is False.
        schema = {"type": "string", "contentMediaType": media_type}

        assert is_oas31_binary_schema(schema) is False

    @pytest.mark.parametrize(
        "media_type",
        [
            "application/octet-stream",
            "application/pdf",
            "application/zip",
            "application/vnd.ms-excel",
            "image/png",
            "image/jpeg",
            "audio/mpeg",
            "video/mp4",
            # case-insensitive + parameters
            "Application/PDF",
            "application/pdf; version=1.7",
        ],
    )
    def test_opaque_media_types_are_binary(self, media_type):
        schema = {"type": "string", "contentMediaType": media_type}

        assert is_oas31_binary_schema(schema) is True


class TestEncodingExclusion:
    @pytest.mark.parametrize(
        "encoding",
        ["base64", "base64url", "base16", "base32", "quoted-printable"],
    )
    def test_real_encoding_excludes_binary(self, encoding):
        schema = {
            "type": "string",
            "contentMediaType": OCTET,
            "contentEncoding": encoding,
        }

        assert is_oas31_binary_schema(schema) is False

    @pytest.mark.parametrize(
        "encoding", ["identity", "binary", "7bit", "8bit"]
    )
    def test_noop_encoding_keeps_binary(self, encoding):
        schema = {
            "type": "string",
            "contentMediaType": OCTET,
            "contentEncoding": encoding,
        }

        assert is_oas31_binary_schema(schema) is True


class TestCrossVersionDivergence:
    def test_format_binary_is_binary_in_oas30_only(self):
        schema = {"type": "string", "format": "binary"}

        assert is_oas30_binary_schema(schema) is True
        assert is_oas31_binary_schema(schema) is False
        assert is_oas32_binary_schema(schema) is False

    def test_typeless_content_media_type_is_binary_in_oas31_plus_only(self):
        schema = {"contentMediaType": OCTET}

        assert is_oas30_binary_schema(schema) is False
        assert is_oas31_binary_schema(schema) is True
        assert is_oas32_binary_schema(schema) is True

    @pytest.mark.parametrize(
        "schema",
        [
            {},
            {"contentMediaType": OCTET},
            {"type": "string", "contentMediaType": OCTET},
            {"type": ["string", "null"], "contentMediaType": OCTET},
            {"type": "string", "contentMediaType": "application/json"},
            {"type": "string", "format": "binary"},
            {"contentMediaType": OCTET, "contentEncoding": "base16"},
        ],
    )
    def test_oas32_default_matches_oas31_default(self, schema):
        assert is_oas32_binary_schema(schema) == is_oas31_binary_schema(schema)

    @pytest.mark.parametrize(
        "schema",
        [
            {},
            {"contentMediaType": OCTET},
            {"type": "string", "contentMediaType": OCTET},
            {"contentMediaType": "application/json"},
            {"contentMediaType": OCTET, "contentEncoding": "base16"},
        ],
    )
    def test_oas32_strict_matches_oas31_strict(self, schema):
        assert is_oas32_strict_binary_schema(
            schema
        ) == is_oas31_strict_binary_schema(schema)
