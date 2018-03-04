from functools import wraps
from inspect import Parameter

import mock

from doctor.resource import ResourceAnnotation, ResourceSchemaAnnotation

from .base import TestCase
from .types import ItemId
from .utils import add_doctor_attrs


def does_nothing(func):
    """An example decorator that does nothing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def plain_logic(a, b=1):
    return (a, b)


def plain_logic_with_kwargs(a, b=1, **kwargs):
    return (a, b, kwargs)


@does_nothing
def decorated_logic(a, b=1):
    return (a, b)


@does_nothing
def decorated_logic_with_kwargs(a, b=1, **kwargs):
    return (a, b, kwargs)


class TestResourceAnnotation(TestCase):

    def test_init(self):
        def logic(user_id: int, item_id: ItemId):
            pass

        logic = add_doctor_attrs(logic)
        annotation = ResourceAnnotation(logic, 'POST')
        assert annotation.logic == logic
        assert annotation.http_method == 'POST'
        assert annotation.title == 'Create'

        # Verify that the annotated_parameters attribute only has parameters
        # from the signature that are doctor types.  It shouldn't include
        # `user_id` since int doesn't extend doctor.types.SuperType
        expected = Parameter('item_id', Parameter.POSITIONAL_OR_KEYWORD,
                             default=Parameter.empty, annotation=ItemId)
        assert {'item_id': expected} == annotation.annotated_parameters

    def test_init_title(self):
        def logic():
            pass

        logic = add_doctor_attrs(logic)
        tests = (
            # (http_method, title, expected)
            ('GET', None, 'Retrieve'),
            ('POST', None, 'Create'),
            ('PUT', None, 'Update'),
            ('DELETE', None, 'Delete'),
            ('PUT', 'Batch', 'Batch'),
        )
        for http_method, title, expected in tests:
            annotation = ResourceAnnotation(logic, http_method, title=title)
            self.assertEqual(expected, annotation.title)


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
