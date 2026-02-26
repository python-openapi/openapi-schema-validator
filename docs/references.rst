References
==========

You can resolve JSON Schema references by passing registry.
The ``validate(instance, schema, ...)`` shortcut resolves local references
(``#/...``) against the provided ``schema`` mapping.
By default, the shortcut uses a local-only empty registry and does not
implicitly retrieve remote references.
If needed, ``allow_remote_references=True`` enables jsonschema's default
remote retrieval behavior.

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
               "$ref": "urn:name-schema"
           },
           "age": {
               "$ref": "urn:age-schema"
           },
           "birth-date": {
               "$ref": "urn:birth-date-schema"
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

   # If no exception is raised by validate(), the instance is valid.
   validate({"name": "John", "age": 23}, schema, registry=registry)

   # raises error
   validate({"birth-date": "yesterday", "age": -1}, schema, registry=registry)

   Traceback (most recent call last):
       ...
   ValidationError: 'name' is a required property

For more information about resolving references see `JSON (Schema) Referencing <https://python-jsonschema.readthedocs.io/en/latest/referencing/>`__
