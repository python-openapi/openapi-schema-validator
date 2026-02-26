Schema validation
=================

The simplest way to validate an instance under OAS schema is to use the ``validate`` function.

Validate
--------

``validate`` call signature is:

.. code-block:: python

   validate(instance, schema, cls=OAS32Validator, allow_remote_references=False, **kwargs)

The first argument is always the value you want to validate.
The second argument is always the OpenAPI schema object.
The ``cls`` keyword argument is optional and defaults to ``OAS32Validator``.
Use ``cls`` when you need a specific validator version/behavior.
The ``allow_remote_references`` keyword argument is optional and defaults to
``False``.
Common forwarded keyword arguments include:

- ``registry`` for explicit external reference resolution context
- ``format_checker`` to control format validation behavior

By default, ``validate`` uses a local-only empty registry to avoid implicit
remote ``$ref`` retrieval.
Set ``allow_remote_references=True`` only if you explicitly accept
jsonschema's default remote retrieval behavior.

To validate an OpenAPI schema:

.. code-block:: python

   from openapi_schema_validator import validate

   # A sample schema
   schema = {
       "type": "object",
       "required": [
          "name"
       ],
       "properties": {
           "name": {
               "type": "string"
           },
           "age": {
               "type": ["integer", "null"],
               "format": "int32",
               "minimum": 0,
           },
           "birth-date": {
               "type": "string",
               "format": "date",
           },
           "address": {
                "type": 'array',
                "prefixItems": [
                    { "type": "number" },
                    { "type": "string" },
                    { "enum": ["Street", "Avenue", "Boulevard"] },
                    { "enum": ["NW", "NE", "SW", "SE"] }
                ],
                "items": False,
            }
       },
       "additionalProperties": False,
   }

   # If no exception is raised by validate(), the instance is valid.
   validate({"name": "John", "age": 23, "address": [1600, "Pennsylvania", "Avenue"]}, schema)

   validate({"name": "John", "city": "London"}, schema)

   Traceback (most recent call last):
       ...
   ValidationError: Additional properties are not allowed ('city' was unexpected)

By default, the latest OpenAPI schema syntax is expected.

Common pitfalls
---------------

- argument order matters: call ``validate(instance, schema)``, not
  ``validate(schema, instance)``
- ``validate`` does not load files from a path; load your OpenAPI document
  first and pass the parsed schema mapping
- ``validate`` treats the provided ``schema`` as the reference root; local
  references like ``#/components/...`` must exist within that mapping
- when a schema uses external references (for example ``urn:...``), provide
  reference context via ``registry=...`` as shown in :doc:`references`
- for schema fragments containing local references (for example,
  ``paths/.../responses/.../schema``), use a validator built from the full
  schema root and then validate the fragment via ``validator.evolve(...)``

Validators
----------

if you want to disambiguate the expected schema version, import and use ``OAS31Validator``:

.. code-block:: python

   from openapi_schema_validator import OAS31Validator

   validate({"name": "John", "age": 23}, schema, cls=OAS31Validator)

For OpenAPI 3.2, use ``OAS32Validator``.

In order to validate OpenAPI 3.0 schema, import and use ``OAS30Validator`` instead of ``OAS31Validator``.

.. code-block:: python

   from openapi_schema_validator import OAS30Validator

   # A sample schema
   schema = {
       "type": "object",
       "required": [
          "name"
       ],
       "properties": {
           "name": {
               "type": "string"
           },
           "age": {
               "type": "integer",
               "format": "int32",
               "minimum": 0,
               "nullable": True,
           },
           "birth-date": {
               "type": "string",
               "format": "date",
           }
       },
       "additionalProperties": False,
   }

   validate({"name": "John", "age": None}, schema, cls=OAS30Validator)

Default dialect resolution
--------------------------

The OpenAPI 3.1 and 3.2 base dialect URIs are registered for
``jsonschema.validators.validator_for`` resolution.
If your schema declares
``"$schema": "https://spec.openapis.org/oas/3.1/dialect/base"`` or
``"$schema": "https://spec.openapis.org/oas/3.2/dialect/2025-09-17"``,
``validator_for`` resolves directly to ``OAS31Validator`` or
``OAS32Validator`` without unresolved-metaschema fallback warnings.

.. code-block:: python

   from jsonschema.validators import validator_for

   from openapi_schema_validator import OAS31Validator
   from openapi_schema_validator import OAS32Validator

   schema = {
       "$schema": "https://spec.openapis.org/oas/3.1/dialect/base",
       "type": "object",
   }
   schema32 = {
       "$schema": "https://spec.openapis.org/oas/3.2/dialect/2025-09-17",
       "type": "object",
   }
   assert validator_for(schema) is OAS31Validator
   assert validator_for(schema32) is OAS32Validator

