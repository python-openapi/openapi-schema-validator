References
==========

You can resolve JSON Schema references by passing registry

.. code-block:: python

   from openapi_schema_validator import validate
   from referencing import Registry, Resource
   from referencing.jsonschema import DRAFT202012

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
   # In-schema identifier
   name_schema = Resource.from_contents({
       "$schema": "https://json-schema.org/draft/2020-12/schema",
       "type": "string",
   })
   # Explicit identifier
   age_schema = DRAFT202012.create_resource({
       "type": "integer",
       "format": "int32",
       "minimum": 0,
       "maximum": 120,
   })
   # Default identifier
   birth_date_schema = Resource.from_contents({
       "type": "string",
       "format": "date",
   }, default_specification=DRAFT202012)
   registry = Registry().with_resources(
       [
           ("urn:name-schema", name_schema),
           ("urn:age-schema", age_schema),
           ("urn:birth-date-schema", birth_date_schema),
       ],
   )

   validate({"name": "John", "age": 23}, schema, registry=registry)

For more information about resolving references see `JSON (Schema) Referencing <https://python-jsonschema.readthedocs.io/en/latest/referencing/>`__
