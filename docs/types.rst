Types
=====

Doctor :ref:`types<types-module-documentation>` validate request parameters
passed to logic functions.  Every request parameter that gets passed to your
logic function should define a type from one of those below.  See ... for 
functions that allow you to create types easily on the fly.

String
------

A :class:`~doctor.types.String` type represents a `str` and allows you to
define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.String.format` - An identifier indicating a complex 
  datatype with a string representation. For example `date`, to represent an 
  ISO 8601 formatted date string.  The following formats are supported:

    * date
    * date-time
    * email
    * time
    * uri

* :attr:`~doctor.types.String.max_length` - The maximum length of the string.
* :attr:`~doctor.types.String.min_length` - The minimum length of the string.
* :attr:`~doctor.types.String.pattern` - A regex pattern the string should
  match anywhere whitin it.  Uses `re.search`.
* :attr:`~doctor.types.String.trim_whitespace` - If `True` the string will be
  trimmed of whitespace.

Example
#######

.. code-block:: python

    from dotor.types import String

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

Example
#######

.. code-block:: python

    from dotor.types import Number

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

Example
#######

.. code-block:: python

    from dotor.types import Integer

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

Example
#######

.. code-block:: python

    from dotor.types import Boolean

    class Accept(Boolean):
        description = 'Inciates if the user accepted the agreement or not.'

Enum
----

An :class:`~doctor.types.Enum` type represents a `str` that should be one of
any defined values and allows you to define several attributes for validation.

Attributes
##########

* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.Enum.enum` - A list of `str` containing valid values.

Example
#######

.. code-block:: python

    from dotor.types import Enum

    class Color(Enum):
        description = 'A color.'
        enum = ['blue', 'green', 'purple', 'yellow']


Object
------

An :class:`~doctor.types.Object` type represents a `dict` and allows you to
define properties and required properties.

Attributes
##########

* :attr:`~doctor.types.Object.additional_properties` - If `True` additional
  properties will be allowed in the object that are not defined in
  :attr:`~doctor.types.Object.properties`.
* :attr:`~doctor.types.SuperType.description` - A human readable description
  of what the type represents.  This will be used when generating documentation.
* :attr:`~doctor.types.Object.properties` - A dict containing a mapping of
  property name to expected type.
* :attr:`~doctor.types.Object.required` - A list of required properties.

Example
#######

.. code-block:: python

    from dotor.types import Object, boolean, string

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
* :attr:`~doctor.types.Array.items` - The type each item should be, or a list of
  types where the position of the type in the list represents the type at that
  position in the array the item should be.
* :attr:`~doctor.types.Array.min_items` - The minimum number of items allowed
  in the list.
* :attr:`~doctor.types.Array.max_items` - The maximum number of items allowed
  in the list.
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

.. _types-module-documentation:

Module Documentation
--------------------

.. automodule:: doctor.types
    :members:
    :private-members:
    :show-inheritance:

