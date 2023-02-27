References
==========

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
