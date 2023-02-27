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
