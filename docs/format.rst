Format check
============

You can check format for predefined OAS primitive types

.. code-block:: python

   from openapi_schema_validator import oas31_format_checker

   validate({"name": "John", "birth-date": "-12"}, schema, format_checker=oas31_format_checker)

   Traceback (most recent call last):
       ...
   ValidationError: '-12' is not a 'date'

For OpenAPI 3.2, use ``oas32_format_checker`` (behaves identically to ``oas31_format_checker``, since 3.2 uses the same JSON Schema dialect).
