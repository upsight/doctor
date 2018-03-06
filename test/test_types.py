import os
from datetime import date, datetime

import pytest

from doctor.errors import TypeSystemError
from doctor.resource import ResourceSchema
from doctor.types import (
    array, boolean, enum, integer, json_schema_type, number, string, Object,
    MissingDescriptionError, SuperType)


class TestSuperType(object):

    def test_init_no_description(self):
        class MyType(SuperType):
            pass

        with pytest.raises(ValueError, match='define a description attribute'):
            MyType()

    def test_init_with_description_defined(self):
        class MyType(SuperType):
            description = 'My Type'

        MyType()


class TestString(object):

    def test_type(self):
        S = string('string')
        assert type(S('string')) is str

    def test_trim_whitespace(self):
        S = string('a string', trim_whitespace=True)
        actual = S(' foo ')
        assert 'foo' == actual

    def test_min_length(self):
        S = string('a string', min_length=2)
        # No exception
        S('foo')
        # String too short
        with pytest.raises(TypeSystemError,
                           match='Must have at least 2 characters'):
            S('f')
        # Empty string when min_length is 1
        S = string('empty', min_length=1)
        with pytest.raises(TypeSystemError, match='Must not be blank.'):
            S('')

    def test_max_length(self):
        S = string('a string', max_length=2)
        # No exception
        S('12')
        # String too long
        with pytest.raises(TypeSystemError,
                           match='Must have no more than 2 characters'):
            S('123')

    def test_pattern(self):
        S = string('a regex', pattern=r'^foo*')
        # No exception
        S('foo bar')
        # Does not begin with `foo`
        with pytest.raises(TypeSystemError):
            S('bar')

    def test_format_date(self):
        S = string('date', format='date')
        # No exception
        s = S('2018-10-22')
        assert s == date(2018, 10, 22)
        # Invalid date
        expected_msg = "time data 'foo' does not match format '%Y-%m-%d'"
        with pytest.raises(TypeSystemError, match=expected_msg):
            S('foo')

    def test_format_date_time(self):
        S = string('date-time', format='date-time')
        # No exception
        s = S('2018-10-22T11:12:00')
        assert s == datetime(2018, 10, 22, 11, 12, 0)

        # Invalid datetime
        expected_msg = ("ISO 8601 time designator 'T' missing. Unable to parse "
                        "datetime string 'foo'")
        with pytest.raises(TypeSystemError, match=expected_msg):
            S('foo')

    def test_format_email(self):
        S = string('email', format='email')
        # No exception
        S('user@domain.net')
        # Invalid email
        with pytest.raises(TypeSystemError, match='Not a valid email address.'):
            S('foo.net')

    def test_format_time(self):
        S = string('time', format='time')
        # no exception
        s = S('13:10:00')
        assert 13 == s.hour
        assert 10 == s.minute
        assert 0 == s.second

        # invalid
        expected_msg = "time data 'foo' does not match format '%H:%M:%S"
        with pytest.raises(TypeSystemError, match=expected_msg):
            S('foo')

    def test_format_uri(self):
        S = string('uri', format='uri')
        # no exception
        S('https://doctor.com')
        # Invalid uri
        expected_msg = "'foo' is not a valid 'URI'."
        with pytest.raises(TypeSystemError, match=expected_msg):
            S('foo')

    def test_get_example(self):
        S = string('A string.', example='Foo')
        assert 'Foo' == S.get_example()

        # Default example
        S = string('A string.')
        assert 'string' == S.get_example()


class TestNumericType(object):

    def test_minimum(self):
        N = number('float', minimum=3.22)
        # No exception
        N(3.23)
        # Number too small
        with pytest.raises(TypeSystemError,
                           match='Must be greater than or equal to 3.22'):
            N(3.21)

    def test_maximum(self):
        N = number('int', maximum=30)
        # No exception
        N(30)
        # Number > max
        with pytest.raises(TypeSystemError,
                           match='Must be less than or equal to 30'):
            N(31)

    def test_exclusive_mimimum(self):
        N = integer('int', minimum=2, exclusive_minimum=True)
        # No exception
        N(3)
        # number is equal to minimum
        with pytest.raises(TypeSystemError,
                           match='Must be greater than 2.'):
            N(2)

    def test_exclusive_maximum(self):
        N = number('float', maximum=3.3, exclusive_maximum=True)
        # No exception
        N(3.2)
        # number is equal to maximum
        with pytest.raises(TypeSystemError, match='Must be less than 3.3.'):
            N(3.3)

    def test_multiple_of(self):
        N = integer('int', multiple_of=2)
        # No exception
        N(4)
        # Not multiple
        with pytest.raises(TypeSystemError, match='Must be a multiple of 2.'):
            N(5)

        # Also test with float
        N = number('float', multiple_of=1.1)
        # No exception
        N(2.2)
        # Not multiple
        with pytest.raises(TypeSystemError, match='Must be a multiple of 1.1.'):
            N(5)


