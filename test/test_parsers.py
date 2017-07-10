# encoding: utf-8

from doctor.errors import ParseError
from doctor.parsers import parse_json, parse_value
from .base import TestCase


class TestParsers(TestCase):

    def test_parse_json(self):
        self.assertEqual(parse_json('{"foo": 1}'), {'foo': 1})
        with self.assertRaisesRegexp(
                ParseError, r'Error parsing JSON: Expecting value'):
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
            self.assertEqual(parse_value(value, allowed_types), expected)

    def test_parse_value_errors(self):
        """These cases should raise an error when parsing."""
        tests = {'array': ['{}', '['],
                 'boolean': ['0', '1'],
                 'float': ['bad'],
                 'integer': ['bad', '0.1'],
                 'object': ['[]', '{']}
        for allowed_type, bad_values in list(tests.items()):
            for bad_value in bad_values:
                with self.assertRaises(ParseError):
                    parse_value(bad_value, [allowed_type])

    def test_parse_value_error_not_string(self):
        """Should raise an error if the value isn't a string."""
        with self.assertRaisesRegexp(
                ValueError, r"value for 'foo' must be a string"):
            parse_value(1337, [], 'foo')
