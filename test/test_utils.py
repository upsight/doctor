import inspect
import os
from functools import wraps

import mock

from .base import TestCase

from doctor.utils import (
    exec_params, get_description_lines, get_module_attr, nested_set,
    undecorate_func)


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


class TestUtils(TestCase):

    def test_exec_params_function(self):
        def logic(a, b, c=None):
            return a+1, b+1, c
        logic._argspec = inspect.getargspec(logic)
        kwargs = {'c': 1, 'd': 'a'}
        args = (1, 2)
        a, b, c = exec_params(logic, *args, **kwargs)
        self.assertEqual(a, args[0]+1)
        self.assertEqual(b, args[1]+1)
        self.assertEqual(c, kwargs['c'])

    def test_exec_params_callable(self):
        kwargs = {'c': 1, 'd': 'a'}
        args = (1, 2)

        class Foo(object):
            def __call__(self, a, b, c=None):
                return a+1, b+1, c
        logic = Foo()
        logic._argspec = inspect.getargspec(logic.__call__)
        a, b, c = exec_params(logic, *args, **kwargs)
        self.assertEqual(a, args[0]+1)
        self.assertEqual(b, args[1]+1)
        self.assertEqual(c, kwargs['c'])

    def test_exec_params_args_only(self):
        def logic(a, b, c):
            return a+1, b+1, c
        logic._argspec = inspect.getargspec(logic)
        kwargs = {'d': 1, 'e': 2}
        args = (1, 2, 3)
        a, b, c = exec_params(logic, *args, **kwargs)
        self.assertEqual(a, args[0]+1)
        self.assertEqual(b, args[1]+1)
        self.assertEqual(c, 3)

    def test_exec_params_kwargs_only(self):
        def logic(a=1, b=2, c=3):
            return a+1, b+1, c
        logic._argspec = inspect.getargspec(logic)
        kwargs = {'d': 1, 'e': 2}
        args = (1, 2, 3)
        a, b, c = exec_params(logic, *args, **kwargs)
        self.assertEqual(a, args[0]+1)
        self.assertEqual(b, args[1]+1)
        self.assertEqual(c, 3)

    def test_exec_params_with_magic_kwargs(self):
        """
        This test replicates a bug where if a logic function were decorated
        and we sendt a json body request that contained parameters not in
        the logic function's signature it would cause a TypeError similar to
        the following for the logic function defined in this test:

        TypeError: logic() got an unexpected keyword argument 'e'

        This test verifies if a logic function uses the **kwargs functionality
        that we pass along those to the logic function in addition to any
        other positional or keyword arguments.
        """
        def logic(a, b=2, c=3, **kwargs):
            return (a, b, c, kwargs)

        logic._argspec = inspect.getargspec(logic)
        kwargs = {'c': 3, 'e': 2}
        args = (1, 2)
        actual = exec_params(logic, *args, **kwargs)
        self.assertEqual((1, 2, 3, {'e': 2}), actual)

    @mock.patch('doctor.utils.open',
                new_callable=mock.mock_open,
                read_data='mock_attr = "something"')
    @mock.patch('doctor.utils.compile', create=True)
    @mock.patch('doctor.utils.os', autospec=True)
    @mock.patch('doctor.utils.sys', autospec=True)
    def test_get_module_attr(self, mock_sys, mock_os, mock_compile, m):
        def side_effect(source, filename, mode, flags=0, dont_inherit=False):
            self.assertEqual(mock_sys.path, ['foo', 'bar', '/foo/bar'])
            return compile(source, filename, mode, flags=flags,
                           dont_inherit=dont_inherit)
        mock_compile.side_effect = side_effect
        mock_os.getcwd.return_value = mock.sentinel.old_cwd
        mock_os.path = os.path
        mock_sys.path = ['foo', 'bar']
        namespace = {}
        result = get_module_attr('/foo/bar/baz', 'mock_attr',
                                 namespace=namespace)
        m.assert_called_once_with('/foo/bar/baz', 'r')
        mock_compile.assert_called_once_with('mock_attr = "something"',
                                             '/foo/bar/baz', 'exec')
        self.assertEqual(result, 'something')
        self.assertEqual(namespace['__file__'], '/foo/bar/baz')
        self.assertEqual(mock_os.chdir.call_args_list,
                         [mock.call('/foo/bar'),
                          mock.call(mock.sentinel.old_cwd)])
        self.assertEqual(mock_sys.path, ['foo', 'bar'])

    def test_get_description_lines(self):
        """
        Tests that get_description_lines properly dedents docstrings and strips
        out values we don't want.
        """
        docstring = """line one

                       line two

                           indented line three

                       line four

                       :param str c: example param
                       :returns: d
                       """
        self.assertEqual(get_description_lines(docstring), [
            'line one',
            '',
            'line two',
            '',
            '    indented line three',
            '',
            'line four',
            '',
        ])

    def test_get_description_lines_none(self):
        """It should just return an empty list for None."""
        self.assertEqual(get_description_lines(None), [])

    def test_get_description_lines_trailing_newline(self):
        """It should add a trailing line if necessary."""
        self.assertEqual(get_description_lines('foo\n:arg'), ['foo', ''])

    def test_nested_set(self):
        data_dict = {}
        nested_set(data_dict, ["b", "v", "new"], {})
        self.assertEqual(data_dict['b']['v']['new'], {})

        nested_set(data_dict, ["b", "v", "new"], '4')
        self.assertEqual(data_dict['b']['v']['new'], '4')

        nested_set(data_dict, ["a", "v", "new"], '1')
        self.assertEqual(data_dict['a']['v']['new'], '1')

        nested_set(data_dict, ["a", "new"], 'new')
        self.assertEqual(data_dict['a']['new'], 'new')

    def test_undecorate_func(self):
        def foobar(a, b=False):
            pass

        # No decorator just returns the function
        actual = undecorate_func(foobar)
        self.assertEqual(foobar, actual)

        # Normal decorator with no args
        decorated = does_nothing(foobar)
        actual = undecorate_func(decorated)
        self.assertEqual(foobar, actual)

        # Ensure it can handle multiple decorators
        double_decorated = does_nothing(does_nothing(foobar))
        actual = undecorate_func(double_decorated)
        self.assertEqual(foobar, actual)

        # Ensure it works with decorators that take arguments
        decorated_with_args = dec_with_args('foo1')(foobar)
        actual = undecorate_func(decorated_with_args)
        self.assertEqual(foobar, actual)

        def bar(foo):
            return 'foo ' + foo

        decorated_with_arg_takes_func = (
            dec_with_args_one_of_which_allows_a_func('foo', bar)(foobar))
        actual = undecorate_func(decorated_with_arg_takes_func)
        self.assertEqual(foobar, actual)
