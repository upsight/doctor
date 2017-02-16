from doctor.docs.base import BaseHarness
from doctor.resource import ResourceSchema, ResourceSchemaAnnotation

from .base import TestCase


class BaseHarnessTestCase(TestCase):

    def setUp(self):
        super(BaseHarnessTestCase, self).setUp()
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
                    'anyOf': [
                        {'$ref': '#/definitions/a'},
                        {'$ref': '#/definitions/c'},
                    ],
                }
            },
        })

        self.request_schema = self.schema._create_request_schema(
            params=('a', 'b', 'c', 'd'), required=('a', 'b'))

        def mock_logic():
            pass
        mock_logic.required_args = ['a', 'c']
        self.annotation = ResourceSchemaAnnotation(
            logic=mock_logic, http_method='GET', schema=self.schema,
            request_schema=self.request_schema, response_schema=None)

    def test_get_example_lines_texts_with_oneof(self):
        """
        This test verifies that if a defintion is an anyOf/oneOf that we
        resolve it in order to get the example value.  In this test the param
        `d` can be anyOf `a` or `b`.  The logic always uses the first value,
        so we expect the example value for `d` to be the same as `a`.
        """
        harness = BaseHarness('/api')
        route = '/foo'
        actual = harness._get_example_values(route, self.annotation)
        expected = {
            'a': 'example string',
            'b': 123,
            'c': True,
            'd': 'example string',
        }
        self.assertEqual(expected, actual)
