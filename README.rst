************************
openapi-schema-validator
************************

.. image:: https://img.shields.io/pypi/v/openapi-schema-validator.svg
     :target: https://pypi.python.org/pypi/openapi-schema-validator
.. image:: https://github.com/python-openapi/openapi-schema-validator/actions/workflows/python-tests.yml/badge.svg
     :target: https://github.com/python-openapi/openapi-schema-validator/actions
.. image:: https://img.shields.io/codecov/c/github/python-openapi/openapi-schema-validator/master.svg?style=flat
     :target: https://codecov.io/github/python-openapi/openapi-schema-validator?branch=master
.. image:: https://img.shields.io/pypi/pyversions/openapi-schema-validator.svg
     :target: https://pypi.python.org/pypi/openapi-schema-validator
.. image:: https://img.shields.io/pypi/format/openapi-schema-validator.svg
     :target: https://pypi.python.org/pypi/openapi-schema-validator
.. image:: https://img.shields.io/pypi/status/openapi-schema-validator.svg
     :target: https://pypi.python.org/pypi/openapi-schema-validator

About
#####

Openapi-schema-validator is a Python library that validates schema against:

* `OpenAPI Schema Specification v3.0 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#schemaObject>`__ which is an extended subset of the `JSON Schema Specification Wright Draft 00 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.1 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#schemaObject>`__ which is an extended superset of the `JSON Schema Specification Draft 2020-12 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.2 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.2.0.md#schemaObject>`__ which uses the same JSON Schema dialect as v3.1.


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

   pip install -e git+https://github.com/python-openapi/openapi-schema-validator.git#egg=openapi_schema_validator


Usage
#####

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

The OpenAPI 3.1 base dialect URI is registered for
``jsonschema.validators.validator_for`` resolution.
Schemas declaring
``"$schema": "https://spec.openapis.org/oas/3.1/dialect/base"``
resolve directly to ``OAS31Validator`` without unresolved-metaschema
fallback warnings.

.. code-block:: python

   from jsonschema.validators import validator_for

   from openapi_schema_validator import OAS31Validator

   schema = {
       "$schema": "https://spec.openapis.org/oas/3.1/dialect/base",
       "type": "object",
   }

   assert validator_for(schema) is OAS31Validator


Strict vs Pragmatic Validators
==============================

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
-----------------

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

For more details read about `Validation <https://openapi-schema-validator.readthedocs.io/en/latest/validation.html>`__.


Related projects
################
* `openapi-core <https://github.com/python-openapi/openapi-core>`__
   Python library that adds client-side and server-side support for the OpenAPI.
* `openapi-spec-validator <https://github.com/python-openapi/openapi-spec-validator>`__
   Python library that validates OpenAPI Specs against the OpenAPI 2.0 (aka Swagger) and OpenAPI 3.0 specification
