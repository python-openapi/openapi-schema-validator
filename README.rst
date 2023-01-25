************************
openapi-schema-validator
************************

.. image:: https://img.shields.io/pypi/v/openapi-schema-validator.svg
     :target: https://pypi.python.org/pypi/openapi-schema-validator
.. image:: https://travis-ci.org/p1c2u/openapi-schema-validator.svg?branch=master
     :target: https://travis-ci.org/p1c2u/openapi-schema-validator
.. image:: https://img.shields.io/codecov/c/github/p1c2u/openapi-schema-validator/master.svg?style=flat
     :target: https://codecov.io/github/p1c2u/openapi-schema-validator?branch=master
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

Installation
############

Recommended way (via pip):

::

    $ pip install openapi-schema-validator

Alternatively you can download the code and install from the repository:

.. code-block:: bash

   $ pip install -e git+https://github.com/p1c2u/openapi-schema-validator.git#egg=openapi_schema_validator


Usage
#####

By default, the latest OpenAPI schema syntax is expected.

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

if you want to disambiguate the expected schema version, import and use ``OAS31Validator``:

.. code-block:: python

   from openapi_schema_validator import OAS31Validator

   validate({"name": "John", "age": 23}, schema, cls=OAS31Validator)

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

In order to validate read/write context in OpenAPI 3.0 schema, import and use ``OAS30ReadValidator`` or ``OAS30WriteValidator``.

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

Format check
************

You can also check format for primitive types

.. code-block:: python

   from openapi_schema_validator import oas31_format_checker

   validate({"name": "John", "birth-date": "-12"}, schema, format_checker=oas31_format_checker)

   Traceback (most recent call last):
       ...
   ValidationError: '-12' is not a 'date'

References
**********

You can resolve JSON references by passing custon reference resolver

.. code-block:: python

   from jsonschema.validators import RefResolver

   # A schema with reference
   schema = {
       "type" : "object",
       "required": [
          "name"
       ],
       "properties": {
           "name": {
               "$ref": "#/components/schemas/Name"
           },
           "age": {
               "$ref": "#/components/schemas/Age"
           },
           "birth-date": {
               "$ref": "#/components/schemas/BirthDate"
           }
       },
       "additionalProperties": False,
   }
   # Referenced schemas
   schemas = {
       "components": {
           "schemas": {
               "Name": {
                   "type": "string"
               },
               "Age": {
                   "type": "integer",
                   "format": "int32",
                   "minimum": 0,
                   "nullable": True,
               },
               "BirthDate": {
                   "type": "string",
                   "format": "date",
               }
           },
       },
   }

   ref_resolver = RefResolver.from_schema(schemas)

   validate({"name": "John", "age": 23}, schema, resolver=ref_resolver)

For more information about reference resolver see `Resolving JSON References <https://python-jsonschema.readthedocs.io/en/stable/references/>`__

Related projects
################
* `openapi-core <https://github.com/p1c2u/openapi-core>`__
   Python library that adds client-side and server-side support for the OpenAPI.
* `openapi-spec-validator <https://github.com/p1c2u/openapi-spec-validator>`__
   Python library that validates OpenAPI Specs against the OpenAPI 2.0 (aka Swagger) and OpenAPI 3.0 specification
