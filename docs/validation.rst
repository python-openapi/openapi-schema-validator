Schema validation
=================

The simplest way to validate an instance under OAS schema is to use the ``validate`` function.

Validate
--------

To validate an OpenAPI v3.1 schema:

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

Validators
----------

if you want to disambiguate the expected schema version, import and use ``OAS31Validator``:

.. code-block:: python

   from openapi_schema_validator import OAS31Validator

   validate({"name": "John", "age": 23}, schema, cls=OAS31Validator)

The OpenAPI 3.1 base dialect URI is registered for
``jsonschema.validators.validator_for`` resolution.
If your schema declares
``"$schema": "https://spec.openapis.org/oas/3.1/dialect/base"``,
``validator_for`` resolves directly to ``OAS31Validator`` without
unresolved-metaschema fallback warnings.

.. code-block:: python

   from jsonschema.validators import validator_for

   from openapi_schema_validator import OAS31Validator

   schema = {
       "$schema": "https://spec.openapis.org/oas/3.1/dialect/base",
       "type": "object",
   }
   assert validator_for(schema) is OAS31Validator

For OpenAPI 3.2, use ``OAS32Validator`` (behaves identically to ``OAS31Validator``, since 3.2 uses the same JSON Schema dialect).

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

Strict vs Pragmatic Validators
------------------------------

OpenAPI 3.0 has two validator variants with different behaviors for binary format:

**OAS30Validator (default - pragmatic)**

- Accepts Python ``bytes`` for ``type: string`` with ``format: binary``
- More lenient for Python use cases where binary data is common
- Use when validating Python objects directly

**OAS30StrictValidator**

- Follows OAS spec strictly: only accepts ``str`` for ``type: string``
- For ``format: binary``, only accepts base64-encoded strings
- Use when strict spec compliance is required

Comparison Matrix
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 20 22 23

   * - Schema
     - Value
     - OAS30Validator (default)
     - OAS30StrictValidator
   * - ``type: string``
     - ``"test"`` (str)
     - Pass
     - Pass
   * - ``type: string``
     - ``b"test"`` (bytes)
     - **Fail**
     - **Fail**
   * - ``type: string, format: binary``
     - ``b"test"`` (bytes)
     - Pass
     - **Fail**
   * - ``type: string, format: binary``
     - ``"dGVzdA=="`` (base64)
     - Pass
     - Pass
   * - ``type: string, format: binary``
     - ``"test"`` (plain str)
     - Pass
     - **Fail**

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
