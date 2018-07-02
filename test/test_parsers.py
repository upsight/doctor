# encoding: utf-8

import inspect

import pytest

from doctor.errors import ParseError, TypeSystemError
from doctor.parsers import (
    map_param_names, parse_form_and_query_params, parse_json, parse_value)

from .base import TestCase
from .types import Age, Auth, Color, IsDeleted, Latitude, Longitude, OptIn


def logic(age: Age, color: Color, is_deleted: IsDeleted=False):
    return '{} {} {}'.format(age, color, is_deleted)


class TestParsers(TestCase):

    def test_parse_json(self):
        assert {'foo': 1} == parse_json('{"foo": 1}')
        message = 'Error parsing JSON: \'bad json\' error: Expecting value'
        with pytest.raises(ParseError, match=message):
            parse_json('bad json')

    def test_parse_value(self):
        """These cases should return a value when parsing."""
        tests = [
            ('', ['null'], None),
            ('true', ['boolean'], True),
            ('True', ['boolean'], True),
            ('TRUE', ['boolean'], True),
            ('false', ['boolean'], False),
            ('False', ['boolean'], False),
            ('FALSE', ['boolean'], False),
            ('0', ['integer'], 0),
            ('1', ['integer'], 1),
            ('-1', ['integer'], -1),
            ('0', ['number'], 0.0),
            ('0.5', ['number'], 0.5),
            ('[]', ['array'], []),
            ('[0]', ['array'], [0]),
            ('["0", 0]', ['array'], ['0', 0]),
            ('{}', ['object'], {}),
            ('{"a": 1}', ['object'], {'a': 1}),
            ('foo', ['string'], 'foo'),
            ('"foo"', ['string'], '"foo"'),
            (u'foø', ['string'], u'foø'),

            # ambiguous test cases
            ('', ['string', 'null'], None),
            ('', ['boolean', 'string'], ''),
            ('', ['boolean', 'string', 'null'], None),
            ('true', ['string', 'boolean'], True),
            ('false', ['string', 'boolean'], False),
            ('0', ['string', 'float', 'integer'], 0),
            ('1', ['string', 'float', 'integer'], 1),
            ('[]', ['string', 'object', 'array'], []),
            ('  []', ['string', 'object', 'array'], []),
            ('{}', ['string', 'array', 'object'], {}),
            ('    {}', ['string', 'array', 'object'], {}),
        ]
        for value, allowed_types, expected_value in tests:
            expected = (allowed_types[-1], expected_value)
            assert parse_value(value, allowed_types) == expected

    def test_parse_value_errors(self):
        """These cases should raise an error when parsing."""
        tests = {'array': ['{}', '['],
                 'boolean': ['0', '1'],
                 'float': ['bad'],
                 'integer': ['bad', '0.1'],
                 'object': ['[]', '{']}
        for allowed_type, bad_values in list(tests.items()):
            for bad_value in bad_values:
                with pytest.raises(ParseError):
                    parse_value(bad_value, [allowed_type])

    def test_parse_value_error_not_string(self):
        """Should raise an error if the value isn't a string."""
        with pytest.raises(
                ValueError, match=r"value for 'foo' must be a string"):
            parse_value(1337, [], 'foo')

    def test_parse_form_and_query_params_no_errors(self):
        sig = inspect.signature(logic)
        query_params = {
            'age': '22',
            'color': 'blue',
            'is_deleted': 'true',
        }
        actual = parse_form_and_query_params(query_params, sig.parameters)
        assert {
            'age': 22,
            'color': 'blue',
            'is_deleted': True,
        } == actual

    def test_parse_form_and_query_params_with_errors(self):
        sig = inspect.signature(logic)
        query_params = {
            'age': 'not an int',
            'color': 'blue',
            'is_deleted': 'not a boolean',
        }
        with pytest.raises(TypeSystemError) as exc:
            parse_form_and_query_params(query_params, sig.parameters)

        assert {
            'age': 'value must be a valid type (integer)',
            'is_deleted': 'value must be a valid type (boolean)',
        } == exc.value.errors

    def test_parse_form_and_query_params_no_doctor_type_param_in_sig(self):
        """
        This is a regression test for when a logic function has a parameter
        in it's signature that is not annotated by a doctor type and the name
        of the parameter matches a parameter in the request variables.
        Previously this would cause an AttributeError.
        """
        def logic(age: Age, use_cache: bool = False):
            pass

        sig = inspect.signature(logic)
        params = {
            'age': '22',
            'use_cache': '1',
        }
        actual = parse_form_and_query_params(params, sig.parameters)
        expected = {'age': 22}
        assert expected == actual

    def test_map_param_names(seilf):
        def foo(lat: Latitude, lon: Longitude, opt_in: OptIn, auth: Auth):
            pass

        sig = inspect.signature(foo)
        request_params = {
            'auth': 'auth',
            'location.lat': 45.12345,
            'locationLon': -122.12345,
            'opt-in': True,
        }
        actual = map_param_names(request_params, sig.parameters)

        expected = {
            'auth': 'auth',
            'lat': 45.12345,
            'lon': -122.12345,
            'opt_in': True,
        }
        assert expected == actual
