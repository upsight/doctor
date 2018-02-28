import json

import mock
from werkzeug.routing import Rule

from doctor.docs import base
from doctor.resource import ResourceAnnotation

from .base import TestCase
from .types import (
    Age, Auth, Color, ExampleArray, ExampleObject, ExampleObjects, IsAlive,
    IsDeleted, Name)
from .utils import add_doctor_attrs


class TestDocsBase(TestCase):

    def test_prefix_lines_bytes(self):
        """
        This is a regression test where the response was a bytes instance.
        """
        lines = b'"Notes API v1.0.0"'
        prefix = '   '
        expected = ['   "Notes API v1.0.0"']
        assert expected == base.prefix_lines(lines, prefix)

    def test_get_example_lines_json(self):
        """Tests an example when the response is valid JSON."""
        headers = {'GeoIp-Country-Code': 'US'}
        lines = base.get_example_lines(headers, 'GET', 'http://example.com/',
                                       {}, json.dumps({'foo': 1, 'bar': 2}))
        self.assertEqual(lines, [
            '',
            'Example Request:',
            '',
            '.. code-block:: bash',
            '',
            '   curl http://example.com/ -X GET -H \'GeoIp-Country-Code: US\'',
            '',
            'Example Response:',
            '',
            '.. code-block:: json',
            '',
            '   {',
            '     "bar": 2,',
            '     "foo": 1',
            '   }',
        ])

    def test_get_example_lines_text(self):
        """Tests an example when the response is *not* valid JSON."""
        lines = base.get_example_lines({}, 'GET', 'http://example.com/', {},
                                       'hello, world!')
        self.assertEqual(lines, [
            '',
            'Example Request:',
            '',
            '.. code-block:: bash',
            '',
            '   curl http://example.com/ -X GET',
            '',
            'Example Response:',
            '',
            '.. code-block:: text',
            '',
            '   hello, world!',
        ])

    def test_get_json_object_lines_for_request_with_enum(self):
        def mock_logic(auth: Auth, is_alive: IsAlive, name: Name=None,
                       color: Color='blue'):
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        annotation = ResourceAnnotation(mock_logic, 'GET')
        parameters = annotation.logic._doctor_signature.parameters
        properties = {k: p.annotation for k, p in parameters.items()}
        result = base.get_json_object_lines(
            annotation, properties, field='>json', url_params=[],
            request=True)
        assert result == [
            ':>json str auth: **Required**.  auth token',
            ':>json bool is_alive: **Required**.  Is alive?',
            ":>json str color: Color Must be one of: `['blue', 'green']`.",
            ':>json str name: name']

    def test_get_json_object_lines_for_request(self):
        """
        This tests that when the request kwarg is True that any
        required params have the description prefixed with
        **Required** and sorted in alphabetical order, followed by
        any optional parameters in alpabetical order.
        """
        def mock_logic(auth: Auth, age: Age, is_deleted: IsDeleted=True):
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        annotation = ResourceAnnotation(mock_logic, 'GET')
        parameters = annotation.logic._doctor_signature.parameters
        properties = {k: p.annotation for k, p in parameters.items()}
        url_params = ['age']
        result = base.get_json_object_lines(
            annotation, properties, field='>json', url_params=url_params,
            request=True)
        self.assertEqual(result, [
            ':param int age: **Required**.  age',
            ':>json str auth: **Required**.  auth token',
            (':>json bool is_deleted: Indicates if the item should be marked '
             'as deleted'),
        ])

    def test_get_json_object_lines_object_response(self):
        """
        This tests that when our response is an object that we return
        all of it's documented properties.
        """
        def mock_logic() -> ExampleObject:
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        annotation = ResourceAnnotation(mock_logic, 'GET')
        result = base.get_json_lines(
            annotation, field='>json', route='/foo', request=False)
        expected = [
            ':>json str str: auth token'
        ]
        self.assertEqual(expected, result)

    def test_get_json_lines_array_response(self):
        """
        Verifies we document properties of an array of objects.
        """
        def mock_logic() -> ExampleObjects:
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        annotation = ResourceAnnotation(mock_logic, 'GET')
        result = base.get_json_lines(
            annotation, field='<json', route='/foo')
        self.assertEqual(result, [':<jsonarr str str: auth token'])

    def test_get_name(self):
        mock_class = mock.Mock()
        mock_class.__module__ = 'foo.bar'
        mock_class.__name__ = 'baz'
        self.assertEqual(base.get_name(mock_class), 'foo.bar.baz')
        mock_class.__module__ = '__builtin__'
        self.assertEqual(base.get_name(mock_class), 'baz')


