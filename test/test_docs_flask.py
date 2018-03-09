import json
import os

import mock

from doctor.docs.flask import AutoFlaskHarness

from .base import TestCase


class TestDocsFlask(TestCase):

    def setUp(self):
        flask_folder = os.path.join(os.path.dirname(__file__))
        self.harness = AutoFlaskHarness(
            os.path.join(flask_folder, 'flask_app.py'), 'http://127.0.0.1/')
        self.harness.setup_app(mock.sentinel.sphinx_app)
        self.annotations = list(self.harness.iter_annotations())

    def tearDown(self):
        self.harness.teardown_app(mock.sentinel.sphinx_app)

    def test_harness_iter_annotations(self):
        self.assertEqual(len(self.annotations), 4)

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

        heading, rule, view_class, annotations = self.annotations[3]
        assert 'Z' == heading
        assert '/example/list-obj/' == rule.rule
        assert ['GET'] == [annotation.http_method for annotation in annotations]

    def test_harness_request_get_query_string(self):
        _, rule, view_class, annotations = self.annotations[2]
        annotation = annotations[0]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'GET',
            'params': {},
            'response': {'body': 'Example body',
                         'done': True,
                         'note_id': 1},
            'url': 'http://127.0.0.1/note/1/?note_type=quick'})

    def test_harness_request_get_list_and_dict_params(self):
        """
        This test verifies that we json dumps object and array types when
        building the url's query string parameters if this is a GET request.
        """
        _, rule, view_class, annotations = self.annotations[3]
        annotation = annotations[0]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        expected = {

            'method': 'GET',
            'params': {},
            'response': {},
            'url': ('http://127.0.0.1/example/list-obj/?note_types=%5B%22quick'
                    '%22%5D&a_note=%7B%22body%22%3A+%22Example+Body%22%2C+%22'
                    'done%22%3A+true%2C+%22note_id%22%3A+1%7D')
        }
        self.assertEqual(expected, result)

    def test_harness_request_post(self):
        _, rule, view_class, annotations = self.annotations[1]
        annotation = annotations[1]
        result = self.harness.request(rule, view_class, annotation)
        result['response'] = json.loads(result['response'])
        self.assertEqual(result, {
            'method': 'POST',
            'params': {'body': 'body',
                       'done': False},
            'response': {'body': 'body',
                         'done': False,
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
            'params': {'body': 'body',
                       'done': False},
            'response': {'body': 'body',
                         'done': False,
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
                                            'done': False})
