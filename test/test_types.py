import os
from datetime import datetime

import pytest

from doctor.errors import TypeSystemError
from doctor.types import (
    array, boolean, enum, integer, jsonschematype, number, string, Object,
    SuperType)


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
        assert s == datetime(2018, 10, 22)
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


class TestBoolean(object):

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


class TestEnum(object):

    def test_enum(self):
        E = enum('choices', enum=['foo', 'bar'])
        # no exception
        E('foo')
        E('bar')
        # not in choices
        with pytest.raises(TypeSystemError, match='Must be a valid choice'):
            E('dog')


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

        expected_msg = "{'cat': 'Additional propertues are not allowed.'}"
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


class TestJsonSchema(object):

    def test_no_definition_key(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = jsonschematype(schema_file=schema_file)
        # no exception
        data = {
            'annotation_id': 1,
            'name': 'test',
        }
        actual = J(data)
        # Verify description pulled from yaml file
        expected = 'An annotation object.'
        assert expected == actual.description

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

    def test_no_definition_key_missing_description(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'no_description.yaml')
        J = jsonschematype(schema_file=schema_file)
        data = {
            'annotation_id': 1,
            'name': 'test',
        }
        with pytest.raises(TypeSystemError,
                           match='Schema is missing a description.'):
            J(data)

    def test_definition_key(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = jsonschematype(
            schema_file=schema_file, definition_key='annotation_id')
        # no exception
        J(1)
        # Not an int
        expected = "'not an int' is not of type 'integer'"
        with pytest.raises(TypeSystemError, match=expected):
            J('not an int')

    def test_definition_key_missing(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = jsonschematype(
            schema_file=schema_file, definition_key='does_not_exist')
        expected = "Definition `does_not_exist` is not defined in the schema."
        with pytest.raises(TypeSystemError, match=expected):
            J(1)

    def test_definition_key_missing_description(self):
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'no_description.yaml')
        J = jsonschematype(
            schema_file=schema_file, definition_key='annotation_id')
        data = 1
        expected = 'Definition `annotation_id` is missing a description.'
        with pytest.raises(TypeSystemError, match=expected):
            J(data)

    def test_definition_key_ref_missing_description(self):
        """
        Tests if the definition is a reference that once resolved does not
        have a description, that we raise a TypeSystemError.
        """
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = jsonschematype(
            schema_file=schema_file, definition_key='dog')
        expected = "Definition `dog` is missing a description."
        with pytest.raises(TypeSystemError, match=expected):
            J('dog')

    def test_definition_key_bad_ref(self):
        """
        Tests when the desire definition is a reference that can't be resolved.
        """
        schema_file = os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml')
        J = jsonschematype(
            schema_file=schema_file, definition_key='bad_ref')
        expected = "Unresolvable JSON pointer: 'definitions/doesnotexist'"
        with pytest.raises(TypeSystemError, match=expected):
            J('dog')
