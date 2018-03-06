"""
Copyright © 2017, Encode OSS Ltd. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the name of the copyright holder nor the names of its contributors may
be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This file is a modified version of the typingsystem.py module in apistar.
https://github.com/encode/apistar/blob/973c6485d8297c1bcef35a42221ac5107dce25d5/apistar/typesystem.py
"""
import math
import re
import typing
from datetime import datetime

import isodate
import rfc3987

from doctor.errors import SchemaError, SchemaValidationError, TypeSystemError
from doctor.parsers import parse_value


class MissingDescriptionError(ValueError):
    """An exception raised when a type is missing a description."""
    pass


class SuperType(object):
    """A super type all custom types must extend from.

    This super type requires all subclasses define a description attribute
    that describes what the type represents.  A `ValueError` will be raised
    if the subclass does not define a `description` attribute.
    """
    #: The description of what the type represents.
    description = None  # type: str

    #: An example value for the type.
    example = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.description is None:
            cls = self.__class__
            raise MissingDescriptionError(
                '{} did not define a description attribute'.format(cls))


class String(SuperType, str):
    """Represents a `str` type."""
    native_type = str
    errors = {
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
    }
    #: Will check format of the string for `date`, `date-time`, `email`,
    #: `time` and `uri`.
    format = None
    #: The maximum length of the string.
    max_length = None  # type: int
    #: The minimum length of the string.
    min_length = None  # type: int
    #: A regex pattern that the string should match.
    pattern = None  # type: str
    #: Whether to trim whitespace on a string.  Defaults to `True`.
    trim_whitespace = True

    def __new__(cls, *args, **kwargs):
        value = super().__new__(cls, *args, **kwargs)

        if cls.trim_whitespace:
            value = value.strip()

        if cls.min_length is not None:
            if len(value) < cls.min_length:
                if cls.min_length == 1:
                    raise TypeSystemError(cls=cls, code='blank')
                else:
                    raise TypeSystemError(cls=cls, code='min_length')

        if cls.max_length is not None:
            if len(value) > cls.max_length:
                raise TypeSystemError(cls=cls, code='max_length')

        if cls.pattern is not None:
            if not re.search(cls.pattern, value):
                raise TypeSystemError(cls=cls, code='pattern')

        # Validate format, if specified
        if cls.format == 'date':
            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError as e:
                raise TypeSystemError(str(e), cls=cls)
        elif cls.format == 'date-time':
            try:
                value = isodate.parse_datetime(value)
            except (ValueError, isodate.ISO8601Error) as e:
                raise TypeSystemError(str(e), cls=cls)
        elif cls.format == 'email':
            if '@' not in value:
                raise TypeSystemError('Not a valid email address.', cls=cls)
        elif cls.format == 'time':
            try:
                value = datetime.strptime(value, "%H:%M:%S")
            except ValueError as e:
                raise TypeSystemError(str(e), cls=cls)
        elif cls.format == 'uri':
            try:
                rfc3987.parse(value, rule='URI')
            except ValueError as e:
                raise TypeSystemError(str(e), cls=cls)

        # Coerce value to the native str type.  We only do this if the value
        # is an instance of the class.  It could be a datetime instance or
        # a str already if `trim_whitespace` is True.
        if isinstance(value, cls):
            value = cls.native_type(value)
        return value

    @classmethod
    def get_example(cls) -> str:
        """Returns an example value for the String type."""
        if cls.example is not None:
            return cls.example
        return 'string'


