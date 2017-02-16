Creating a JSON Schema
----------------------

Before we can do anything, we need a JSON schema. doctor can load a
schema from an external file, it supports both YAML and JSON formats. The schema
contains a list of definitions of your request parameters and optionally what
schemas your responses should have for your endpoints. The schema files also
support referencing a definition in another file within the schema directory 
using a `$ref` as shown in the example below.

.. code-block:: yaml

    ---
    $schema: 'http://json-schema.org/draft-04/schema#'
    definitions:
      auth:
        $ref: 'common.yaml#/defintions/auth' 

When defininig a definition we must provide the following: 

- *description* - A description of the definition we are defining.
- *type* - One or more valid `json schema types <https://spacetelescope.github.io/understanding-json-schema/reference/type.html>`_.  An array of types is acceptable if the 
  definition can have multiple types.  An example might be a definition that is
  a `number` but is also allowed to be `null`.
- *example* - An example value of the definition.  This is used when generating
  documentation.  The values are sent as request params to produce example
  responses.

Let's say we have a schema.yaml with the following:

.. literalinclude:: examples/schema.yaml
   :language: yaml
