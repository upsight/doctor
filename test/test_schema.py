import os

import jsonschema
import mock
import simplejson as json

from doctor.errors import (
    ParseError, SchemaError, SchemaLoadingError, SchemaValidationError)
from doctor.schema import Schema, SchemaRefResolver
from .base import TestCase


class TestSchema(TestCase):

    def setUp(self):
        self.schema = Schema.from_file(os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml'))

    @mock.patch('doctor.schema.logging')
    def test_from_file_error(self, mock_logging):
        schema_filename = os.path.join(os.path.dirname(__file__),
                                       'schema', 'bad_yaml.yaml')
        with self.assertRaises(SchemaLoadingError):
            Schema.from_file(schema_filename)
        self.assertEqual(mock_logging.exception.call_args_list, [mock.call(
            'Error loading schema file {}'.format(schema_filename))])

    def test_get_validator(self):
        validator = self.schema.get_validator()
        self.assertIsInstance(validator, jsonschema.Draft4Validator)
        self.assertEqual(validator.resolver, self.schema.resolver)
        self.assertEqual(validator.schema, self.schema.schema)

    def test_resolver(self):
        self.assertIsNone(self.schema._resolver)
        resolver = self.schema.resolver
        self.assertIsInstance(resolver, jsonschema.RefResolver)
        self.assertEqual(resolver, self.schema._resolver)

    def test_validate(self):
        value = {'annotation_id': 1,
                 'name': 'hodor'}
        result = self.schema.validate(value, self.schema.get_validator())
        self.assertEqual(result, value)

    def test_validate_error(self):
        bad_value = {'annotation_id': 'hodor',
                     'name': 'hodor'}
        with self.assertRaisesRegexp(
                SchemaValidationError, r"'hodor' is not of type 'integer'"):
            self.schema.validate(bad_value, self.schema.get_validator())

    def test_validate_format_error(self):
        bad_value = {
            'annotation_id': 1,
            'name': 'hodor',
            'url': 'not-a-url-but-i-am-a-string',
        }
        with self.assertRaisesRegexp(
                SchemaValidationError,
                r"'not-a-url-but-i-am-a-string' is not a 'uri'"):
            self.schema.validate(bad_value, self.schema.get_validator())

    def test_validate_json(self):
        value = {'annotation_id': 1,
                 'name': 'hodor'}
        result = self.schema.validate_json(json.dumps(value),
                                           self.schema.get_validator())
        self.assertEqual(result, value)

    def test_validate_json_with_key_from_ref(self):
        value = {'annotation_id': 1,
                 'name': 'hodor',
                 'auth': 'abcd'}
        result = self.schema.validate_json(json.dumps(value),
                                           self.schema.get_validator())
        self.assertEqual(result, value)

    def test_validate_json_with_key_from_ref_invalid(self):
        value = {'annotation_id': 1,
                 'name': 'hodor',
                 'auth': 1}
        with self.assertRaisesRegexp(
                SchemaValidationError, r"1 is not of type 'string'"):
            self.schema.validate_json(json.dumps(value),
                                      self.schema.get_validator())

    def test_validate_json_error_invalid_data_multiple_errors(self):
        bad_value = json.dumps({'annotation_id': 'hodor',
                                'name': 1})
        expected_error = r"'hodor' is not of type 'integer'"
        with self.assertRaisesRegexp(
                SchemaValidationError, expected_error) as context:
            self.schema.validate_json(bad_value, self.schema.get_validator())
        errors = context.exception.errors
        expected = {
            'annotation_id': expected_error,
            'name': "1 is not of type 'string'",
        }
        self.assertEqual(expected, errors)

    def test_validate_json_error_invalid_json(self):
            with self.assertRaisesRegexp(ParseError, r'Error parsing JSON'):
                self.schema.validate_json(
                    'bad json', self.schema.get_validator())


class TestSchemaRefResolver(TestCase):

    def setUp(self):
        self.schema_filepath = os.path.join(os.path.dirname(__file__),
                                            'schema', 'annotation.yaml')
        self.base_uri = 'file://{}/'.format(
            os.path.dirname(os.path.abspath(self.schema_filepath)))
        self.schema = Schema.from_file(self.schema_filepath)
        self.resolver = self.schema.resolver
        self.assertIsInstance(self.resolver, SchemaRefResolver)

    def test_resolve(self):
        uri, value = self.resolver.resolve('#/test_ref')
        self.assertEqual(uri, self.base_uri + '#/definitions/annotation_id')
        self.assertEqual(value, {'description': 'Auto-increment ID.',
                                 'type': 'integer', 'example': 1})

    def test_resolve_external(self):
        """Should be able to resolve references to other files."""
        uri, value = self.resolver.resolve('#/properties/auth')
        self.assertEqual(uri, self.base_uri + 'common.yaml#/definitions/auth')
        self.assertEqual(value, {'description': 'auth token',
                                 'example': 'eb25f25becca416092752b0f457f1271',
                                 'type': ['string']})

    def test_resolve_error(self):
        with self.assertRaisesRegexp(
                SchemaError, r"Unresolvable JSON pointer: u?'invalid_ref'"):
            self.resolver.resolve('#/invalid_ref')

    def test_resolve_error_chain(self):
        expected_message = (
            r"Unresolvable JSON pointer: u?'invalid_ref_chain_3' \(from "
            r"/ => /#/invalid_ref_chain_1 => /#/invalid_ref_chain_2\)")
        with self.assertRaisesRegexp(SchemaError, expected_message):
            self.resolver.resolve('#/invalid_ref_chain_1')

    def test_resolve_error_circular_chain(self):
        """If there is a circular reference, should raise an error."""
        expected_message = (
            r"Circular reference in schema: / => /#/circular_ref_chain_1 => "
            r"/#/circular_ref_chain_2 => /#/circular_ref_chain_3 => "
            r"/#/circular_ref_chain_1")
        with self.assertRaisesRegexp(SchemaError, expected_message):
            self.resolver.resolve('#/circular_ref_chain_1')
