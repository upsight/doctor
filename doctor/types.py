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

from doctor.errors import SchemaError, SchemaValidationError, TypeSystemError
from doctor.flask import FlaskResourceSchema


class SuperType(object):
    """A super type all custom types must extend from.

    This super type requires all subclasses define a description attribute
    that describes what the type represents.  A `ValueError` will be raised
    if the subclass does not define a `description` attribute.
    """
    #: The description of what the type represents.
    description = None  # type: str

    def __init__(self, *args, **kwargs):
        if self.description is None:
            raise ValueError('Each type must define a description attribute')


class String(SuperType, str):
    native_type = str
    errors = {
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
    }
    max_length = None  # type: int
    min_length = None  # type: int
    pattern = None  # type: str
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

        return value


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
    minimum = None  # type: typing.Union[float, int]
    maximum = None  # type: typing.Union[float, int]
    exclusive_minimum = False
    exclusive_maximum = False
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

        return value


class Number(_NumericType, float):
    native_type = float


class Integer(_NumericType, int):
    native_type = int


class Boolean(SuperType):
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


class Enum(SuperType, str):
    errors = {
        'invalid': 'Must be a valid choice.',
    }
    enum = []  # type: typing.List[str]

    def __new__(cls, value: str):
        if value not in cls.enum:
            raise TypeSystemError(cls=cls, code='invalid')
        return value


class Object(SuperType, dict):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'This field is required.',
        'additional_properties': 'Additional propertues are not allowed.',
    }
    properties = {}  # type: typing.Dict[str, typing.Any]
    required = []  # type: typing.List[str]
    additional_properties = True  # type: bool

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], dict):
            value = args[0]
        else:
            try:
                value = dict(*args, **kwargs)
            except (ValueError, TypeError):
                if (len(args) == 1 and not kwargs and
                        hasattr(args[0], '__dict__')):
                    value = dict(args[0].__dict__)
                else:
                    raise TypeSystemError(
                        cls=self.__class__, code='type') from None

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
                    detail = f'{key} not in {properties}'
                    exc = TypeSystemError(detail, cls=self.__class__,
                                          code='additional_properties')
                    errors[key] = exc.detail

        if errors:
            raise TypeSystemError(errors)


class Array(SuperType, list):
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }
    items = None  # type: typing.Union[type, typing.List[type]]
    additional_items = False  # type: bool
    min_items = 0  # type: typing.Optional[int]
    max_items = None  # type: typing.Optional[int]
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


class JsonSchema(SuperType):
    """Represents a type loaded from a json schema."""

    description = 'json type'
    #: The full path to the schema file.
    schema_file = None  # type: str
    #: The key from the definitions in the file that the type should come from.
    definition_key = None  # type: str

    def __init__(self, data: typing.Any):
        self.schema = FlaskResourceSchema.from_file(self.schema_file)
        request_schema = None

        # Look up the description in the schema.
        if self.definition_key is not None:
            params = [self.definition_key]
            request_schema = self.schema._create_request_schema(params, params)
            try:
                definition = request_schema['definitions'][self.definition_key]
            except KeyError:
                raise TypeSystemError(
                    f'Definition `{self.definition_key}` is not defined in the '
                    'schema.', cls=self.__class__)
            if '$ref' in request_schema['definitions'][self.definition_key]:
                try:
                    self.description = self.schema.resolve(
                        definition['$ref'])['description']
                except KeyError:
                    raise TypeSystemError(
                        f'Definition `{self.definition_key}` is missing a '
                        f'description.', cls=self.__class__)
                except SchemaError as e:
                    raise TypeSystemError(str(e), cls=self.__class__)
            else:
                try:
                    self.description = definition['description']
                except KeyError:
                    raise TypeSystemError(
                        f'Definition `{self.definition_key}` is missing a '
                        f'description.', cls=self.__class__)
            data = {self.definition_key: data}
        else:
            try:
                self.description = self.schema.schema['description']
            except KeyError:
                raise TypeSystemError(
                    'Schema is missing a description.', cls=self.__class__)

        super(JsonSchema, self).__init__()
        # Validate the data against the schema and raise an error if it
        # does not validate.
        validator = self.schema.get_validator(request_schema)
        try:
            self.schema.validate(data, validator)
        except SchemaValidationError as e:
            raise TypeSystemError(e.args[0], cls=self.__class__)


def jsonschematype(**kwargs) -> typing.Type:
    return type('JsonSchema', (JsonSchema,), kwargs)


def string(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('String', (String,), kwargs)


def integer(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('Integer', (Integer,), kwargs)


def number(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('Number', (Number,), kwargs)


def boolean(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('Boolean', (Boolean,), kwargs)


def enum(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('Enum', (Enum,), kwargs)


def array(description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type('Array', (Array,), kwargs)


def newtype(cls, description, **kwargs) -> typing.Type:
    kwargs['description'] = description
    return type(cls.__name__, (cls,), kwargs)
