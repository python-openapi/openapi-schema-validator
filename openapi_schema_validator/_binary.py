"""Per-version detection of opaque binary ``bytes`` payload schemas.

This module is the single source of truth for deciding whether a schema
describes an *opaque binary* string payload for which a Python ``bytes``
instance should be accepted. It deliberately works on plain schema mappings
(pure functions, no validation side effects) so the predicates can be unit
tested directly -- importantly for the OAS 3.0 array-``type`` case, which
crashes the 3.0 ``type`` keyword if evaluated through validation.

Each OAS dialect declares "this is opaque binary" differently, so the
predicates are version scoped:

* OAS 3.0 uses ``format: binary`` (it has no ``contentMediaType`` /
  ``contentEncoding`` keywords).
* OAS 3.1 / 3.2 model raw binary with a *typeless* schema, optionally annotated
  with a non-text ``contentMediaType`` and no ``contentEncoding``. ``format`` is
  an annotation in 2020-12 and is therefore *not* a binary marker there.

The default 3.1 / 3.2 predicates additionally tolerate a common non-canonical
form (``type: string`` + non-text ``contentMediaType``) as a documented runtime
compatibility extension. The strict predicates recognize canonical typeless raw
binary only.

The acceptance of ``bytes`` lives exclusively in the keyword wrappers built here
(``build_binary_type`` and friends); the global ``"string"`` type checker is
never broadened to include ``bytes`` (see the design's architectural invariant).
"""

from collections.abc import Mapping
from typing import Any
from typing import Callable
from typing import Iterator

from jsonschema.exceptions import ValidationError

BinarySchemaPredicate = Callable[[Mapping[str, Any]], bool]
KeywordValidator = Callable[
    [Any, Any, Any, Mapping[str, Any]], Iterator[ValidationError]
]

# Media types that are textual even though they fall outside the ``text/*``
# tree. JSON Schema 2020-12 treats ``contentMediaType`` as describing the media
# type of the string's *contents*; for these the contents are text (a ``str``),
# not raw bytes, so they stay on the normal string path. Non-exhaustive on
# purpose: an unrecognized ``application/*`` subtype with no textual suffix
# defaults to opaque binary. Keep this easy to extend as new textual subtypes
# surface.
_TEXTUAL_MEDIA_TYPES = frozenset(
    {
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
    }
)

# Structured-syntax suffixes whose payloads are textual (e.g. ``image/svg+xml``,
# ``application/problem+json``, ``application/ld+json``).
_TEXTUAL_MEDIA_TYPE_SUFFIXES = ("+json", "+xml", "+yaml")

# ``contentEncoding`` values that denote identity / no-op transfer: the string
# is *not* an encoded representation, so the payload can still be raw binary.
_NOOP_CONTENT_ENCODINGS = frozenset({"identity", "binary", "7bit", "8bit"})

# ``format`` values that mean the string is base64-style encoded text in any
# OAS version.
_ENCODED_TEXT_FORMATS = frozenset({"byte", "base64"})


def _normalize_media_type(media_type: str) -> str:
    """Return the lowercased ``type/subtype`` with parameters stripped.

    Media types are case-insensitive (RFC 6838) and MAY carry parameters
    (``; charset=...``, ``; version=...``). Split on the first ``;``, keep the
    type/subtype portion, trim whitespace, then lowercase -- so
    ``application/problem+json; charset=utf-8`` stays textual and
    ``application/pdf; version=1`` stays opaque.
    """
    return media_type.split(";", 1)[0].strip().lower()


def _is_textual_media_type(media_type: str) -> bool:
    normalized = _normalize_media_type(media_type)
    if normalized.startswith("text/"):
        return True
    if normalized in _TEXTUAL_MEDIA_TYPES:
        return True
    return any(
        normalized.endswith(suffix) for suffix in _TEXTUAL_MEDIA_TYPE_SUFFIXES
    )


def _content_media_type(schema: Mapping[str, Any]) -> str | None:
    media_type = schema.get("contentMediaType")
    if isinstance(media_type, str):
        return media_type
    return None


def _has_non_text_content_media_type(schema: Mapping[str, Any]) -> bool:
    media_type = _content_media_type(schema)
    return media_type is not None and not _is_textual_media_type(media_type)


