************************
openapi-schema-validator
************************

.. image:: https://img.shields.io/pypi/v/openapi-schema-validator.svg
     :target: https://pypi.org/project/openapi-schema-validator/
.. image:: https://github.com/python-openapi/openapi-schema-validator/actions/workflows/python-tests.yml/badge.svg
     :target: https://github.com/python-openapi/openapi-schema-validator/actions
.. image:: https://img.shields.io/codecov/c/github/python-openapi/openapi-schema-validator/master.svg?style=flat
     :target: https://codecov.io/github/python-openapi/openapi-schema-validator?branch=master
.. image:: https://img.shields.io/pypi/pyversions/openapi-schema-validator.svg
     :target: https://pypi.org/project/openapi-schema-validator/
.. image:: https://img.shields.io/pypi/format/openapi-schema-validator.svg
     :target: https://pypi.org/project/openapi-schema-validator/
.. image:: https://img.shields.io/pypi/status/openapi-schema-validator.svg
     :target: https://pypi.org/project/openapi-schema-validator/

About
#####

openapi-schema-validator is a Python library that validates schemas against:

* `OpenAPI Schema Specification v3.0 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#schemaObject>`__ which is an extended subset of the `JSON Schema Specification Wright Draft 00 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.1 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#schemaObject>`__ which is an extended superset of the `JSON Schema Specification Draft 2020-12 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.2 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.2.0.md#schemaObject>`__ using the published OAS 3.2 JSON Schema dialect resources.


Documentation
#############

Check documentation to see more details about the features. All documentation is in the "docs" directory and online at `openapi-schema-validator.readthedocs.io <https://openapi-schema-validator.readthedocs.io>`__


Installation
############

Recommended way (via pip):

.. code-block:: console

   pip install openapi-schema-validator

Alternatively you can download the code and install from the repository:

.. code-block:: console

   pip install "git+https://github.com/python-openapi/openapi-schema-validator.git"


Usage
#####

``validate`` call signature is:

.. code-block:: python

   validate(instance, schema, cls=OAS32Validator, allow_remote_references=False, **kwargs)

The first argument is always the value you want to validate.
The second argument is always the OpenAPI schema object.
The ``cls`` keyword argument is optional and defaults to ``OAS32Validator``.
Use ``cls`` when you need a specific validator version/behavior.

.. code-block:: python

   from openapi_schema_validator import OAS30Validator
   from openapi_schema_validator import OAS31Validator
   from openapi_schema_validator import validate

   # OpenAPI 3.0 behavior
   validate(instance, schema, cls=OAS30Validator)

   # OpenAPI 3.1 behavior
   validate(instance, schema, cls=OAS31Validator)

   # OpenAPI 3.2 behavior (default)
   validate(instance, schema)

Common forwarded keyword arguments include ``registry`` (reference context)
and ``format_checker`` (format validation behavior).
By default, ``validate`` uses a local-only empty registry to avoid implicit
remote ``$ref`` retrieval. To resolve external references, pass an explicit
``registry``. Set ``allow_remote_references=True`` only if you explicitly
accept jsonschema's default remote retrieval behavior.

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

Expected failure output:

.. code-block:: text

   Traceback (most recent call last):
       ...
   ValidationError: Additional properties are not allowed ('city' was unexpected)

By default, the latest OpenAPI schema syntax is expected.

Default dialect resolution
--------------------------

The OpenAPI 3.1 and 3.2 base dialect URIs are registered for
``jsonschema.validators.validator_for`` resolution.
Schemas declaring ``"$schema"`` as either
``"https://spec.openapis.org/oas/3.1/dialect/base"`` or
``"https://spec.openapis.org/oas/3.2/dialect/2025-09-17"`` resolve
directly to ``OAS31Validator`` and ``OAS32Validator`` without
unresolved-metaschema fallback warnings.

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

Binary Data Semantics
=====================

The handling of binary-like payloads differs between OpenAPI versions.

OpenAPI 3.0
-----------

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
------------

OpenAPI 3.1+ follows JSON Schema semantics for string typing in this library.

- ``type: string`` accepts ``str`` only (not ``bytes``)
- ``format: binary`` and ``format: byte`` are not treated as built-in formats
- for base64-in-JSON, model with ``contentEncoding: base64`` (optionally
  ``contentMediaType``)
- for raw binary payloads, model via media type (for example
  ``application/octet-stream``) rather than schema string formats

Regex Behavior
==============

By default, ``pattern`` handling follows host Python regex behavior.
For ECMAScript-oriented regex validation and matching (via ``regress``),
install the optional extra:

.. code-block:: console

   pip install "openapi-schema-validator[ecma-regex]"


For more details read about `Validation <https://openapi-schema-validator.readthedocs.io/en/latest/validation.html>`__.


Related projects
################
* `openapi-core <https://github.com/python-openapi/openapi-core>`__
   Python library that adds client-side and server-side support for the OpenAPI.
* `openapi-spec-validator <https://github.com/python-openapi/openapi-spec-validator>`__
   Python library that validates OpenAPI Specs against the OpenAPI 2.0 (aka Swagger) and OpenAPI 3.0 specification
