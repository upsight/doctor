"""
This module provides Sphinx directives to generate documentation for Flask
resources which have been annotated with schema information. It is broken into
a separate module so that Flask applications using doctor for
validation don't need to include Sphinx in their runtime dependencies.
"""

from __future__ import absolute_import

import json
from collections import defaultdict
from urllib import parse

from ..resource import ResourceAnnotation
from ..utils import get_module_attr
from .base import BaseDirective, BaseHarness, HTTP_METHODS


class AutoFlaskDirective(BaseDirective):

    """Sphinx directive to document schema annotated Flask resources."""

    directive_name = 'autoflask'


class AutoFlaskHarness(BaseHarness):

    def __init__(self, app_module_filename, url_prefix):
        super(AutoFlaskHarness, self).__init__(url_prefix)
        self.app_module_filename = app_module_filename

    def __getstate__(self):  # pragma: no cover
        state = self.__dict__.copy()
        del state['app']
        del state['test_client']
        return state

    def __setstate__(self, state):  # pragma: no cover
        self.__dict__.update(state)

    def iter_annotations(self):
        """Yield a tuple for each Flask handler containing annotated methods.

        Each tuple contains a heading, routing rule, the view class associated
        with the rule, and the annotations for the methods in that class.
        """
        # Need to store a list of route, view_class, and annotations by a
        # section key so that all methods of a resource are kept together in
        # the documentation.  The key of the section will be the heading that
        # the route documentation goes under.
        section_map = defaultdict(list)
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint == 'static':
                # Don't document static file endpoints.
                continue
            # This gives us the auto-generated view function.
            view_function = self.app.view_functions.get(rule.endpoint)
            if view_function is None:
                continue
            # This gives us the actual Flask resource class.
            view_class = getattr(view_function, 'view_class', None)
            if view_class is None:
                continue

            annotations = []
            for method_name in HTTP_METHODS:
                method = getattr(view_class, method_name, None)
                if not method:
                    continue
                annotation = ResourceAnnotation(
                    method, method_name, method._doctor_title)
                annotations.append(annotation)
            if annotations:
                heading = self._get_annotation_heading(view_class, str(rule))
                section_map[heading].append((rule, view_class, annotations))

        # Loop through each heading and it's items and yield the values.
        for heading in sorted(section_map.keys()):
            for item in section_map[heading]:
                rule, view_class, annotations = item
                yield (heading, rule, view_class, annotations)

    def request(self, rule, view_class, annotation):
        """Make a request against the app.

        This attempts to use the schema to replace any url params in the path
        pattern. If there are any unused parameters in the schema, after
        substituting the ones in the path, they will be sent as query string
        parameters or form parameters. The substituted values are taken from
        the "example" value in the schema.

        Returns a dict with the following keys:

        - **url** -- Example URL, with url_prefix added to the path pattern,
          and the example values substituted in for URL params.
        - **method** -- HTTP request method (e.g. "GET").
        - **params** -- A dictionary of query string or form parameters.
        - **response** -- The text response to the request.

        :param route: Werkzeug Route object.
        :param view_class: View class for the annotated method.
        :param annotation: Annotation for the method to be requested.
        :type annotation: doctor.resource.ResourceAnnotation
        :returns: dict
        """
        headers = self._get_headers(rule, annotation)
        example_values = self._get_example_values(rule, annotation)
        # If any of the example values for DELETE/GET HTTP methods are dicts
        # or lists, we will need to json dump them before building the rule,
        # otherwise the query string parameter won't get parsed correctly
        # by doctor.
        if annotation.http_method.upper() in ('DELETE', 'GET'):
            for key, value in list(example_values.items()):
                if isinstance(value, (dict, list)):
                    example_values[key] = json.dumps(value)
        _, path = rule.build(example_values, append_unknown=True)
        if annotation.http_method.upper() not in ('DELETE', 'GET'):
            parsed_path = parse.urlparse(path)
            path = parsed_path.path
            params = example_values
        else:
            params = {}
        method_name = annotation.http_method.lower()
        method = getattr(self.test_client, method_name)
        if method_name in ('post', 'put'):
            response = method(path, data=json.dumps(params), headers=headers,
                              content_type='application/json')
        else:
            response = method(path, data=params, headers=headers)
        return {
            'url': '/'.join([self.url_prefix, path.lstrip('/')]),
            'method': annotation.http_method.upper(),
            'params': params,
            'response': response.data,
        }

    def setup_app(self, sphinx_app):
        self.app = get_module_attr(self.app_module_filename, 'app', {})
        self.test_client = self.app.test_client()


def setup(app):  # pragma: no cover
    """This setup function is called by Sphinx."""
    AutoFlaskDirective.setup(app)
