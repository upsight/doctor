from functools import wraps
import os

import mock

from doctor.resource import ResourceSchema
from doctor.router import Router, RouterException
from .base import TestCase


def does_nothing(func):
    """An example decorator that does nothing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def dec_with_args(foo='foo', bar='bar'):
    """An example decorator that takes args and passes value to func."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func('arg', *args, **kwargs)
        return wrapper
    return decorator


def dec_with_args_one_of_which_allows_a_func(foo, bar=None):
    """An example decorator that takes args where one is a function.

    In this case, bar accepts a func which transforms foo.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if bar is not None:
                bar(foo)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RouterTestCase(TestCase):

    def setUp(self):
        super(RouterTestCase, self).setUp()
        schema_dir = os.path.join(os.path.dirname(__file__), 'schema')
        self.router = Router(schema_dir, ResourceSchema)

    def test_init(self):
        s = mock.sentinel
        router = Router(s.schema_dir, s.resource_schema_class,
                        s.default_base_handler)
        self.assertEqual(s.schema_dir, router.schema_dir)
        self.assertEqual(s.resource_schema_class, router.resource_schema_class)
        self.assertEqual(s.default_base_handler, router.default_base_handler)

        # ensure default_base_handler is `object` if not passed
        router = Router(s.schema_dir, s.resource_schema_class)
        self.assertEqual(object, router.default_base_handler)

    def test_get_schema_schema_already_initialized(self):
        resource_schema_class = mock.Mock()
        router = Router('/path/to/schema/dir/', resource_schema_class)
        router.schemas['foobar.yaml'] = 'foobar'
        actual = router.get_schema('foobar.yaml')
        expected = 'foobar'
        self.assertEqual(expected, actual)
        self.assertFalse(resource_schema_class.class_from_file.called)

    def test_get_schema_schema_not_initialized(self):
        resource_schema_class = mock.Mock()
        resource_schema_class.from_file.return_value = 'foobar'
        router = Router('/path/to/schema/dir/', resource_schema_class)
        actual = router.get_schema('foobar.yaml')
        expected = 'foobar'
        self.assertEqual(expected, actual)

    def test_undecorate_func(self):
        def foobar(a, b=False):
            pass

        # No decorator just returns the function
        actual = self.router._undecorate_func(foobar)
        self.assertEqual(foobar, actual)

        # Normal decorator with no args
        decorated = does_nothing(foobar)
        actual = self.router._undecorate_func(decorated)
        self.assertEqual(foobar, actual)

        # Ensure it can handle multiple decorators
        double_decorated = does_nothing(does_nothing(foobar))
        actual = self.router._undecorate_func(double_decorated)
        self.assertEqual(foobar, actual)

        # Ensure it works with decorators that take arguments
        decorated_with_args = dec_with_args('foo1')(foobar)
        actual = self.router._undecorate_func(decorated_with_args)
        self.assertEqual(foobar, actual)

        def bar(foo):
            return 'foo ' + foo

        decorated_with_arg_takes_func = (
            dec_with_args_one_of_which_allows_a_func('foo', bar)(foobar))
        actual = self.router._undecorate_func(decorated_with_arg_takes_func)
        self.assertEqual(foobar, actual)

    def test_get_params_from_func_with_optional(self):
        def foobar(req1, req2, opt1=None, opt2=False):
            pass

        actual = self.router._get_params_from_func(foobar)
        expected = (['req1', 'req2', 'opt1', 'opt2'], ['req1', 'req2'])
        self.assertEqual(expected, actual)

    def test_get_params_from_func_all_required(self):
        def foobar(req1, req2, req3):
            pass

        actual = self.router._get_params_from_func(foobar)
        expected = (['req1', 'req2', 'req3'], ['req1', 'req2', 'req3'])
        self.assertEqual(expected, actual)

    def test_get_params_from_func_omit_args(self):
        def foobar(req1, req2, opt1=None, opt2=False):
            pass

        omit_args = ['req1']
        actual = self.router._get_params_from_func(foobar, omit_args)
        expected = (['req2', 'opt1', 'opt2'], ['req2'])
        self.assertEqual(expected, actual)

    def test_get_params_from_decorated_func(self):
        @dec_with_args('foo')
        @does_nothing
        def foobar(page, req1, opt1=None):
            pass

        omit_args = ['page']
        actual = self.router._get_params_from_func(foobar, omit_args)
        expected = (['req1', 'opt1'], ['req1'])
        self.assertEqual(expected, actual)

    def test_create_routes_no_logic_func_raises_exc(self):
        with self.assertRaises(RouterException):
            self.router.create_routes('title', 'annotation.yaml', {
                '^/foobar/?$': {
                    'get': {},
                },
            })

    def test_create_routes(self):
        class BaseHandler(object):
            pass

        def logic_get(req1, opt1=None):
            pass

        def logic_post(req1, opt1=None):
            pass

        actual = self.router.create_routes('Annotation', 'annotation.yaml', {
            '^/annotation/?$': {
                'additional_args': {
                    'required': ['auth'],
                },
                'base_handler_class': BaseHandler,
                'decorators': [does_nothing],
                'handler_name': 'AnnotationHandlerV1',

                'get': {
                    'logic': logic_get,
                    # Specifying a different schema file that contains `someid`
                    # for the response.  An example of overriding the schema
                    # at the http method level.  This would fail without the
                    # schema key since someid is not defined in annotation.yaml
                    'schema': 'common.yaml',
                    'response': 'someid',
                },
                'post': {
                    'additional_args': {
                        'optional': ['limit', 'offset'],
                    },
                    'allowed_exceptions': [Exception],
                    'logic': logic_post,
                    'omit_args': ['req1'],
                    'response': 'annotation',
                    'title': 'Custom Title',
                },
            },
        })
        self.assertEqual('^/annotation/?$', actual[0][0])
        handler = actual[0][1]

        # Verify the class name is as expected.
        self.assertEqual('AnnotationHandlerV1', handler.__name__)
        self.assertTrue(issubclass(handler, BaseHandler))
        self.assertTrue(hasattr(handler, 'get'))
        self.assertTrue(hasattr(handler, 'post'))
        self.assertEqual('Annotation', handler.schematic_title)
        self.assertEqual(['req1', 'auth'], handler.get.required_args)
        # Since we omitted `req` for the post method, it will only have `auth`
        # defined in addtional_args as required.
        self.assertEqual(['auth'], handler.post.required_args)