def _has_textual_content_media_type(schema: Mapping[str, Any]) -> bool:
    media_type = _content_media_type(schema)
    return media_type is not None and _is_textual_media_type(media_type)


def _is_encoded_text(schema: Mapping[str, Any]) -> bool:
    """Whether the schema's string is an *encoded* representation.

    Encoded strings are never opaque binary; they stay on the normal string
    path in every version. This covers ``format: byte`` / ``format: base64`` and
    -- for 3.1 / 3.2 -- any real ``contentEncoding`` (``base64``, ``base64url``,
    ``base16``, ``base32``, ``quoted-printable``, ...). A no-op identity
    encoding (``identity`` / ``binary`` / ``7bit`` / ``8bit``) does not count as
    encoded. Checked across versions so that, e.g., ``format: binary`` alongside
    ``contentEncoding: base64`` is correctly excluded.
    """
    fmt = schema.get("format")
    if isinstance(fmt, str) and fmt.strip().lower() in _ENCODED_TEXT_FORMATS:
        return True

    encoding = schema.get("contentEncoding")
    if encoding is None:
        return False
    if (
        isinstance(encoding, str)
        and encoding.strip().lower() in _NOOP_CONTENT_ENCODINGS
    ):
        return False
    # Any other present ``contentEncoding`` asserts the value is encoded text.
    return True


def _type_includes_string(schema: Mapping[str, Any]) -> bool:
    declared_type = schema.get("type")
    if declared_type == "string":
        return True
    return isinstance(declared_type, list) and "string" in declared_type


def _is_oas30_binary_candidate(schema: Mapping[str, Any]) -> bool:
    # OAS 3.0 does not permit array-valued ``type`` and the 3.0 ``type`` keyword
    # cannot evaluate one, so detection is restricted to scalar ``type``: no
    # ``type``, or exactly ``type: string``.
    if "type" not in schema:
        return True
    return schema.get("type") == "string"


def _is_oas31_binary_candidate(schema: Mapping[str, Any]) -> bool:
    # JSON Schema 2020-12 permits array-valued ``type`` and evaluates it
    # natively, so multi-type binary schemas are supported: no ``type``,
    # ``type: string``, or a ``type`` array that includes ``"string"``.
    if "type" not in schema:
        return True
    return _type_includes_string(schema)


def is_oas30_binary_schema(schema: Mapping[str, Any]) -> bool:
    """OAS 3.0 opaque binary: scalar-``type`` candidate plus ``format: binary``.

    ``format`` is the sole binary indicator in 3.0. Encoded co-presence (e.g.
    ``contentEncoding: base64`` or ``format: byte``) disqualifies the schema.
    """
    if not isinstance(schema, Mapping):
        return False
    if _is_encoded_text(schema):
        return False
    if not _is_oas30_binary_candidate(schema):
        return False
    fmt = schema.get("format")
    return isinstance(fmt, str) and fmt.strip().lower() == "binary"


def is_oas31_binary_schema(schema: Mapping[str, Any]) -> bool:
    """Default (runtime-friendly) OAS 3.1 opaque binary predicate.

    A candidate schema (no ``type`` / ``type: string`` / ``type`` array with
    ``"string"``) that is not encoded text, and is one of:

    * **no ``type`` and no textual ``contentMediaType``** -- the canonical
      raw-binary form (covers ``{}`` and
      ``{"contentMediaType": "application/octet-stream"}``); or
    * **``type`` includes ``"string"`` and a non-text ``contentMediaType``** --
      the pragmatic compatibility extension.

    Phrasing it this way keeps a typeless *text* schema like
    ``{"contentMediaType": "application/json"}`` from being mislabeled as binary.
    ``format: binary`` is not a binary indicator in 3.1.
    """
    if not isinstance(schema, Mapping):
        return False
    if _is_encoded_text(schema):
        return False
    if not _is_oas31_binary_candidate(schema):
        return False
    if "type" not in schema:
        # Canonical typeless raw binary: no textual contentMediaType.
        return not _has_textual_content_media_type(schema)
    # type includes "string" (guaranteed by the candidate gate): pragmatic
    # compatibility extension requires a non-text contentMediaType.
    return _has_non_text_content_media_type(schema)