class _NumericType(SuperType):
    """
    Base class for both `Number` and `Integer`.
    """
    native_type = None  # type: type
    errors = {
        'type': 'Must be a valid number.',
        'finite': 'Must be a finite number.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }
    #: The minimum value allowed.
    minimum = None  # type: typing.Union[float, int]
    #: The maximum value allowed.
    maximum = None  # type: typing.Union[float, int]
    #: The minimum value should be treated as exclusive or not.
    exclusive_minimum = False
    #: The maximum value should be treated as exclusive or not.
    exclusive_maximum = False
    #: The value is required to be a multiple of this value.
    multiple_of = None  # type: typing.Union[float, int]

    def __new__(cls, *args, **kwargs):
        try:
            value = cls.native_type.__new__(cls, *args, **kwargs)
        except (TypeError, ValueError):
            raise TypeSystemError(cls=cls, code='type') from None

        if not math.isfinite(value):
            raise TypeSystemError(cls=cls, code='finite')

        if cls.minimum is not None:
            if cls.exclusive_minimum:
                if value <= cls.minimum:
                    raise TypeSystemError(cls=cls, code='exclusive_minimum')
            else:
                if value < cls.minimum:
                    raise TypeSystemError(cls=cls, code='minimum')

        if cls.maximum is not None:
            if cls.exclusive_maximum:
                if value >= cls.maximum:
                    raise TypeSystemError(cls=cls, code='exclusive_maximum')
            else:
                if value > cls.maximum:
                    raise TypeSystemError(cls=cls, code='maximum')

        if cls.multiple_of is not None:
            if isinstance(cls.multiple_of, float):
                failed = not (value * (1 / cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                raise TypeSystemError(cls=cls, code='multiple_of')

        # Coerce value to the native type.  We only do this if the value
        # is an instance of the class.
        if isinstance(value, cls):
            value = cls.native_type(value)
        return value


class Number(_NumericType, float):
    """Represents a `float` type."""
    native_type = float

    @classmethod
    def get_example(cls) -> float:
        """Returns an example value for the Number type."""
        if cls.example is not None:
            return cls.example
        return 3.14


class Integer(_NumericType, int):
    """Represents an `int` type."""
    native_type = int

    @classmethod
    def get_example(cls) -> int:
        """Returns an example value for the Integer type."""
        if cls.example is not None:
            return cls.example
        return 1


class Boolean(SuperType):
    """Represents a `bool` type."""
    native_type = bool
    errors = {
        'type': 'Must be a valid boolean.'
    }

    def __new__(cls, *args, **kwargs) -> bool:
        if args and isinstance(args[0], str):
            try:
                return {
                    'true': True,
                    'false': False,
                    'on': True,
                    'off': False,
                    '1': True,
                    '0': False,
                    '': False
                }[args[0].lower()]
            except KeyError:
                raise TypeSystemError(cls=cls, code='type') from None
        return bool(*args, **kwargs)

    @classmethod
    def get_example(cls) -> bool:
        """Returns an example value for the Boolean type."""
        if cls.example is not None:
            return cls.example
        return True


class Enum(SuperType, str):
    """
    Represents a `str` type that must be one of any defined allowed values.
    """
    native_type = str
    errors = {
        'invalid': 'Must be a valid choice.',
    }
    #: A list of valid values.
    enum = []  # type: typing.List[str]

    def __new__(cls, value: str):
        if value not in cls.enum:
            raise TypeSystemError(cls=cls, code='invalid')
        return value

    @classmethod
    def get_example(cls) -> str:
        """Returns an example value for the Enum type."""
        if cls.example is not None:
            return cls.example
        return cls.enum[0]


class Object(SuperType, dict):
    """Represents a `dict` type."""
    native_type = dict
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'This field is required.',
        'additional_properties': 'Additional properties are not allowed.',
    }
    #: A mapping of property name to expected type.
    properties = {}  # type: typing.Dict[str, typing.Any]
    #: A list of required properties.
    required = []  # type: typing.List[str]
    #: If True additional properties will be allowed, otherwise they will not.
    additional_properties = True  # type: bool

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except MissingDescriptionError:
            raise
        except (ValueError, TypeError):
            if (len(args) == 1 and not kwargs and
                    hasattr(args[0], '__dict__')):
                value = dict(args[0].__dict__)
            else:
                raise TypeSystemError(
                    cls=self.__class__, code='type') from None
        value = self

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            raise TypeSystemError(cls=self.__class__, code='invalid_key')

        # Properties
        for key, child_schema in self.properties.items():
            try:
                item = value[key]
            except KeyError:
                if hasattr(child_schema, 'default'):
                    # If a key is missing but has a default, then use that.
                    self[key] = child_schema.default
                elif key in self.required:
                    exc = TypeSystemError(cls=self.__class__, code='required')
                    errors[key] = exc.detail
            else:
                # Coerce value into the given schema type if needed.
                if isinstance(item, child_schema):
                    self[key] = item
                else:
                    try:
                        self[key] = child_schema(item)
                    except TypeSystemError as exc:
                        errors[key] = exc.detail

        # If additional properties are allowed set any other key/value(s) not
        # in the defined properties.
        if self.additional_properties:
            for key, value in value.items():
                if key not in self:
                    self[key] = value

        # Raise an exception if additional properties are defined and
        # not allowed.
        if not self.additional_properties:
            properties = list(self.properties.keys())
            for key in value.keys():
                if key not in properties:
                    detail = '{key} not in {properties}'.format(
                        key=key, properties=properties)
                    exc = TypeSystemError(detail, cls=self.__class__,
                                          code='additional_properties')
                    errors[key] = exc.detail

        if errors:
            raise TypeSystemError(errors)

    @classmethod
    def get_example(cls) -> dict:
        """Returns an example value for the Dict type.

        If an example isn't a defined attribute on the class we return
        a dict of example values based on each property's annotation.
        """
        if cls.example is not None:
            return cls.example
        return {k: v.get_example() for k, v in cls.properties.items()}


class Array(SuperType, list):
    """Represents a `list` type."""
    native_type = list
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }
    #: The type each item should be, or a list of types where the position
    #: of the type in the list represents the type at that position in the
    #: array the item should be.
    items = None  # type: typing.Union[type, typing.List[type]]
    #: If `items` is a list and this is `True` then additional items whose
    #: types aren't defined are allowed in the list.
    additional_items = False  # type: bool
    #: The minimum number of items allowed in the list.
    min_items = 0  # type: typing.Optional[int]
    #: The maxiimum number of items allowed in the list.
    max_items = None  # type: typing.Optional[int]
    #: If `True` items in the array should be unique from one another.
    unique_items = False  # type: bool

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], (str, bytes)):
            raise TypeSystemError(cls=self.__class__, code='type')

        try:
            value = list(*args, **kwargs)
        except TypeError:
            raise TypeSystemError(cls=self.__class__, code='type') from None

        if isinstance(self.items, list) and len(self.items) > 1:
            if len(value) < len(self.items):
                raise TypeSystemError(cls=self.__class__, code='min_items')
            elif len(value) > len(self.items) and not self.additional_items:
                raise TypeSystemError(cls=self.__class__, code='max_items')

        if len(value) < self.min_items:
            raise TypeSystemError(cls=self.__class__, code='min_items')
        elif self.max_items is not None and len(value) > self.max_items:
            raise TypeSystemError(cls=self.__class__, code='max_items')

        # Ensure all items are of the right type.
        errors = {}
        if self.unique_items:
            seen_items = set()

        for pos, item in enumerate(value):
            try:
                if isinstance(self.items, list):
                    if pos < len(self.items):
                        item = self.items[pos](item)
                elif self.items is not None:
                    item = self.items(item)

                if self.unique_items:
                    if item in seen_items:
                        raise TypeSystemError(
                            cls=self.__class__, code='unique_items')
                    else:
                        seen_items.add(item)

                self.append(item)
            except TypeSystemError as exc:
                errors[pos] = exc.detail

        if errors:
            raise TypeSystemError(errors)

    @classmethod
    def get_example(cls) -> list:
        """Returns an example value for the Array type.

        If an example isn't a defined attribute on the class we return
        a list of 1 item containing the example value of the `items` attribute.
        If `items` is None we simply return a `[1]`.
        """
        if cls.example is not None:
            return cls.example
        if cls.items is not None:
            return [cls.items.get_example()]
        return [1]


