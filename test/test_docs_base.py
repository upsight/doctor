import json

import mock
from werkzeug.routing import Rule

from doctor.docs import base
from doctor.resource import ResourceAnnotation
from doctor.response import Response

from .base import TestCase
from .types import (
    Age, AgeOrColor, Auth, Color, Colors, ExampleArray, ExampleObject,
    ExampleObjects, ExampleObjectsAndAge, FooInstance, IsAlive, IsDeleted, Name,
    TwoItems)
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
        assert lines == [
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
        ]

    def test_get_example_lines_text(self):
        """Tests an example when the response is *not* valid JSON."""
        lines = base.get_example_lines({}, 'GET', 'http://example.com/', {},
                                       'hello, world!')
        assert lines == [
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
        ]

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
        assert result == [
            ':param int age: **Required**.  age',
            ':>json str auth: **Required**.  auth token',
            (':>json bool is_deleted: Indicates if the item should be marked '
             'as deleted'),
        ]

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
        assert expected == result

    def test_get_json_lines_logic_defines_req_obj_type(self):
        """
        This tests that we properly generate the json params for a request
        when the logic function defines a `req_obj_type`.
        """
        def mock_logic(foo: FooInstance):
            pass

        mock_logic = add_doctor_attrs(mock_logic, req_obj_type=FooInstance)
        annotation = ResourceAnnotation(mock_logic, 'POST')
        result = base.get_json_lines(
            annotation, field='<json', route='/foo', request=True)
        expected = [
            ':<json int foo_id: **Required**.  foo id',
            ':<json str foo: foo'
        ]
        assert expected == result

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
        assert result == [':<jsonarr str str: auth token']

    def test_get_json_lines_response_response(self):
        """
        Verifies when our response is a doctor.response.Response instance
        and it has a type associated with it that we use that type to
        document it.
        """
        def mock_logic() -> Response[ExampleObject]:
            pass

        mock_logic = add_doctor_attrs(mock_logic)
        annotation = ResourceAnnotation(mock_logic, 'GET')
        result = base.get_json_lines(
            annotation, field='>json', route='/foo', request=False)
        expected = [
            ':>json str str: auth token'
        ]
        assert expected == result

    def test_get_name(self):
        mock_class = mock.Mock()
        mock_class.__module__ = 'foo.bar'
        mock_class.__name__ = 'baz'
        assert base.get_name(mock_class) == 'foo.bar.baz'
        mock_class.__module__ = '__builtin__'
        assert base.get_name(mock_class) == 'baz'


class TestDocsBaseHarness(TestCase):

    def test_init(self):
        harness = base.BaseHarness('http://foo/')
        assert harness.url_prefix == 'http://foo'

    def test_get_annotation_heading_doctor_heading(self):
        """
        This test verifies we use the _doctor_heading attribute of the
        handler if it is present.
        """
        handler = mock.Mock(_doctor_heading='Test Title')
        route = '^foo/?$'
        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)
        assert 'Test Title' == actual

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
        assert expected == actual

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
        assert expected == actual

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
        assert expected == actual

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
        assert expected == actual

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
        assert expected == actual

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
        assert expected == example_values

        # Change the http method to something other than GET, they should
        # not be json dumped.
        annotation.http_method = 'POST'
        example_values = harness._get_example_values(route, annotation)
        expected = {
            'e': ['ex', 'array'],
            'f': {'str': 'ex str'},
        }
        assert expected == example_values

    def test_get_example_values_when_logic_defines_req_obj_type(self):
        """
        This tests that we generate example values appropriately when the
        route defineds a req_obj_type which will pass all request params as
        that object instance to the logic function.

        If a req_obj_type was not defined for the logic, it would expect
        the json body to look like:

        {
            "foo": {
                "foo": "foo",
                "foo_id": 1
            }
        }

        Defining a req_obj_type tells the code that the request body should
        contain those attributes rather than a sub-key within the request.
        """
        def mock_logic(foo: FooInstance):
            pass

        mock_logic = add_doctor_attrs(mock_logic, req_obj_type=FooInstance)
        route = Rule('/foo/bar/')

        annotation = ResourceAnnotation(mock_logic, 'POST')
        harness = base.BaseHarness('http://foo/bar/')
        example_values = harness._get_example_values(route, annotation)
        expected = {
            'foo': 'foo',
            'foo_id': 1,
        }
        assert expected == example_values

    def test_class_name_to_resource_name(self):
        tests = (
            # (input, expected)
            ('Foo', 'Foo'),
            ('FooBar', 'Foo Bar'),
            ('FooV1Bar', 'Foo V1 Bar'),
            ('Reallylongnamewithnoothercase', 'Reallylongnamewithnoothercase'),
            ('HTTPResponse', 'HTTP Response'),
        )
        for arg, expected in tests:
            assert expected == base.class_name_to_resource_name(arg)

    @mock.patch.dict('doctor.docs.base.ALL_RESOURCES',
                     {'An Object': ExampleObject})
    def test_get_resource_object_doc_lines(self):
        actual = base.get_resource_object_doc_lines()
        expected = [
            'Resource Objects',
            '----------------',
            '.. _resource-an-object:',
            '',
            'An Object',
            '#########',
            'ex description f',
            '',
            'Attributes',
            '**********',
            '* **str** (*str*) - auth token',
            '',
            'Example',
            '*******',
            '.. code-block:: json',
            '',
            '   {',
            '       "str": "ex str"',
            '   }'
        ]
        assert expected == actual

    @mock.patch.dict('doctor.docs.base.ALL_RESOURCES', {})
    def test_get_resource_object_doc_lines_no_resources(self):
        """
        This test verifies if we have no resources to document, we don't
        attempt to do it anyway which would result in a header w/ no content
        below it.
        """
        assert [] == base.get_resource_object_doc_lines()

    @mock.patch.dict('doctor.docs.base.ALL_RESOURCES', {})
    def test_get_object_reference(self):
        actual = base.get_object_reference(ExampleObject)
        expected = ' See :ref:`resource-example-object`.'
        assert expected == actual

        # also verify it was added to `ALL_RESOURCES`.
        assert {'Example Object': ExampleObject} == base.ALL_RESOURCES

    def test_get_json_types(self):
        assert ['int'] == base.get_json_types(Age)
        assert ['list[str]'] == base.get_json_types(Colors)
        assert ['list[int,str]'] == base.get_json_types(TwoItems)
        assert ['int', 'str'] == base.get_json_types(AgeOrColor)

    @mock.patch.dict('doctor.docs.base.ALL_RESOURCES', {})
    def test_get_array_description(self):
        actual = base.get_array_items_description(Colors)
        expected = (
            "  *Items must be*: Color Must be one of: `['blue', 'green']`.")
        assert expected == actual

        actual = base.get_array_items_description(TwoItems)
        expected = (" *Item 0 must be*: age *Item 1 must be*: Color Must be "
                    "one of: `['blue', 'green']`.")
        assert expected == actual

        actual = base.get_array_items_description(ExampleObjectsAndAge)
        expected = (" *Item 0 must be*: age *Item 1 must be*: ex description "
                    "f See :ref:`resource-example-object`.")
        assert expected == actual

        actual = base.get_array_items_description(ExampleObjects)
        expected = ('  *Items must be*: ex description f See '
                    ':ref:`resource-example-object`.')
        assert expected == actual