def is_oas32_binary_schema(schema: Mapping[str, Any]) -> bool:
    """Default OAS 3.2 opaque binary predicate (identical to OAS 3.1)."""
    return is_oas31_binary_schema(schema)


def is_oas31_strict_binary_schema(schema: Mapping[str, Any]) -> bool:
    """Strict OAS 3.1 opaque binary predicate: canonical typeless raw binary.

    Recognizes only the typeless form (no ``type``, not encoded text, no textual
    ``contentMediaType``). A schema asserting ``type: string`` -- even with a
    non-text ``contentMediaType`` -- stays on the ordinary string path and
    rejects ``bytes``, preserving JSON Schema string typing.
    """
    if not isinstance(schema, Mapping):
        return False
    if _is_encoded_text(schema):
        return False
    if "type" in schema:
        return False
    return not _has_textual_content_media_type(schema)


def is_oas32_strict_binary_schema(schema: Mapping[str, Any]) -> bool:
    """Strict OAS 3.2 opaque binary predicate (identical to strict OAS 3.1)."""
    return is_oas31_strict_binary_schema(schema)


def build_binary_type(
    original: KeywordValidator,
    is_binary: BinarySchemaPredicate,
) -> KeywordValidator:
    """Wrap a ``type`` keyword to accept ``bytes`` for opaque binary schemas.

    When the instance is ``bytes`` and the schema is opaque binary for the
    active predicate, the instance is accepted as a string-compatible binary
    payload (no type assertion to violate). Every other case delegates to the
    original ``type`` validator unchanged.
    """

    def binary_type(
        validator: Any,
        data_type: Any,
        instance: Any,
        schema: Mapping[str, Any],
    ) -> Iterator[ValidationError]:
        if isinstance(instance, bytes) and is_binary(schema):
            return
        yield from original(validator, data_type, instance, schema)

    return binary_type


def build_binary_max_length(
    original: KeywordValidator,
    is_binary: BinarySchemaPredicate,
) -> KeywordValidator:
    """Wrap ``maxLength`` to enforce octet length for opaque binary ``bytes``.

    jsonschema's ``maxLength`` is guarded by ``is_type(instance, "string")`` and
    so no-ops on ``bytes``. For opaque binary ``bytes`` the bound is instead
    checked against ``len(instance)`` (the number of octets), matching the OAS
    3.2 statement that for unencoded binary "the length is the number of
    octets." Every other case delegates to the original validator.
    """

    def binary_max_length(
        validator: Any,
        max_length: Any,
        instance: Any,
        schema: Mapping[str, Any],
    ) -> Iterator[ValidationError]:
        if isinstance(instance, bytes) and is_binary(schema):
            if len(instance) > max_length:
                message = (
                    "is expected to be empty"
                    if max_length == 0
                    else "is too long"
                )
                yield ValidationError(f"{instance!r} {message}")
            return
        yield from original(validator, max_length, instance, schema)

    return binary_max_length


def build_binary_min_length(
    original: KeywordValidator,
    is_binary: BinarySchemaPredicate,
) -> KeywordValidator:
    """Wrap ``minLength`` to enforce octet length for opaque binary ``bytes``.

    Mirrors :func:`build_binary_max_length` for the lower bound.
    """

    def binary_min_length(
        validator: Any,
        min_length: Any,
        instance: Any,
        schema: Mapping[str, Any],
    ) -> Iterator[ValidationError]:
        if isinstance(instance, bytes) and is_binary(schema):
            if len(instance) < min_length:
                message = (
                    "should be non-empty"
                    if min_length == 1
                    else "is too short"
                )
                yield ValidationError(f"{instance!r} {message}")
            return
        yield from original(validator, min_length, instance, schema)

    return binary_min_length


def build_binary_format(
    original: KeywordValidator,
    is_binary: BinarySchemaPredicate,
) -> KeywordValidator:
    """Wrap ``format`` to skip text-oriented format checks on opaque binary.

    Format checks are text oriented and should not run on opaque binary
    ``bytes``. Every other case delegates to the original validator.
    """

    def binary_format(
        validator: Any,
        format: Any,
        instance: Any,
        schema: Mapping[str, Any],
    ) -> Iterator[ValidationError]:
        if isinstance(instance, bytes) and is_binary(schema):
            return
        yield from original(validator, format, instance, schema)

    return binary_format
