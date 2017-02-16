import copy
import json
import os

import mock

from doctor.docs.flask import AutoFlaskHarness
from doctor.resource import ResourceSchemaAnnotation
from .base import TestCase


class TestDocsFlask(TestCase):

    def setUp(self):
        flask_folder = os.path.join(os.path.dirname(__file__), '..',
                                    'examples', 'flask')
        self.harness = AutoFlaskHarness(os.path.join(flask_folder, 'app.py'),
                                        'http://127.0.0.1/')
        self.harness.setup_app(mock.sentinel.sphinx_app)
        self.annotations = list(self.harness.iter_annotations())

    def tearDown(self):
        self.harness.teardown_app(mock.sentinel.sphinx_app)

    def test_harness_iter_annotations(self):
        self.assertEqual(len(self.annotations), 3)

        heading, rule, view_class, annotations = self.annotations[0]
        self.assertEqual(heading, 'API Status')
        self.assertEqual(rule.rule, '/')
        self.assertEqual([annotation.http_method for annotation in annotations],
                         ['GET'])

        heading, rule, view_class, annotations = self.annotations[1]
        self.assertEqual(heading, 'Notes (v1)')
        self.assertEqual(rule.rule, '/note/')
        self.assertEqual([annotation.http_method for annotation in annotations],
                         ['GET', 'POST'])

        heading, rule, view_class, annotations = self.annotations[2]
        self.assertEqual(heading, 'Notes (v1)')
        self.assertEqual(rule.rule, '/note/<int:note_id>/')
        self.assertEqual([annotation.http_method for annotation in annotations],
                         ['GET', 'PUT', 'DELETE'])

    def test_harness_request_get(self):
        _, rule, view_class, annotations = self.annotations[2]
        annotation = annotations[0]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'GET',
            'params': {},
            'response': {'body': 'Example body',
                         'done': False,
                         'note_id': 1},
            'url': 'http://127.0.0.1/note/1/'})

    def test_harness_request_get_query_string(self):
        _, rule, view_class, annotations = self.annotations[2]
        annotation = annotations[0]
        request_schema = copy.deepcopy(annotation.request_schema.copy())
        request_schema['properties']['fake_param'] = {
            'type': 'string',
            'description': 'This is a fake param',
            'example': 'fake value',
        }
        annotation = ResourceSchemaAnnotation(
            annotation.logic, annotation.http_method, annotation.schema,
            request_schema, annotation.response_schema)
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'GET',
            'params': {},
            'response': {'body': 'Example body',
                         'done': False,
                         'note_id': 1},
            'url': 'http://127.0.0.1/note/1/?fake_param=fake+value'})

    def test_harness_request_get_list_and_dict_params(self):
        """
        This test verifies that we json dumps object and array types when
        building the url's query string parameters if this is a GET request.
        """
        _, rule, view_class, annotations = self.annotations[2]
        annotation = annotations[0]
        request_schema = copy.deepcopy(annotation.request_schema.copy())
        request_schema['properties']['array_param'] = {
            'items': {
                'type': 'string',
            },
            'type': 'array',
            'description': 'This is a list',
            'example': [1],
        }
        request_schema['properties']['object_param'] = {
            'properties': {
                'foo': {
                    'type': 'string',
                    'description': 'A string',
                    'example': 'bar',
                },
            },
            'type': 'object',
            'description': 'This is a dict',
            'example': {
                'foo': 'bar'
            },
        }
        annotation = ResourceSchemaAnnotation(
            annotation.logic, annotation.http_method, annotation.schema,
            request_schema, annotation.response_schema)
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        expected = {

            'method': 'GET',
            'params': {},
            'response': {
                'body': 'Example body',
                'done': False,
                'note_id': 1
            },
            'url': ('http://127.0.0.1/note/1/?array_param=%5B1%5D&'
                    'object_param=%7B%22foo%22%3A+%22bar%22%7D')
        }
        self.assertEqual(expected, result)

    def test_harness_request_post(self):
        _, rule, view_class, annotations = self.annotations[1]
        annotation = annotations[1]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'POST',
            'params': {'body': 'This is an example note.',
                       'done': True},
            'response': {'body': 'This is an example note.',
                         'done': True,
                         'note_id': 2},
            'url': 'http://127.0.0.1/note/'})

    def test_harness_request_delete(self):
        response_mock = mock.Mock(data='')
        self.harness.test_client.delete = mock.Mock(return_value=response_mock)
        _, rule, view_class, annotations = self.annotations[2]
        annotation = annotations[2]
        result = self.harness.request(rule, view_class, annotation)

        expected_url = '/note/1/'
        self.harness.test_client.delete.assert_called_with(
            expected_url, data={}, headers={})
        expected_result = {
            'url': 'http://127.0.0.1/note/1/',
            'params': {},
            'method': 'DELETE',
            'response': ''
        }
        self.assertEqual(expected_result, result)

    def test_harness_define_example_values(self):
        _, rule, view_class, annotations = self.annotations[1]
        annotation = annotations[1]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'POST',
            'params': {'body': 'This is an example note.',
                       'done': True},
            'response': {'body': 'This is an example note.',
                         'done': True,
                         'note_id': 2},
            'url': 'http://127.0.0.1/note/'})

        # Now override the values and validate that they're different
        self.harness.define_example_values('POST', '/note/', {
            'body': 'This is a replaced body.'
        })
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result['params'], {'body': 'This is a replaced body.'})

        # Override, but with update=True, which should merge the values
        self.harness.define_example_values('POST', '/note/', {
            'body': 'This is an updated body.'
        }, update=True)
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result['params'], {'body': 'This is an updated body.',
                                            'done': True})
