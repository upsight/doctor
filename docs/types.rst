.. _doctor-types:

Types
=====

Doctor :ref:`types<types-module-documentation>` validate request parameters
passed to logic functions.  Every request parameter that gets passed to your
logic function should define a type from one of those below.  See 
:ref:`quick type creation<quick-type-creation>` for 
functions that allow you to create types easily on the fly.

String
------

A :class:`~doctor.types.String` type represents a `str` and allows you to
define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types.String.format` - An identifier indicating a complex 
  datatype with a string representation. For example `date`, to represent an 
  ISO 8601 formatted date string.  The following formats are supported:

    * `date` - Will parse the string as a `datetime.datetime` instance.  Expects
      the format `'%Y-%m-%d'`
    * `date-time` - Will parse the string as a `datetime.datetime` instance.
      Expects a valid ISO8601 string.  e.g. `'2018-02-21T16:09:02Z'`
    * `email` - Does basic validation that the string is an email by checking
      for an `'@'` character in the string.
    * `time` - Will parse the string as a `datetime.datetime` instance.  Expects
      the format `'%H:%M:%S'`
    * `uri` - Will validate the string is a valid URI.

* :attr:`~doctor.types.String.max_length` - The maximum length of the string.
* :attr:`~doctor.types.String.min_length` - The minimum length of the string.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.
* :attr:`~doctor.types.String.pattern` - A regex pattern the string should
  match anywhere whitin it.  Uses `re.search`.
* :attr:`~doctor.types.String.trim_whitespace` - If `True` the string will be
  trimmed of whitespace.

Example
#######

.. code-block:: python

    from doctor.types import String

    class FirstName(String):
        description = "A user's first name."
        min_length = 1
        max_length = 255
        trim_whitespace = True

Number
------

A :class:`~doctor.types.Number` type represents a `float` and allows you to
define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types._NumericType.exclusive_maximum`- If `True` and
  :attr:`~doctor.types._NumericType.maximum` is set, the maximum value should
  be treated as exclusive (value can not be equal to maximum).
* :attr:`~doctor.types._NumericType.exclusive_minimum`- If `True` and
  :attr:`~doctor.types._NumericType.minimum` is set, the minimum value should
  be treated as exclusive (value can not be equal to minimum).
* :attr:`~doctor.types._NumericType.maximum` - The maximum value allowed.
* :attr:`~doctor.types._NumericType.minimum` - The minimum value allowed.
* :attr:`~doctor.types._NumericType.multiple_of` - The value is required to be
  a multiple of this value.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.

Example
#######

.. code-block:: python

    from doctor.types import Number

    class AverageRating(Number):
        description = 'The average rating.'
        exclusive_maximum = False
        exclusive_minimum = True
        minimum = 0.00
        maximum = 10.0

Integer
-------

An :class:`~doctor.types.Integer` type represents an `int` and allows you to
define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types._NumericType.exclusive_maximum`- If `True` and the
  :attr:`~doctor.types._NumericType.maximum` is set, the maximum value should
  be treated as exclusive (value can not be equal to maximum).
* :attr:`~doctor.types._NumericType.exclusive_minimum`- If `True` and the
  :attr:`~doctor.types._NumericType.minimum` is set, the minimum value should
  be treated as exclusive (value can not be equal to minimum).
* :attr:`~doctor.types._NumericType.maximum` - The maximum value allowed.
* :attr:`~doctor.types._NumericType.minimum` - The minimum value allowed.
* :attr:`~doctor.types._NumericType.multiple_of` - The value is required to be
  a multiple of this value.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.

Example
#######

.. code-block:: python

    from doctor.types import Integer

    class Age(Integer):
        description = 'The age of the user.'
        exclusive_maximum = False
        exclusive_minimum = True
        minimum = 1
        maximum = 120

Boolean
-------

A :class:`~doctor.types.Boolean` type represents a `bool`.  This type will
convert several common strings used as booleans to a boolean type when
instaniated.  The following `str` values (case-insensitve) will be converted to
a boolean:

*  `'true'`/`'false'`
* `'on'`/`'off'`
* `'1'`/`'0'`

It also accepts typical truthy inputs e.g. `True`, `False`, `1`, `0`.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.

Example
#######

.. code-block:: python

    from doctor.types import Boolean

    class Accept(Boolean):
        description = 'Indicates if the user accepted the agreement or not.'

Enum
----

An :class:`~doctor.types.Enum` type represents a `str` that should be one of
any defined values and allows you to define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.Enum.enum` - A list of `str` containing valid values.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.

Example
#######

.. code-block:: python

    from doctor.types import Enum

    class Color(Enum):
        description = 'A color.'
        enum = ['blue', 'green', 'purple', 'yellow']


Object
------

An :class:`~doctor.types.Object` type represents a `dict` and allows you to
define properties and required properties.

Attributes
##########

* :attr:`~doctor.types.Object.additional_properties` - If `True`, additional
  properties (that is, ones not defined in
  :attr:`~doctor.types.Object.properties`) will be allowed.
* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.
* :attr:`~doctor.types.Object.properties` - A dict containing a mapping of
  property name to expected type.
* :attr:`~doctor.types.Object.required` - A list of required properties.
* :attr:`~doctor.types.Object.title` - An optional title for your object. This
  value will be used when generating documentation about objects in requests
  and responses.

Example
#######

.. code-block:: python

    from doctor.types import Object, boolean, string

    class Contact(Object):
        description = 'An address book contact.'
        additional_properties = True
        properties = {
            'name': string('The contact name', min_length=1, max_length=200),
            'is_primary', boolean('Indicates if this is a primary contact.'),
        }
        required = ['name']

