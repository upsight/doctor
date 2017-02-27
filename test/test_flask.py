import os

import jsonschema
import mock

from doctor.errors import (
    ForbiddenError, ImmutableError, InvalidValueError, ParseError,
    NotFoundError, SchemaValidationError, UnauthorizedError)
from doctor.flask import (
    FlaskResourceSchema, SchematicHTTPException, handle_http,
    HTTP400Exception, HTTP401Exception, HTTP403Exception, HTTP404Exception,
    HTTP409Exception, HTTP500Exception)
from .base import TestCase


class TestFlask(TestCase):

    def setUp(self):
        self.mock_handler = mock.Mock()

        self.mock_logic = mock.Mock(spec=['_autospec'])
        self.mock_logic.return_value = {'foo': 1}

        self.mock_request_patch = mock.patch('doctor.flask.request')
        self.mock_request = self.mock_request_patch.start()

        self.schema = FlaskResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer'},
                'response': {
                    'type': 'object',
                    'properties': {
                        'foo': {'type': 'integer'},
                    },
                    'additionalProperties': False
                }
            }
        })
        self.request_schema = self.schema._create_request_schema(
            params=('a', 'b', 'c'), required=('a', 'b'))
        self.request_validator = jsonschema.Draft4Validator(
            self.request_schema, resolver=self.schema.resolver)
        self.response_schema = self.schema.resolve('#/definitions/response')
        self.response_validator = jsonschema.Draft4Validator(
            self.response_schema, resolver=self.schema.resolver)
        self.allowed_exceptions = None

    def tearDown(self):
        self.mock_request_patch.stop()

    def call_handle_http(self, args=None, kwargs=None):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        return handle_http(self.schema, self.mock_handler, args, kwargs,
                           self.mock_logic, self.request_schema,
                           self.request_validator, self.response_validator,
                           self.allowed_exceptions)

    def mock_logic_exception(self, exception):
        self.mock_request.content_type = 'application/json; charset=UTF8'
        self.mock_request.mimetype = 'application/json'
        self.mock_request.json = {'a': 'foo', 'b': 1}
        self.mock_logic.side_effect = exception

    def test_from_file(self):
        schema_filepath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'schema', 'annotation.yaml'))
        schema_path = os.path.dirname(schema_filepath)
        schema = FlaskResourceSchema.from_file(schema_filepath)
        self.assertIsInstance(schema, FlaskResourceSchema)
        self.assertEqual(schema._schema_path, schema_path)
        self.assertEqual(schema.handle_http, handle_http)
        # Should be able to resolve a ref to another file
        self.assertEqual(schema.resolve('#/properties/auth'), {
            'description': 'auth token',
            'example': 'eb25f25becca416092752b0f457f1271',
            'type': ['string']
        })

    def test_handle_http_with_json(self):
        self.mock_request.method = 'POST'
        self.mock_request.content_type = 'application/json; charset=UTF8'
        self.mock_request.mimetype = 'application/json'
        self.mock_request.json = {'a': 'foo', 'b': 1}
        result = self.call_handle_http((10,), {'b': 2, 'x': 20, 'y': 30})
        self.assertEqual(result, ({'foo': 1}, 201))
        self.assertEqual(self.mock_logic.call_args_list,
                         [mock.call(10, x=20, y=30, a='foo', b=2)])

    def test_handle_http_with_params(self):
        self.mock_request.method = 'DELETE'
        self.mock_request.content_type = 'application/x-www-form-urlencoded'
        self.mock_request.values = {'a': 'foo', 'b': '1'}
        result = self.call_handle_http((10,), {'b': 2, 'x': 20, 'y': 30})
        self.assertEqual(result, ({'foo': 1}, 204))
        self.assertEqual(self.mock_logic.call_args_list,
                         [mock.call(10, x=20, y=30, a='foo', b=2)])

    @mock.patch('doctor.flask.MAX_RESPONSE_LENGTH', 10)
    @mock.patch('doctor.flask.logging')
    def test_handle_http_catch_and_log_response_validaiton_errors(
            self, logging_mock):
        """
        This test verifies that if the schema attribute
        `raise_response_validation_errors` is False we simply log
        the error as a warning and return the result, instead of
        raising the exception.
        """
        self.schema = FlaskResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer'},
                'response': {
                    'type': 'object',
                    'properties': {
                        'foo': {'type': 'integer'},
                    },
                    'additionalProperties': False
                }
            }
        }, raise_response_validation_errors=False)
        self.mock_logic = mock.Mock(spec=['_autospec'])
        self.mock_logic.return_value = {'dinosaurs': 'are extinct'}
        self.mock_request.method = 'GET'
        self.mock_request.path = '/foo'
        self.mock_request.content_type = 'application/x-www-form-urlencoded'
        self.mock_request.values = {'a': 'foo', 'b': '1'}
        result = self.call_handle_http((10,), {'b': 2, 'x': 20, 'y': 30})

        expected = ({'dinosaurs': 'are extinct'}, 200)
        self.assertEqual(expected, result)
        expected_call = mock.call(
            'Response to %s %s does not validate: %s.', 'GET', '/foo',
            "{'dinosaur...", exc_info=mock.ANY)
        self.assertEqual(expected_call, logging_mock.warning.call_args)

    def test_handle_http_raise_response_validaiton_errors(self):
        """
        This test verifies that if the schema attribute
        `raise_response_validation_errors` is True we raise the
        exception.
        """
        self.schema = FlaskResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer'},
                'response': {
                    'type': 'object',
                    'properties': {
                        'foo': {'type': 'integer'},
                    },
                    'additionalProperties': False
                }
            }
        }, raise_response_validation_errors=True)
        self.mock_logic = mock.Mock(spec=['_autospec'])
        self.mock_logic.return_value = {'dinosaurs': 'are extinct'}
        self.mock_request.method = 'GET'
        self.mock_request.content_type = 'application/x-www-form-urlencoded'
        self.mock_request.values = {'a': 'foo', 'b': '1'}
        with self.assertRaises(HTTP400Exception) as context:
            self.call_handle_http((10,), {'b': 2, 'x': 20, 'y': 30})
        errors = context.exception.errobj
        expected = {
            '_other': ("Additional properties are not allowed ('dinosaurs' was "
                       "unexpected)"),
        }
        self.assertEqual(expected, errors)

    def test_handle_http_no_schemas(self):
        result = handle_http(self.schema, self.mock_handler, (1, 2),
                             {'a': 3, 'b': 4}, self.mock_logic, None, None,
                             None, None)
        self.assertEqual(result, ({'foo': 1}, 200))
        self.assertEqual(self.mock_logic.call_args_list,
                         [mock.call(1, 2, a=3, b=4)])

    def test_http_error(self):
        """Schematic errors should be re-raised as a SchematicHTTPException."""
        self.mock_request.content_type = 'application/x-www-form-urlencoded'
        self.mock_request.values = {'b': 'bad integer'}
        with self.assertRaisesRegexp(
                SchematicHTTPException, r'b must be a valid type \(integer\)'):
            self.call_handle_http()

    def test_handle_invalid_value_error(self):
        self.mock_logic_exception(InvalidValueError('400'))
        with self.assertRaisesRegexp(HTTP400Exception, r'400'):
            self.call_handle_http()

    def test_handle_immutable_error(self):
        self.mock_logic_exception(ImmutableError('409'))
        with self.assertRaisesRegexp(HTTP409Exception, r'409'):
            self.call_handle_http()

    def test_handle_parse_error(self):
        self.mock_logic_exception(ParseError('400'))
        with self.assertRaisesRegexp(HTTP400Exception, r'400'):
            self.call_handle_http()

    def test_handle_schema_validation_error(self):
        self.mock_logic_exception(SchemaValidationError('400'))
        with self.assertRaisesRegexp(HTTP400Exception, r'400'):
            self.call_handle_http()

    def test_handle_unauthorized_error(self):
        self.mock_logic_exception(UnauthorizedError('401'))
        with self.assertRaisesRegexp(HTTP401Exception, r'401'):
            self.call_handle_http()

    def test_handle_forbidden_error(self):
        self.mock_logic_exception(ForbiddenError('403'))
        with self.assertRaisesRegexp(HTTP403Exception, r'403'):
            self.call_handle_http()

    def test_handle_not_found_error(self):
        self.mock_logic_exception(NotFoundError('404'))
        with self.assertRaisesRegexp(HTTP404Exception, r'404'):
            self.call_handle_http()

    @mock.patch('doctor.flask.current_app')
    def test_handle_unexpected_error(self, mock_current_app):
        mock_current_app.config = {'DEBUG': False}
        self.mock_logic_exception(TypeError('bad type'))
        with self.assertRaisesRegexp(
                HTTP500Exception, r'Uncaught error in logic function'):
            self.call_handle_http()

        # When DEBUG is True, it should reraise the original exception
        mock_current_app.config = {'DEBUG': True}
        with self.assertRaisesRegexp(TypeError, 'bad type'):
            self.call_handle_http()

    @mock.patch('doctor.flask.current_app')
    def test_handle_unexpected_error_allowed_exceptions(self, mock_current_app):
        mock_current_app.config = {'DEBUG': False}

        class ExceptionalException(Exception):
            pass
        self.allowed_exceptions = [ExceptionalException]

        # allowed exceptions should be re-raised
        self.mock_logic_exception(ExceptionalException('should be re-raised'))
        with self.assertRaisesRegexp(
                ExceptionalException, r'should be re-raised'):
            self.call_handle_http()

        # but other exceptions should still be caught
        self.mock_logic_exception(TypeError('bad type'))
        with self.assertRaisesRegexp(
                HTTP500Exception, r'Uncaught error in logic function'):
            self.call_handle_http()