Schema errors vs instance errors
--------------------------------

The high-level ``validate(...)`` helper checks schema validity before instance
validation, following ``jsonschema.validate(...)`` behavior.
Malformed schema values (for example an invalid regex in ``pattern``) raise
``SchemaError``.

If you instantiate a validator class directly and call ``.validate(...)``,
schema checking is not performed automatically, matching
``jsonschema`` validator-class behavior.
For malformed regex patterns this may raise a lower-level regex error
(default mode) or ``ValidationError`` from the validator (ECMAScript mode).

Use ``<ValidatorClass>.check_schema(schema)`` first when you need deterministic
schema-validation errors with direct validator usage.

Read/write context
------------------

OpenAPI 3.0 schema comes with ``readOnly`` and ``writeOnly`` keywords. In order to validate read/write context in OpenAPI 3.0 schema, import and use ``OAS30ReadValidator`` or ``OAS30WriteValidator``.

.. code-block:: python

   from openapi_schema_validator import OAS30WriteValidator

   # A sample schema
   schema = {
       "type": "object",
       "required": [
          "name"
       ],
       "properties": {
           "name": {
               "type": "string"
           },
           "age": {
               "type": "integer",
               "format": "int32",
               "minimum": 0,
               "readOnly": True,
           },
           "birth-date": {
               "type": "string",
               "format": "date",
           }
       },
       "additionalProperties": False,
   }

   validate({"name": "John", "age": 23}, schema, cls=OAS30WriteValidator)

   Traceback (most recent call last):
       ...
   ValidationError: Tried to write read-only property with 23

Binary Data Semantics
---------------------

The handling of binary-like payloads differs between OpenAPI versions.

OpenAPI 3.0
~~~~~~~~~~~

OpenAPI 3.0 keeps historical ``format: binary`` / ``format: byte`` usage on
``type: string``.

**OAS30Validator (default - compatibility behavior)**

- ``type: string`` accepts ``str``
- ``type: string, format: binary`` accepts Python ``bytes`` and strings
- useful when validating Python-native runtime data

**OAS30StrictValidator**

- ``type: string`` accepts ``str`` only
- ``type: string, format: binary`` uses strict format validation
- use when you want strict, spec-oriented behavior for 3.0 schemas

OpenAPI 3.1+
~~~~~~~~~~~~

OpenAPI 3.1+ follows JSON Schema semantics for string typing in this library.

- ``type: string`` accepts ``str`` only (not ``bytes``)
- ``format: binary`` and ``format: byte`` are not treated as built-in formats
- for base64-in-JSON, model with ``contentEncoding: base64`` (optionally
  ``contentMediaType``)
- for raw binary payloads, model via media type (for example
  ``application/octet-stream``) rather than schema string formats

Quick Reference
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 28 24 24 24

   * - Context
     - ``"text"`` (str)
     - ``b"text"`` (bytes)
     - Notes
   * - OAS 3.0 + ``OAS30Validator``
     - Pass
     - Pass for ``format: binary``
     - Compatibility behavior for Python runtime payloads
   * - OAS 3.0 + ``OAS30StrictValidator``
     - Pass
     - Fail
     - Strict 3.0 validation mode
   * - OAS 3.1 + ``OAS31Validator``
     - Pass
     - Fail
     - Use ``contentEncoding``/``contentMediaType`` and media types
   * - OAS 3.2 + ``OAS32Validator``
     - Pass
     - Fail
     - Same semantics as OAS 3.1

Regex Behavior
--------------

Pattern validation follows one of two modes:

- default installation: follows host Python regex behavior
- ``ecma-regex`` extra installed: uses ``regress`` for ECMAScript-oriented
  regex validation and matching

Install optional ECMAScript regex support with:

.. code-block:: console

   pip install "openapi-schema-validator[ecma-regex]"

Example usage:

.. code-block:: python

   from openapi_schema_validator import OAS30StrictValidator
   from openapi_schema_validator import OAS30Validator

   # Pragmatic (default) - accepts bytes for binary format
   validator = OAS30Validator({"type": "string", "format": "binary"})
   validator.validate(b"binary data")  # passes

   # Strict - follows spec precisely
   validator = OAS30StrictValidator({"type": "string", "format": "binary"})
   validator.validate(b"binary data")  # raises ValidationError