Array
-----

An :class:`~doctor.types.Array` type represents a `list` and allows you to
define properties and required properties.

Attributes
##########

* :attr:`~doctor.types.Array.additional_items` - If :attr:`~doctor.types.Array.items`
  is a list and this is `True` then additional items whose types aren't defined
  are allowed in the list.
* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This is optional and a default
  example value will be generated for you.
* :attr:`~doctor.types.Array.items` - The type each item should be, or a list of
  types where the position of the type in the list represents the type at that
  position in the array the item should be.
* :attr:`~doctor.types.Array.min_items` - The minimum number of items allowed
  in the list.
* :attr:`~doctor.types.Array.max_items` - The maximum number of items allowed
  in the list.
* :attr:`~doctor.types.SuperType.nullable` - Indicates if the value of this type
  is allowed to be None.
* :attr:`~doctor.types.SuperType.param_name` - The name of the request parameter
  that should map to your logic function annotated parameter.  If not specified
  it expects the request parameter will be named the same as the logic function
  parameter name.
* :attr:`~doctor.types.Array.unique_items` - If `True`, items in the array
  should be unique from one another.

Example
#######

.. code-block:: python

    from doctor.types import Array, string

    class Countries(Array):
        description = 'An array of countries.'
        items = string('A country')
        min_items = 0
        max_items = 5
        unique_items = True

JsonSchema
----------

A :class:`~doctor.types.JsonSchema` type is primarily meant to ease the transition
from doctor `2.x.x` to `3.0.0`.  It allows you to specify an already defined
schema file to represent a type.  You can use a definition within the schema
as your type or the root type of the schema.

This type will use the json schema to set the description, example and native
type attributes of the class.  This type should not be used directly, instead
you should use :func:`~doctor.types.json_schema_type` to create your class.

Attributes
##########

* :attr:`~doctor.types.JsonSchema.definition_key` - The key of the definition
  within your schema that should be used for the type.
* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
  This value will automatically get loaded from your schema definition.
* :attr:`~doctor.types.SuperType.example` - An example value to send to the
  endpoint when generating API documentation.  This value will automatically
  get loaded from your schema definition.
* :attr:`~doctor.types.JsonSchema.schema_file` - The full path to the schema file.
  This attribute is required to be defined on your class.

Example
#######

**annotation.yaml**

.. code-block:: yaml

    ---
    $schema: 'http://json-schema.org/draft-04/schema#'
    description: An annotation.
    definitions:
      annotation_id:
        description: Auto-increment ID.
        example: 1
        type: integer
      name:
        description: The name of the annotation.
        example: Example Annotation.
        type: string
    type: object
    properties:
      annotation_id:
        $ref: '#/definitions/annotation_id'
      name:
        $ref: '#/definitions/name'
    additionalProperties: false
   
**Using `definition_key`**

.. code-block:: python

    from doctor.types import json_schema_type

    AnnotationId = json_schema_type(
        '/full/path/to/annoation.yaml', definition_key='annotation_id')

**Without `definition_key`**

.. code-block:: python

    from doctor.types import json_schema_type

    Annotation = json_schema_type('/full/path/to/annotation.yaml')


.. _quick-type-creation:

Quick Type Creation
-------------------

Each type also has a function that can be used to quickly create a new type
without having to define large classes.  Each of these functions takes the
description of the type as the first positional argument and any attributes
the type accepts can be passed as keyword arguments.  The following functions
are provided:

* :func:`~doctor.types.array` - Create a new :class:`~doctor.types.Array` type.
* :func:`~doctor.types.boolean` - Create a new :class:`~doctor.types.Boolean` type.
* :func:`~doctor.types.enum` - Create a new :class:`~doctor.types.Enum` type.
* :func:`~doctor.types.integer` - Create a new :class:`~doctor.types.Integer` type.
* :func:`~doctor.types.json_schema_type` - Create a new :class:`~doctor.types.JsonSchema` type.
* :func:`~doctor.types.new_type` - Create a new user defined type.
* :func:`~doctor.types.number` - Create a new :class:`~doctor.types.Number` type.
* :func:`~doctor.types.string` - Create a new :class:`~doctor.types.String` type.

Examples
########

.. code-block:: python

    from doctor.errors import TypeSystemError
    from doctor.types import (
        array, boolean, enum, integer, json_schema_type, new_type, number, 
        string, String)

    # Create a new array type of countries
    Countries = array('List of countries', items=string('Country'), min_items=1)

    # Create a new boolean type
    Agreed = boolean('Indicates if user agreed or not')

    # Create a new enum type
    Color = enum('A color', enum=['blue', 'green', 'red'])

    # Create a new integer type
    AnnotationId = integer('Annotation PK', minimum=1)

    # Create a new jsonschema type
    Annotation = json_schema_type(schema_file='/path/to/annotation.yaml')

    # Create a new type based on a String
    class FooString(String):
        must_start_with_foo = True

        def __new__(cls, *args, **kwargs):
            value = super().__new__(cls, *args, **kwargs)
            if cls.must_start_with_foo:
                if not value.lower().startswith('foo'):
                    raise TypeSystemError('Must start with foo', cls=cls)

    MyFooString = new_type(FooString)

    # Create a new number type
    ProductRating = number('Product rating', maximum=10, minimum=1)

    # Create a new string type
    FirstName = string('First name', min_length=2, max_length=255)

    # Create a new type based on FirstName, but is allowed to be None
    NullableFirstName = new_type(FirstName, nullable=True)

.. _types-module-documentation:

Module Documentation
--------------------

.. automodule:: doctor.types
    :members:
    :private-members:
    :show-inheritance:

