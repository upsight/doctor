import mock

from doctor.resource import ResourceSchema, ResourceSchemaAnnotation
from doctor.flask import handle_http
from .base import TestCase


class TestResourceSchema(TestCase):

    def setUp(self):
        self.mock_handle_http = mock.Mock(autospec=True, spec=handle_http,
                                          return_value=mock.sentinel.result)

    def test_create_request_schema(self):
        schema = ResourceSchema({'definitions': mock.sentinel.definitions},
                                self.mock_handle_http)
        request_schema = schema._create_request_schema(params=('a', 'b', 'c'),
                                                       required=('b', 'c'))
        self.assertEqual(request_schema, {
            'additionalProperties': True,
            'definitions': mock.sentinel.definitions,
            'properties': {'a': {'$ref': '#/definitions/a'},
                           'b': {'$ref': '#/definitions/b'},
                           'c': {'$ref': '#/definitions/c'}},
            'required': ('b', 'c'),
            'type': 'object',
        })

    def test_parse_params(self):
        schema = ResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer'},
                'd': {'type': ['integer', 'null']},
                'e': {'type': ['array']},
                'f': {'type': ['object']}
            }
        }, self.mock_handle_http)
        request_schema = schema._create_request_schema(
            params=('a', 'b', 'c', 'd', 'e', 'f'),
            required=None)
        params = {
            'a': 'hodor',
            'b': '1',
            'd': '',
            'e': '[1, 2]',
            'f': '{"foo": 1}',
        }
        expected = {
            'a': 'hodor',
            'b': 1,
            'd': None,
            'e': [1, 2],
            'f': {'foo': 1},
        }
        self.assertEqual(schema._parse_params(params, request_schema),
                         expected)

    def test_create_http_method(self):
        s = mock.sentinel
        mock_logic = mock.Mock()
        mock_logic.__name__ = 'mock_name'
        mock_logic.__doc__ = s.__doc__
        schema = ResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'b': {'type': 'integer'},
                'c': {'type': 'integer'},
                'request': {
                    'type': 'object',
                    'properties': {
                        'bar': {'type': 'integer'},
                    },
                    'additionalProperties': False,
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'foo': {'type': 'integer'},
                    },
                    'additionalProperties': False,
                },
            },
        }, self.mock_handle_http)
        handler = schema._create_http_method(
            mock_logic, 'POST', params=('a', 'b', 'c'), required=('a', 'b'),
            response='response', allowed_exceptions=s.allowed_exceptions)
        annotation = handler._schema_annotation
        self.assertTrue(callable(handler))
        self.assertEqual(handler.__name__, 'mock_name')
        self.assertEqual(handler.__doc__, s.__doc__)
        self.assertEqual(annotation.request_schema, {
            'additionalProperties': True,
            'definitions': schema.resolve('#/definitions'),
            'properties': {
                'a': {'$ref': '#/definitions/a'},
                'b': {'$ref': '#/definitions/b'},
                'c': {'$ref': '#/definitions/c'}
            },
            'required': ('a', 'b'),
            'type': 'object',
        })
        self.assertEqual(annotation.response_schema,
                         schema.resolve('#/definitions/response'))
        result = handler(s.handler, 1, x=2, y=3)
        self.assertEqual(result, s.result)
        self.assertEqual(self.mock_handle_http.call_args_list, [
            mock.call(schema, s.handler, (1,), {'x': 2, 'y': 3}, mock_logic,
                      annotation.request_schema, mock.ANY, mock.ANY,
                      s.allowed_exceptions)
        ])

        # Test a handler with an explicit request schema
        self.mock_handle_http.reset_mock()
        handler = schema._create_http_method(mock_logic, 'POST',
                                             request='request',
                                             response='response')
        annotation = handler._schema_annotation
        self.assertEqual(annotation.request_schema,
                         schema.resolve('#/definitions/request'))
        self.assertEqual(annotation.response_schema,
                         schema.resolve('#/definitions/response'))

        # Test a handler without any params
        self.mock_handle_http.reset_mock()
        handler = schema._create_http_method(mock_logic, 'POST',
                                             response='response')
        annotation = handler._schema_annotation
        self.assertIsNone(annotation.request_schema)
        self.assertEqual(annotation.response_schema,
                         schema.resolve('#/definitions/response'))
        result = handler(s.handler, 1, x=2, y=3)
        self.assertEqual(result, s.result)
        self.assertEqual(self.mock_handle_http.call_args_list, [
            mock.call(schema, s.handler, (1,), {'x': 2, 'y': 3}, mock_logic,
                      None, None, mock.ANY, None)
        ])

        # Test a handler without a response schema
        self.mock_handle_http.reset_mock()
        handler = schema._create_http_method(
            mock_logic, 'POST', params=('a', 'b', 'c'), required=('a', 'b'))
        annotation = handler._schema_annotation
        self.assertIsNone(annotation.response_schema)
        handler(s.handler, 1, x=2, y=3)
        self.assertEqual(result, s.result)
        self.assertEqual(self.mock_handle_http.call_args_list, [
            mock.call(schema, s.handler, (1,), {'x': 2, 'y': 3}, mock_logic,
                      annotation.request_schema, mock.ANY, None, None)
        ])

    def test_before_after_callables(self):
        mock_logic = mock.Mock()
        mock_logic.__name__ = 'mock_name'
        mock_logic.__doc__ = mock.sentinel.__doc__

        schema = ResourceSchema({
            'definitions': {
                'a': {'type': 'string'},
                'request': {
                    'type': 'object',
                    'properties': {
                        'bar': {'type': 'integer'},
                    },
                    'additionalProperties': False,
                },
                'response': {
                    'type': 'object',
                    'properties': {
                        'foo': {'type': 'integer'},
                    },
                    'additionalProperties': False,
                },
            },
        }, self.mock_handle_http)

        before_mock = mock.Mock()
        after_mock = mock.Mock()
        handler = schema.http_post(
            mock_logic,
            before=before_mock,
            after=after_mock)
        handler(mock.sentinel.handler, 1, x=2)
        self.assertTrue(before_mock.called)
        self.assertTrue(after_mock.called)

        before_mock.reset_mock()
        after_mock.reset_mock()
        handler = schema.http_get(
            mock_logic, after=after_mock)
        handler(mock.sentinel.handler, 1, x=2)
        self.assertFalse(before_mock.called)
        self.assertTrue(after_mock.called)

        def after(self, result, *args, **kwargs):
            result.name = 'hi'

        handler = schema.http_get(
            mock_logic, after=after)
        result = handler(mock.sentinel.handler, 1, x=2)
        self.assertEqual(result.name, 'hi')

    @mock.patch.object(ResourceSchema, '_create_http_method', autospec=True,
                       return_value=mock.sentinel.result)
    def test_http_methods(self, mock_create_http_method):
        s = mock.sentinel
        schema = ResourceSchema({}, self.mock_handle_http)
        for method in ('delete', 'get', 'post', 'put'):
            mock_create_http_method.reset_mock()
            fn = getattr(schema, 'http_{}'.format(method))
            result = fn(s.logic, s.request, s.response, s.params, s.required,
                        title=s.title)
            self.assertEqual(result, s.result)
            self.assertEqual(
                mock_create_http_method.call_args_list,
                [mock.call(schema, s.logic, method.upper(), request=s.request,
                           response=s.response, params=s.params,
                           required=s.required, title=s.title, before=None,
                           after=None, allowed_exceptions=None)])


class TestResourceSchemaAnnotation(TestCase):

    def test_init(self):
        s = mock.sentinel
        annotation = ResourceSchemaAnnotation(
            s.logic, 'POST', s.schema, s.request_schema,
            s.response_schema)
        self.assertEqual(annotation.logic, s.logic)
        self.assertEqual(annotation.http_method, 'POST')
        self.assertEqual(annotation.schema, s.schema)
        self.assertEqual(annotation.request_schema, s.request_schema)
        self.assertEqual(annotation.response_schema, s.response_schema)
        self.assertEqual(annotation.title, 'Create')

    def test_init_title(self):
        tests = (
            # (http_method, title, expected)
            ('GET', None, 'Retrieve'),
            ('POST', None, 'Create'),
            ('PUT', None, 'Update'),
            ('DELETE', None, 'Delete'),
            ('PUT', 'Batch', 'Batch'),
        )
        s = mock.sentinel
        for http_method, title, expected in tests:
            annotation = ResourceSchemaAnnotation(
                s.logic, http_method, s.schema, s.request_schema,
                s.response_schema, title=title)
            self.assertEqual(expected, annotation.title)

    def test_get_annotation(self):
        """Tests that get_annotation works for badly decorated functions."""
        def decorator(fn):
            def wrapper():
                fn()
            return wrapper
        mock_logic = mock.Mock()
        mock_logic._schema_annotation = mock.sentinel.logic_annotation
        wrapper = decorator(mock_logic)
        self.assertEqual(ResourceSchemaAnnotation.get_annotation(mock_logic),
                         mock.sentinel.logic_annotation)
        self.assertEqual(ResourceSchemaAnnotation.get_annotation(wrapper),
                         mock.sentinel.logic_annotation)
        wrapper._schema_annotation = mock.sentinel.wrapper_annotation
        self.assertEqual(ResourceSchemaAnnotation.get_annotation(wrapper),
                         mock.sentinel.wrapper_annotation)
        delattr(wrapper, '_schema_annotation')
        delattr(mock_logic, '_schema_annotation')
        self.assertIsNone(ResourceSchemaAnnotation.get_annotation(wrapper))