class JsonSchema(SuperType):
    """Represents a type loaded from a json schema.

    NOTE: This class should not be used directly.  Instead use
    :func:`~doctor.types.json_schema_type` to create a new class based on
    this one.
    """
    json_type = None
    native_type = None
    #: The loaded ResourceSchema
    schema = None  # type: doctor.resource.ResourceSchema
    #: The full path to the schema file.
    schema_file = None  # type: str
    #: The key from the definitions in the schema file that the type should
    #: come from.
    definition_key = None  # type: str

    def __new__(cls, value):
        # Attempt to parse the value if it came from a query string
        try:
            _, value = parse_value(value, [cls.json_type])
        except ValueError:
            pass
        request_schema = None
        if cls.definition_key is not None:
            params = [cls.definition_key]
            request_schema = cls.schema._create_request_schema(params, params)
            data = {cls.definition_key: value}
        else:
            data = value

        super().__new__(cls)
        # Validate the data against the schema and raise an error if it
        # does not validate.
        validator = cls.schema.get_validator(request_schema)
        try:
            cls.schema.validate(data, validator)
        except SchemaValidationError as e:
            raise TypeSystemError(e.args[0], cls=cls)

        return value

    @classmethod
    def get_example(cls) -> typing.Any:
        """Returns an example value for the JsonSchema type."""
        return cls.example


#: A mapping of json types to native python types.
JSON_TYPES_TO_NATIVE = {
    'array': list,
    'boolean': bool,
    'integer': int,
    'object': dict,
    'number': float,
    'string': str,
}


