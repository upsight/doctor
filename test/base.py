import os
import unittest

import flask_restful
import flask_testing
from doctor.flask import FlaskResourceSchema, FlaskRouter
from flask import Flask


class TestCase(unittest.TestCase):

    maxDiff = None

    def shortDescription(self):
        # Do not show first line of the docstring as a test description
        return None


class FlaskTestCase(flask_testing.TestCase):

    """
    This test case base class is used for integration tests with flask
    and doctor.
    """

    #: Displays the full diff on failure.
    maxDiff = None

    def shortDescription(self):
        # Do not show first line of the docstring as a test description
        return None

    def get_routes(self):
        """Gets the routes for the app.

        This should return a tuple of tuples.  Each tuple contains the
        route as a string and the instnace of a resource to route to.  e.g.

        (
            ('/some/url/', doctor.router.Handler1),
        )

        This method can be overridden in subclasses to change the routes and
        add new ones.

        :returns: The tuple described above.
        """
        def logic_func(annotation_id, url=None):
            return (annotation_id, url)

        schema_dir = os.path.join(os.path.dirname(__file__), 'schema')
        router = FlaskRouter(schema_dir, FlaskResourceSchema)
        return router.create_routes('Test', 'annotation.yaml', {
            '/test/': {
                'get': {
                    'logic': logic_func,
                },
            },
        })

    def create_app(self):
        """This method creates the flask app.

        This is required to be implemented by flask_restful.

        :returns: Flask application instance.
        """
        app = Flask('test')
        app.config['TESTING'] = True

        api = flask_restful.Api(app)
        for url, handler in self.get_routes():
            api.add_resource(handler, url)

        return api.app