class TestDocsBaseHarness(TestCase):

    def test_init(self):
        harness = base.BaseHarness('http://foo/')
        self.assertEqual(harness.url_prefix, 'http://foo')

    def test_get_annotation_heading_doctor_heading(self):
        """
        This test verifies we use the _doctor_heading attribute of the
        handler if it is present.
        """
        handler = mock.Mock(_doctor_heading='Test Title')
        route = '^foo/?$'
        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)
        self.assertEqual('Test Title', actual)

    def test_get_annotation_heading_class_path(self):
        """
        This test verifies if the class path has a resource name in it,
        that we use it for the heading.
        e.g. class <api.handlers.foo_bar.FooListHandler> becomes `Foo Bar`
        """
        handler = mock.Mock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class api.foo_bar.FooBarListHandler>')
        route = '^foo_bar/?$'
        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar'
        self.assertEqual(expected, actual)

    def test_get_annotation_heading_generic_handlers(self):
        """
        This test verifies if our handlers are not in their own resource
        modules that we get the heading from the handler class name.
        e.g. class <api.handlers.handlers.FooBarListHandler> becomes `Foo Bar`
        """
        handler = mock.Mock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class api.handlers.FooBarListHandler>')
        route = '^foo_bar/?$'

        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar'
        self.assertEqual(expected, actual)

    def test_get_annotation_heading_class_name_only(self):
        """
        This test verifies that if our handler has no path and is just
        the class name that we get the heading from the name.
        e.g. class <FooBarListHandler> becomes `Foo Bar`
        """
        handler = mock.Mock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class FooBarListHandler>')
        route = '^foo_bar/?$'

        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar'
        self.assertEqual(expected, actual)

    def test_get_annotation_heading_class_path_internal(self):
        """
        This test verifies the path where the class path has the resource
        name in it and it's an internal route.
        """
        handler = mock.Mock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class api.foo_bar.InternalFooBarListHandler>')
        route = '^internal/r/foo_bar/?$'
        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar (Internal)'
        self.assertEqual(expected, actual)

    @mock.patch('doctor.docs.base.hasattr')
    def test_get_annotation_heading_class_name_only_internal(self, mock_has):
        """
        This test verifies the path where our handler has no path and just
        the class name and that class is internal.
        """
        mock_has.return_value = False
        handler = mock.MagicMock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class InternalFooBarListHandler>')
        route = '^/internal/foo_bar/?$'

        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar (Internal)'
        self.assertEqual(expected, actual)

    def test_get_example_values_get_http_method_with_list_and_dict_vals(self):
        """
        This test verifies if the route we are generating example values for
        is a GET endpoint and the example values are lists or dicts, that we
        json.dumps them when they are returned.  If the HTTP method is any
        other method, they will be returned as normal lists or dicts.
        """
        def mock_logic(e: ExampleArray, f: ExampleObject):
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        route = Rule('/foo/bar/')

        annotation = ResourceAnnotation(mock_logic, 'GET')
        harness = base.BaseHarness('http://foo/bar/')
        example_values = harness._get_example_values(route, annotation)
        expected = {
            'e': json.dumps(['ex', 'array']),
            'f': json.dumps({'str': 'ex str'}),
        }
        self.assertEqual(expected, example_values)

        # Change the http method to something other than GET, they should
        # not be json dumped.
        annotation.http_method = 'POST'
        example_values = harness._get_example_values(route, annotation)
        expected = {
            'e': ['ex', 'array'],
            'f': {'str': 'ex str'},
        }
        self.assertEqual(expected, example_values)