class TestNumber(object):

    def test_type(self):
        N = number('float')
        assert type(N(3.14)) is float

    def test_get_example(self):
        N = number('A float', example=1.12)
        assert 1.12 == N.get_example()

        # Default example
        N = number('Pi')
        assert 3.14 == N.get_example()


class TestInteger(object):

    def test_type(self):
        I = integer('int')  # noqa
        assert type(I(1)) is int

    def test_get_example(self):
        I = integer('An int', example=1022)  # noqa
        assert 1022 == I.get_example()

        # Default example
        I = integer('An ID')  # noqa
        assert 1 == I.get_example()


class TestBoolean(object):

    def test_type(self):
        B = boolean('bool')
        assert type(B('true')) is bool

    def test_boolean_type(self):
        B = boolean('A bool')
        tests = (
            # (input, expected)
            ('true', True),
            ('false', False),
            ('True', True),
            ('False', False),
            ('on', True),
            ('off', False),
            ('1', True),
            ('0', False),
            ('', False),
        )
        for val, expected in tests:
            assert expected == B(val)

    def test_non_boolean(self):
        B = boolean('bool')
        with pytest.raises(TypeSystemError, match='Must be a valid boolean.'):
            B('dog')

    def test_get_example(self):
        B = boolean('A bool', example=False)
        assert B.get_example() is False

        # Default example
        B = boolean('A bool')
        assert B.get_example() is True


class TestEnum(object):

    def test_type(self):
        E = enum('choices', enum=['foo'])
        assert type(E('foo')) is str

    def test_enum(self):
        E = enum('choices', enum=['foo', 'bar'])
        # no exception
        E('foo')
        E('bar')
        # not in choices
        with pytest.raises(TypeSystemError, match='Must be a valid choice'):
            E('dog')

    def test_get_example(self):
        E = enum('choices', enum=['foo', 'bar'], example='bar')
        assert 'bar' == E.get_example()

        # Default example (1st item in enum)
        E = enum('choices', enum=['foo', 'bar'])
        assert 'foo' == E.get_example()


class FooObject(Object):
    additional_properties = True
    description = 'A Foo'
    properties = {'foo': string('foo property', min_length=2)}


class NoAddtPropsObject(FooObject):
    additional_properties = False


class RequiredPropsObject(Object):
    description = 'required'
    properties = {
        'foo': string('foo property', min_length=2),
        'bar': integer('an int'),
    }
    required = ['bar']


class TestObject(object):

    def test_valid_object(self):
        expected = {'foo': 'bar'}
        actual = FooObject(expected)
        assert expected == actual

    def test_missing_description(self):
        class MyObject(Object):
            pass

        expected_msg = "MyObject'> did not define a description attribute"
        with pytest.raises(MissingDescriptionError, match=expected_msg):
            MyObject({'foo': 'bar'})

    def test_invalid_object(self):
        with pytest.raises(TypeSystemError, match='Must be an object.'):
            FooObject('12')

    def test_invalid_property(self):
        with pytest.raises(TypeSystemError,
                           match="{'foo': 'Must have at least 2 characters.'}"):
            FooObject({'foo': 'f'})

    def test_additional_properties(self):
        expected = {
            'foo': 'bar',
            'cat': 12  # Extra property not defined for FooObject
        }
        actual = FooObject(expected)
        assert expected == actual

        expected_msg = "{'cat': 'Additional properties are not allowed.'}"
        with pytest.raises(TypeSystemError, match=expected_msg):
            NoAddtPropsObject(expected)

    def test_required_properties(self):
        expected = {'bar': 1}
        actual = RequiredPropsObject(expected)
        assert expected == actual

        # omit required property 'bar'
        expected = {'foo': 'bar'}
        with pytest.raises(TypeSystemError,
                           match="{'bar': 'This field is required.'}"):
            RequiredPropsObject(expected)

    def test_get_example(self):
        # default example is generated from example values of it's properties.
        assert {'foo': 'string', 'bar': 1} == RequiredPropsObject.get_example()
        # with a defined example
        setattr(RequiredPropsObject, 'example', {'foo': 'foo', 'bar': 33})
        assert {'foo': 'foo', 'bar': 33} == RequiredPropsObject.get_example()


