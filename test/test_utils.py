import inspect
import os

import mock

from .base import TestCase

from doctor.utils import (
    exec_params, get_description_lines, get_module_attr, nested_set)


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

    @mock.patch('doctor.utils.execfile', create=True)
    @mock.patch('doctor.utils.os', autospec=True)
    @mock.patch('doctor.utils.sys', autospec=True)
    def test_get_module_attr(self, mock_sys, mock_os, mock_execfile):
        def side_effect(module_filename, namespace):
            self.assertEqual(mock_sys.path, ['foo', 'bar', '/foo/bar'])
            self.assertEqual(module_filename, '/foo/bar/baz')
            self.assertEqual(namespace, {'__file__': module_filename})
            namespace['mock_attr'] = mock.sentinel.mock_attr
        mock_execfile.side_effect = side_effect
        mock_os.getcwd.return_value = mock.sentinel.old_cwd
        mock_os.path = os.path
        mock_sys.path = ['foo', 'bar']
        result = get_module_attr('/foo/bar/baz', 'mock_attr')
        self.assertEqual(result, mock.sentinel.mock_attr)
        self.assertEqual(len(mock_execfile.call_args_list), 1)
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
