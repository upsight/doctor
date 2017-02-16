import json

import mock
from sphinx.errors import SphinxError

from doctor.docs import base
from doctor.errors import SchemaError
from doctor.resource import ResourceSchema, ResourceSchemaAnnotation
from .base import TestCase


class TestDocsBase(TestCase):

    def setUp(self):
        super(TestDocsBase, self).setUp()
        self.schema = ResourceSchema({
            'definitions': {
                'a': {
                    'type': 'string',
                    'description': 'example description for a',
                    'example': 'example string',
                },
                'b': {
                    'type': 'integer',
                    'description': 'example description for b',
                    'example': 123,
                },
                'c': {
                    'type': 'boolean',
                    'description': 'example description for c',
                    'example': True,
                },
                'd': {
                    'type': ['integer', 'null'],
                    'description': 'example description for d',
                    'example': 456,
                },
                'e': {
                    'type': ['array'],
                    'description': 'example description for e',
                    'example': ['example', 'array'],
                },
                'f': {
                    'type': 'object',
                    'description': 'example description for f',
                    'properties': {
                        'str': {
                            'type': 'string',
                            'description': 'A string',
                            'example': 'A String',
                        },
                    },
                    'example': {'str': 'example string'},
                },
                'g': {
                    'type': 'string',
                    'description': 'example description for g',
                    'example': {
                        'oneOf': [
                            'example string 1',
                            'example string 2',
                        ],
                    },
                },
                'h': {
                    'type': ['null'],
                    'description': 'example description for h',
                    'example': None
                },
                'i': {
                    'type': 'array',
                    'description': 'example description for i',
                    'items': {
                        '$ref': '#/definitions/b',
                    },
                },
                # An example with an array of objects with no example
                # key on the object.
                'j': {
                    'type': 'array',
                    'description': 'An array of objects',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'str': {
                                'type': 'string',
                                'description': 'A String',
                                'example': 'string',
                            },
                            'int': {
                                'type': 'integer',
                                'description': 'An integer',
                                'example': 1022,
                            },
                        },
                        'additionalProperties': False,
                    },
                },
                'k': {
                    'type': 'string',
                    'description': 'The type of shirt.',
                    'enum': ['tshirt', 'sweater'],
                    'example': 'tshirt',
                },
                # An object w/o any properties.
                'l': {
                    'type': 'object',
                    'description': 'An object that can have any properties',
                    'example': {
                        'foo': 'bar',
                    },
                },
                # An object with a property that is a reference we can't resolve
                'm': {
                    'type': 'object',
                    'description': 'An object with a propertery that is a ref',
                    'example': {
                        'hey': 'ref',
                    },
                    'properties': {
                        'hey': {
                            '$ref': 'dinosaurs.yaml#/definitions/trex',
                        },
                    },
                },
                # An object with a property to document whose type is an
                # array, rather than a single item string.
                'n': {
                    'type': ['null', 'object'],
                    'description': 'example description for n',
                    'properties': {
                        'str': {
                            'type': 'string',
                            'description': 'A string',
                            'example': 'A String',
                        },
                    },
                    'example': {'str': 'example string `n`'},
                },
            },
        })
        self.request_schema = self.schema._create_request_schema(
            params=('a', 'b', 'c'), required=('a', 'b'))
        self.response_schema = {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'b': {'$ref': '#/definitions/b'},
                    'c': {'$ref': '#/definitions/c'},
                },
            },
        }

        def mock_logic():
            pass
        mock_logic.required_args = ['a', 'c']

        self.annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema,
            response_schema=self.response_schema)

    def test_get_example_value(self):
        definitions = self.schema.resolve('#/definitions')
        results = [base.get_example_value(prop_schema, self.schema, key)
                   for key, prop_schema in sorted(definitions.iteritems())]
        expected = [
            'example string',
            123,
            True,
            456,
            ['example', 'array'],
            {'str': 'example string'},
            'example string 1',
            None,
            [123],
            [{'str': 'string', 'int': 1022}],
            'tshirt',
            {'foo': 'bar'},
            {'hey': 'ref'},
            {'str': 'example string `n`'},
        ]
        self.assertEqual(expected, results)

    def test_get_example_for_object(self):
        """
        This test verifies we can get an example for an object that is
        missing an example from normal properties.
        """
        schema = {
            'definitions': {
                'a': {
                    'type': 'object',
                    'properties': {
                        'foo': {
                            'type': 'string',
                            'description': 'A foo',
                            'example': 'Foo!',
                        },
                    },
                    'additionalProperties': False,
                },
            },
        }
        schema = ResourceSchema(schema)
        definitions = schema.resolve('#/definitions')
        result = base.get_example_for_object(definitions['a'], schema)
        expected = {'foo': 'Foo!'}
        self.assertEqual(expected, result)

    def test_get_example_for_object_with_different_schema(self):
        """
        This test verifies if the object_schema is a different file than the
        schema argument, that we create a new ResourceSchema instance from
        the object schema in order to resolve example values.
        """
        schema = ResourceSchema({
            'definitions': {
                'a': {
                    'type': 'object',
                    'properties': {
                        'foo': {
                            'type': 'string',
                            'description': 'A foo',
                            'example': 'Foo!',
                        },
                    },
                    'additionalProperties': False,
                },
            },
        })
        object_schema = {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'title': 'Another type of schema',
            'description': 'A description',
            'definitions': {
                'interesting_thing': {
                    'type': 'object',
                    'properties': {
                        'cat': {
                            'type': 'string',
                            'description': 'The name of a cat',
                            'example': 'Els',
                        },
                    },
                },
                'interesting_things': {
                    'type': 'array',
                    'description': 'an array of intersting things',
                    'items': {
                        '$ref': '#/definitions/interesting_thing',
                    },
                }
            },
            'type': 'object',
            'properties': {
                'interesting_things': {
                    '$ref': '#/definitions/interesting_things',
                },
            }
        }
        actual = base.get_example_for_object(object_schema, schema)
        expected = {'interesting_things': [{'cat': 'Els'}]}
        self.assertEqual(expected, actual)

    def test_get_example_value_anyof(self):
        """
        This test verifies that if a property has an anyOf declaration for the
        example, that we first resolve the anyOf by grabbing the first
        defintion in it's list.
        """
        property_schema = {
            'anyOf': [
                {'$ref': '#/definitions/b'},
                {'$ref': '#/definitions/c'}
            ]
        }
        actual = base.get_example_value(property_schema, self.schema, 'type')
        # expected value should be the example from definitions/b
        expected = 123
        self.assertEqual(expected, actual)

    def test_get_example_reraises_with_key(self):
        """
        This test verifies we re-raise the SchemaError with the offending key.
        """
        property_schema = {
            'type': 'integer',
            'description': 'An integer and we are missing the example'
        }
        with self.assertRaises(SchemaError) as cm:
            base.get_example_value(property_schema, self.schema, 'foobar')
        expected = ("Error resolving #example from {'type': 'integer', "
                    "'description': 'An integer and we are missing the "
                    "example'} for property `foobar`. Unresolvable JSON "
                    "pointer: u'example' (from )")
        self.assertEqual(expected, cm.exception.message)

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

    def test_get_json_object_lines(self):
        result = base.get_json_object_lines(
            self.annotation, self.request_schema, field='>json', url_params=[])
        self.assertEqual(result, [
            ':>json str a: example description for a',
            ':>json int b: example description for b',
            ':>json bool c: example description for c',
        ])

    def test_get_json_object_lines_for_request_with_enum(self):
        request_schema = self.schema._create_request_schema(
            params=('a', 'b', 'c', 'k'), required=('a', 'b'))
        result = base.get_json_object_lines(
            self.annotation, request_schema, field='>json', url_params=[],
            request=True)
        self.assertEqual(result, [
            ':>json str a: **Required**.  example description for a',
            ':>json bool c: **Required**.  example description for c',
            ':>json int b: example description for b',
            (":>json str k: The type of shirt. Must be one of: "
             "`['tshirt', 'sweater']`."),
        ])

    def test_get_json_object_lines_for_request(self):
        """
        This tests that when the request kwarg is True that any
        required params have the description prefixed with
        **Required** and sorted in alphabetical order, followed by
        any optional parameters in alpabetical order.
        """
        url_params = ['a']
        result = base.get_json_object_lines(
            self.annotation, self.request_schema, field='>json',
            url_params=url_params, request=True)
        self.assertEqual(result, [
            ':param str a: **Required**.  example description for a',
            ':>json bool c: **Required**.  example description for c',
            ':>json int b: example description for b',
        ])

    def test_get_json_object_lines_object(self):
        def mock_logic():
            pass
        mock_logic.required_args = ['f']
        request_schema = self.schema._create_request_schema(
            params=('f',), required=('f',))
        annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema,
            response_schema=self.response_schema)
        result = base.get_json_schema_lines(
            annotation, request_schema, field='>json', route='/foo')
        expected = [
            ':>json dict f|object: example description for f',
            ':>json str str|objectproperty: A string'
        ]
        self.assertEqual(expected, result)

    def test_get_json_object_lines_object_type_is_array(self):
        """
        This test verifies if a definition has a type of array and one of the
        types is an object that we still docuemnt the properties of the object.
        This is a regression test where we used to only document object
        properties if the type was a string equal to 'object'.
        """
        def mock_logic():
            pass
        mock_logic.required_args = ['n']
        request_schema = self.schema._create_request_schema(
            params=('n',), required=('n',))
        annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema,
            response_schema=self.response_schema)
        result = base.get_json_schema_lines(
            annotation, request_schema, field='>json', route='/foo')
        expected = [
            ':>json null,dict n|object: example description for n',
            ':>json str str|objectproperty: A string'
        ]
        self.assertEqual(expected, result)

    def test_get_json_object_lines_object_no_properties(self):
        """
        This is a regression test that ensures we don't blow up if we encounter
        an object that doesn't have any defined properties to document.
        """
        def mock_logic():
            pass
        mock_logic.required_args = ['l']
        request_schema = self.schema._create_request_schema(
            params=('l',), required=('l',))
        annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema,
            response_schema=self.response_schema)
        result = base.get_json_schema_lines(
            annotation, request_schema, field='>json', route='/foo')
        expected = [':>json dict l: An object that can have any properties']
        self.assertEqual(expected, result)

    def test_get_json_object_lines_object_property_is_a_ref(self):
        """
        This is a regression test that ensures we don't blow up if we encounter
        an object that has a property that can't be resolved.
        """
        def mock_logic():
            pass
        mock_logic.required_args = ['m']
        request_schema = self.schema._create_request_schema(
            params=('m',), required=('m',))
        annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema,
            response_schema=self.response_schema)
        result = base.get_json_schema_lines(
            annotation, request_schema, field='>json', route='/foo')
        expected = [':>json dict m: An object with a propertery that is a ref']
        self.assertEqual(expected, result)

    def test_get_json_schema_lines(self):
        result = base.get_json_schema_lines(
            self.annotation, self.request_schema, field='>json', route='/foo')
        self.assertEqual(result, [
            ':>json str a: example description for a',
            ':>json int b: example description for b',
            ':>json bool c: example description for c',
        ])

    def test_get_json_schema_lines_array(self):
        result = base.get_json_schema_lines(
            self.annotation, self.response_schema, field='<json', route='/foo')
        self.assertEqual(result, [
            ':<jsonarr int b: example description for b',
            ':<jsonarr bool c: example description for c',
        ])

    @mock.patch('doctor.docs.base.logging.warn')
    def test_get_json_schema_lines_array_invalid_type(self, mock_warn):
        self.response_schema['items']['type'] = 'string'
        result = base.get_json_schema_lines(
            self.annotation, self.response_schema, field='<json', route='/foo')
        self.assertEqual(result, [])
        self.assertEqual(mock_warn.call_args_list, [
            mock.call('Not documenting list item of type %s (for %s %s)',
                      'string', 'GET', '/foo')])

    @mock.patch('doctor.docs.base.logging.warn')
    def test_get_json_schema_lines_invalid_type(self, mock_warn):
        result = base.get_json_schema_lines(
            self.annotation, {'type': 'string'}, field='<json', route='/foo')
        self.assertEqual(result, [])
        self.assertEqual(mock_warn.call_args_list, [
            mock.call('Not documenting schema of type %s (for %s %s)',
                      'string', 'GET', '/foo')])

    def test_get_name(self):
        mock_class = mock.Mock()
        mock_class.__module__ = 'foo.bar'
        mock_class.__name__ = 'baz'
        self.assertEqual(base.get_name(mock_class), 'foo.bar.baz')
        mock_class.__module__ = '__builtin__'
        self.assertEqual(base.get_name(mock_class), 'baz')

    def test_resolve(self):
        definitions = self.schema.resolve('#/definitions')
        self.assertEqual(base.resolve('#a', definitions, self.annotation),
                         definitions['a'])
        with self.assertRaises(SphinxError):
            base.resolve('#invalid_ref', definitions, self.annotation)

    def test_resolve_with_oneof(self):
        """
        This test verifies that if a oneOf definition hits the resolve
        method, that we first resolve the oneOf by grabbing the first
        defintion in it's list.
        """
        fragment = 'type'
        definitions = {
            'oneOf': [
                {'$ref': '#/definitions/a'},
                {'$ref': '#/definitions/g'}
            ]
        }
        actual = base.resolve(fragment, definitions, self.annotation)

        expected = {
            'type': 'string',
            'description': 'example description for a',
            'example': 'example string',
        }
        self.assertEqual(expected, actual)

    def test_resolve_with_anyof(self):
        """
        This test verifies that if a anyOf definition hits the resolve
        method, that we first resolve the anyOf by grabbing the first
        defintion in it's list.
        """
        fragment = 'type'
        definitions = {
            'anyOf': [
                {'$ref': '#/definitions/b'},
                {'$ref': '#/definitions/c'}
            ]
        }
        actual = base.resolve(fragment, definitions, self.annotation)

        expected = {
            'type': 'integer',
            'description': 'example description for b',
            'example': 123,
        }
        self.assertEqual(expected, actual)

    def test_resolve_of_type(self):
        schema = {
            'oneOf': [
                {'$ref': '#/definitions/a'},
                {'$ref': '#/definitions/g'}
            ]
        }
        actual = base.resolve_of_type(self.annotation, schema)
        expected = {
            'type': 'string',
            'description': 'example description for a',
            'example': 'example string',
        }
        self.assertEqual(expected, actual)


class TestDocsBaseHarness(TestCase):

    def test_init(self):
        harness = base.BaseHarness('http://foo/')
        self.assertEqual(harness.url_prefix, 'http://foo')

    def test_get_annotation_heading_schematic_title(self):
        """
        This test verifies we use the schematic_title attribute of the
        handler if it is present.
        """
        handler = mock.Mock(schematic_title='Test Title')
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

    def test_get_annotation_heading_class_name_only_internal(self):
        """
        This test verifies the path where our handler has no path and just
        the class name and that class is internal.
        """
        handler = mock.Mock(spec_set=base.BaseHarness)
        handler.__str__ = mock.Mock(
            return_value='<class InternalFooBarListHandler>')
        route = '^/internal/foo_bar/?$'

        harness = base.BaseHarness('http://foo/')
        actual = harness._get_annotation_heading(handler, route)

        expected = 'Foo Bar (Internal)'
        self.assertEqual(expected, actual)