class TestArray(object):

    def test_items(self):
        A = array('array', items=string('string', max_length=1))
        # no exception
        A(['a', 'b'])
        # Invalid type of items
        with pytest.raises(TypeSystemError,
                           match="{0: 'Must have no more than 1 characters.'}"):
            A(['aa', 'b'])

    def test_items_multiple_types(self):
        A = array('a', items=[
            string('string', max_length=1), integer('int', maximum=1234)])
        # no exception
        A(['b', 1234])
        # Invalid type
        with pytest.raises(TypeSystemError,
                           match="{1: 'Must be less than or equal to 1234.'}"):
            A(['b', 1235])

    def test_additional_items(self):
        A = array('a', items=[
            string('string', max_length=1), integer('int', maximum=1234)],
            additional_items=True)
        # no exception
        A(['a', 2, 3, 4, True])

        A = array('a', items=[
            string('string', max_length=1), integer('int', maximum=1234)],
            additional_items=False)
        with pytest.raises(TypeSystemError, match='Too many items.'):
            A(['a', 2, 3, 4, True])

    def test_min_items(self):
        A = array('a', min_items=3)
        # no exception
        A([1, 2, 3])
        # Too few items
        with pytest.raises(TypeSystemError, match='Not enough items'):
            A([1])

    def test_max_items(self):
        A = array('a', max_items=3)
        # no exception
        A([1, 2, 3])
        # Too many items
        with pytest.raises(TypeSystemError, match='Too many items'):
            A([1, 2, 3, 4])

    def test_unique_items(self):
        A = array('not unique', unique_items=False)
        # no exception
        A([1, 1, 1, 2])

        A = array('unique', unique_items=True)
        with pytest.raises(TypeSystemError, match='This item is not unique.'):
            A([1, 1, 1, 2])

    def test_get_example(self):
        A = array('No example of items')
        assert [1] == A.get_example()

        A = array('Defined example', example=['a', 'b'])
        assert ['a', 'b'] == A.get_example()

        A = array('No example, defined items', items=string('letter'))
        assert ['string'] == A.get_example()


class TestJsonSchema(object):

    def test_no_definition_key(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = json_schema_type(schema_file=schema_file)

        # Verify description and example were set as attributes based
        # on values from the loaded json schema.
        assert 'An annotation object.' == J.description
        assert {
            'annotation_id': 1,
            'auth': 'token',
            'more_id': 1,
            'name': 'Annotation',
            'url': 'https://upsight.com',
        } == J.example
        assert isinstance(J.schema, ResourceSchema)

        # no exception
        data = {
            'annotation_id': 1,
            'name': 'test',
        }
        actual = J(data)
        assert data == actual
        # Verify description pulled from yaml file
        expected = 'An annotation object.'
        assert expected == J.description

        # missing required field
        data = {'name': 'test'}
        with pytest.raises(TypeSystemError,
                           match="'annotation_id' is a required property"):
            J(data)

        # annotation_id is not an int.
        data = {
            'auth': 'authtoken',  # verifying we can load from external files
            'annotation_id': 'foobar',
            'name': 'test',
        }
        with pytest.raises(TypeSystemError,
                           match="'foobar' is not of type 'integer'"):
            J(data)

    def test_no_definition_key_no_example(self):
        """
        This tests that if we don't pass a definition_key and the schema
        doesn't define an example at the root that it will attempt to
        resolve it from the properties if the root is an object.
        """
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation_no_example.yaml')
        J = json_schema_type(schema_file=schema_file)

        # Verify description and example were set as attributes based
        # on values from the loaded json schema.
        assert 'An annotation object.' == J.description
        assert {
            'annotation_id': 1,
            'auth': 'eb25f25becca416092752b0f457f1271',
            'more_id': 1,
            'name': 'Annotation',
            'url': 'https://upsight.com',
        } == J.example
        assert isinstance(J.schema, ResourceSchema)

    def test_no_definition_key_missing_description(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'no_description.yaml')
        with pytest.raises(TypeSystemError,
                           match='Schema is missing a description.'):
            json_schema_type(schema_file=schema_file)

    def test_definition_key(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = json_schema_type(
            schema_file=schema_file, definition_key='annotation_id')
        # Verify description and example were set as attributes based
        # on values from the loaded json schema.
        assert 'Auto-increment ID.' == J.description
        assert 1 == J.example
        assert isinstance(J.schema, ResourceSchema)

        # no exception
        J(1)
        # Not an int
        expected = "'not an int' is not of type 'integer'"
        with pytest.raises(TypeSystemError, match=expected):
            J('not an int')

    def test_definition_key_missing(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        expected = "Definition `does_not_exist` is not defined in the schema."
        with pytest.raises(TypeSystemError, match=expected):
            json_schema_type(
                schema_file=schema_file, definition_key='does_not_exist')

    def test_definition_key_missing_description(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'no_description.yaml')
        expected = 'Definition `annotation_id` is missing a description.'
        with pytest.raises(TypeSystemError, match=expected):
            json_schema_type(
                schema_file=schema_file, definition_key='annotation_id')

    def test_definition_key_ref_missing_description(self):
        """
        Tests if the definition is a reference that once resolved does not
        have a description, that we raise a TypeSystemError.
        """
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        expected = "Definition `dog` is missing a description."
        with pytest.raises(TypeSystemError, match=expected):
            json_schema_type(
                schema_file=schema_file, definition_key='dog')

    def test_definition_key_bad_ref(self):
        """
        Tests when the desire definition is a reference that can't be resolved.
        """
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        expected = "Unresolvable JSON pointer: 'definitions/doesnotexist'"
        with pytest.raises(TypeSystemError, match=expected):
            json_schema_type(
                schema_file=schema_file, definition_key='bad_ref')
