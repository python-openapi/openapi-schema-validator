openapi-schema-validator
========================

.. toctree::
   :hidden:
   :maxdepth: 2

   validation
   format
   references
   contributing

Openapi-schema-validator is a Python library that validates schema against:

* `OpenAPI Schema Specification v3.0 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#schemaObject>`__ which is an extended subset of the `JSON Schema Specification Wright Draft 00 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.1 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#schemaObject>`__ which is an extended superset of the `JSON Schema Specification Draft 2020-12 <http://json-schema.org/>`__.
* `OpenAPI Schema Specification v3.2 <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.2.0.md#schemaObject>`__ using the published OAS 3.2 JSON Schema dialect resources.

Installation
------------

.. md-tab-set::

   .. md-tab-item:: Pip + PyPI (recommended)

      .. code-block:: console

         pip install openapi-schema-validator

   .. md-tab-item:: Pip + the source

      .. code-block:: console

         pip install -e git+https://github.com/python-openapi/openapi-schema-validator.git#egg=openapi_schema_validator

Usage
-----

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

Read more about the :doc:`validation`.

Related projects
----------------

* `openapi-core <https://github.com/python-openapi/openapi-core>`__
   Python library that adds client-side and server-side support for the OpenAPI v3.0 and OpenAPI v3.1 specification.
* `openapi-spec-validator <https://github.com/python-openapi/openapi-spec-validator>`__
   Python library that validates OpenAPI Specs against the OpenAPI 2.0 (aka Swagger), OpenAPI 3.0 and OpenAPI 3.1 specification. The validator aims to check for full compliance with the Specification.

License
-------

The project is under the terms of BSD 3-Clause License.