def get_value_from_schema(schema, definition: dict, key: str,
                          definition_key: str, resolve: bool=False):
    """Gets a value from a schema and definition.

    :param ResourceSchema schema: The resource schema.
    :param dict definition: The definition dict from the schema.
    :param str key: The key to use to get the value from the schema.
    :param str definition_key: The name of the definition.
    :param bool resolve: If True we will attempt to resolve the definition
        from the schema.
    :returns: The value.
    :raises TypeSystemError: If the key can't be found in the schema/definition
        or we can't resolve the definition.
    """
    try:
        if resolve:
            value = schema.resolve(definition['$ref'])[key]
        else:
            value = definition[key]
    except KeyError:
        raise TypeSystemError(
            'Definition `{}` is missing a {}.'.format(
                definition_key, key))
    except SchemaError as e:
        raise TypeSystemError(str(e))
    return value


def json_schema_type(schema_file: str, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.JsonSchema` type.

    This function will automatically load the schema and set it as an attribute
    of the class along with the description and example.

    :param schema_file: The full path to the json schema file to load.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.JsonSchema`
    """
    # Importing here to avoid circular dependencies
    from doctor.resource import ResourceSchema
    schema = ResourceSchema.from_file(schema_file)
    kwargs['schema'] = schema

    # Look up the description, example and type in the schema.
    definition_key = kwargs.get('definition_key')
    if definition_key:
        params = [definition_key]
        request_schema = schema._create_request_schema(params, params)
        try:
            definition = request_schema['definitions'][definition_key]
        except KeyError:
            raise TypeSystemError(
                'Definition `{}` is not defined in the schema.'.format(
                    definition_key))
        if '$ref' in request_schema['definitions'][definition_key]:
            description = get_value_from_schema(
                schema, definition, 'description', definition_key, resolve=True)
            example = get_value_from_schema(
                schema, definition, 'example', definition_key, resolve=True)
            native_type = get_value_from_schema(
                schema, definition, 'type', definition_key, resolve=True)
        else:
            description = get_value_from_schema(
                schema, definition, 'description', definition_key)
            example = get_value_from_schema(
                schema, definition, 'example', definition_key)
            native_type = get_value_from_schema(
                schema, definition, 'type', definition_key)
        kwargs['description'] = description
        kwargs['example'] = example
        kwargs['json_type'] = native_type
        kwargs['native_type'] = JSON_TYPES_TO_NATIVE[native_type]
    else:
        try:
            kwargs['description'] = schema.schema['description']
        except KeyError:
            raise TypeSystemError('Schema is missing a description.')
        try:
            kwargs['json_type'] = schema.schema['type']
            kwargs['native_type'] = JSON_TYPES_TO_NATIVE[schema.schema['type']]
        except KeyError:
            raise TypeSystemError('Schema is missing a type.')
        try:
            kwargs['example'] = schema.schema['example']
        except KeyError:
            # Attempt to load from properties, if defined.
            if schema.schema.get('properties'):
                example = {}
                for prop, definition in schema.schema['properties'].items():
                    example[prop] = schema.resolve(
                        definition['$ref'])['example']
                kwargs['example'] = example
            else:
                raise TypeSystemError('Schema is missing an example.')

    return type('JsonSchema', (JsonSchema,), kwargs)


def string(description: str, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.String` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.String`
    """
    kwargs['description'] = description
    return type('String', (String,), kwargs)


def integer(description, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.Integer` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.Integer`
    """
    kwargs['description'] = description
    return type('Integer', (Integer,), kwargs)


def number(description, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.Number` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.Number`
    """
    kwargs['description'] = description
    return type('Number', (Number,), kwargs)


def boolean(description, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.Boolean` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.Boolean`
    """
    kwargs['description'] = description
    return type('Boolean', (Boolean,), kwargs)


def enum(description, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.Enum` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.Enum`
    """
    kwargs['description'] = description
    return type('Enum', (Enum,), kwargs)


def array(description, **kwargs) -> typing.Type:
    """Create a :class:`~doctor.types.Array` type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        :class:`~doctor.types.Array`
    """
    kwargs['description'] = description
    return type('Array', (Array,), kwargs)


def new_type(cls, description, **kwargs) -> typing.Type:
    """Create a user defined type.

    :param description: A description of the type.
    :param kwargs: Can include any attribute defined in
        the provided user defined type.
    """
    kwargs['description'] = description
    return type(cls.__name__, (cls,), kwargs)
