import inspect
import os
from functools import wraps
from inspect import Parameter

import mock

from doctor.routing import get_params_from_func
from doctor.utils import (
    add_param_annotations, get_description_lines, get_module_attr,
    get_valid_class_name, Params, RequestParamAnnotation)

from .base import TestCase
from .types import Age, Auth, Foo, IsAlive, IsDeleted, Name


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


def no_params() -> Foo:
    return ''


def get_foo(name: Name, age: Age, is_alive: IsAlive=True) -> Foo:
    return ''


def pass_pos_param(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func('extra!', *args, **kwargs)
    return wrapper


@pass_pos_param
def decorated_func(extra: str, name: Name, is_alive: IsAlive=True) -> Foo:
    return ''


class TestUtils(TestCase):

    def test_add_param_annotations(self):
        new_params = [
            RequestParamAnnotation('auth', Auth, required=True),
            RequestParamAnnotation('is_deleted', IsDeleted)
        ]
        actual = add_param_annotations(get_foo, new_params)
        # auth and is_deleted should be added to `all`.
        # auth should be added to `required`.
        # is_deleted should be added to `optional`.
        # `logic` should be unmodified.
        expected_params = Params(
            all=['name', 'age', 'is_alive', 'auth', 'is_deleted'],
            logic=['name', 'age', 'is_alive'],
            required=['name', 'age', 'auth'],
            optional=['is_alive', 'is_deleted']
        )
        assert expected_params == actual._doctor_params

        # verify `auth` added to the doctor_signature.
        expected = Parameter('auth', Parameter.KEYWORD_ONLY,
                             default=Parameter.empty, annotation=Auth)
        auth = actual._doctor_signature.parameters['auth']
        assert expected == auth

        # verify `is_deleted` added to the doctor signature.
        expected = Parameter('is_deleted', Parameter.KEYWORD_ONLY,
                             default=None, annotation=IsDeleted)
        is_deleted = actual._doctor_signature.parameters['is_deleted']
        assert expected == is_deleted

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

    def test_get_params_from_func(self):
        get_foo._doctor_signature = inspect.signature(get_foo)
        expected = Params(
            all=['name', 'age', 'is_alive'],
            optional=['is_alive'],
            required=['name', 'age'],
            logic=['name', 'age', 'is_alive'])
        assert expected == get_params_from_func(get_foo)

    def test_get_params_from_func_no_params(self):
        # no signature passed or defined on the function
        expected = Params([], [], [], [])
        assert expected == get_params_from_func(no_params)

        # signature passed in
        signature = inspect.signature(no_params)
        assert expected == get_params_from_func(no_params, signature)

        # signature attached to logic function
        no_params._doctor_signature = inspect.signature(no_params)
        assert expected == get_params_from_func(no_params)

    def test_get_params_from_func_decorated_func(self):
        """
        Verifies that we don't include the `extra` param as required since
        it's not a sublcass of `SuperType` and is passed to the function
        by a decorator.
        """
        decorated_func._doctor_signature = inspect.signature(decorated_func)
        expected = Params(
            all=['extra', 'name', 'is_alive'],
            required=['name'],
            optional=['is_alive'],
            logic=['extra', 'name', 'is_alive'])
        assert expected == get_params_from_func(decorated_func)

    def test_get_valid_class_name(self):
        tests = (
            # (input, expected)
            ('Notes', 'Notes'),
            ('Notes (v1)', 'NotesV1'),
            ('Notes - "v1"', 'NotesV1'),
            ('note_book.', 'NoteBook'),
            ('notes', 'Notes'),
            ('note-book_v1 .', 'NoteBookV1'),
        )
        for s, expected in tests:
            assert expected == get_valid_class_name(s)
