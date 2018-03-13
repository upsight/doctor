"""This module can be used to generate Sphinx documentation for an API."""

from __future__ import absolute_import

import json
import logging
import pipes
import re
from collections import defaultdict
from inspect import Parameter
from typing import Any, Dict, List

try:
    from docutils import nodes
    from docutils.parsers.rst import Directive
    from docutils.statemachine import ViewList
    from sphinx.errors import SphinxError
    from sphinx.util.nodes import nested_parse_with_titles
    from sphinxcontrib.autohttp.common import http_directive
except ImportError:  # pragma: no cover
    raise ImportError('You must install sphinx and sphinxcontrib-httpdomain to '
                      'use the doctor.docs module.')

from doctor.docs.httpdomain import setup as setup_httpdomain
from doctor.errors import SchemaError
from doctor.resource import ResourceAnnotation
from doctor.types import Array, Enum, Object
from doctor.utils import get_description_lines


#: Used to transform a class name into it's various words, splitting on
#: uppercase characters.  So `MyClassName` becomes ['My', 'Class', 'Name']
CAMEL_CASE_RE = re.compile(r'[A-Z][^A-Z]*')

#: Used to get all url parameter names.
URL_PARAMS_RE = re.compile(r'\(([a-zA-Z_]+)\:')

#: These are the HTTP methods that will be documented on handlers.
#:
#: Note that HEAD and OPTIONS aren't included here.
HTTP_METHODS = ('get', 'post', 'put', 'patch', 'delete')

#: Used to map the JSON schema types to more Pythonic types for consistency.
TYPE_MAP = {'array': 'list',
            'boolean': 'bool',
            'integer': 'int',
            'number': 'float',
            'object': 'dict',
            'string': 'str'}

#: Used to list all types that can have multiple items
# Excluded allOf and multipleOf since they require more than one item
OF_TYPES = {'anyOf', 'oneOf'}

# Any line that begins with this text will be transofrmed into a sphinx heading
HEADING_TOKEN = '!!HEADING!!'
HEADING_TOKEN_LENGTH = len(HEADING_TOKEN)


def get_example_curl_lines(method: str, url: str, params: dict,
                           headers: dict) -> List[str]:
    """Render a cURL command for the given request.

    :param str method: HTTP request method (e.g. "GET").
    :param str url: HTTP request URL.
    :param dict params: JSON body, for POST and PUT requests.
    :param dict headers: A dict of HTTP headers.
    :returns: list
    """
    parts = ['curl {}'.format(pipes.quote(url))]
    parts.append('-X {}'.format(method))
    for header in headers:
        parts.append("-H '{}: {}'".format(header, headers[header]))
    if method not in ('DELETE', 'GET'):
        # Don't append a json body if there are no params.
        if params:
            parts.append("-H 'Content-Type: application/json' -d")
            pretty_json = json.dumps(params, separators=(',', ': '), indent=4,
                                     sort_keys=True)
            # add indentation for the closing bracket of the json body
            json_lines = pretty_json.split('\n')
            json_lines[-1] = '   ' + json_lines[-1]
            pretty_json = '\n'.join(json_lines)
            parts.append(pipes.quote(pretty_json))
    wrapped = [parts.pop(0)]
    for part in parts:
        if len(wrapped[-1]) + len(part) < 80:
            wrapped[-1] += ' ' + part
        else:
            wrapped[-1] += ' \\'
            wrapped.append('  ' + part)
    return wrapped


def get_example_lines(headers: Dict[str, str], method: str, url: str,
                      params: Dict[str, Any], response: str) -> List[str]:
    """Render a reStructuredText example for the given request and response.

    :param dict headers: A dict of HTTP headers.
    :param str method: HTTP request method (e.g. "GET").
    :param str url: HTTP request URL.
    :param dict params: Form parameters, for POST and PUT requests.
    :param str response: Text response body.
    :returns: list
    """
    lines = ['', 'Example Request:', '', '.. code-block:: bash', '']
    lines.extend(prefix_lines(
        get_example_curl_lines(method, url, params, headers), '   '))
    lines.extend(['', 'Example Response:', ''])
    try:
        # Try to parse and prettify the response as JSON. If it fails
        # (for whatever reason), we'll treat it as text instead.
        response = json.dumps(json.loads(response), indent=2,
                              separators=(',', ': '), sort_keys=True)
        lines.extend(['.. code-block:: json', ''])
    except Exception:
        lines.extend(['.. code-block:: text', ''])
    lines.extend(prefix_lines(response, '   '))
    return lines


def get_json_object_lines(annotation: ResourceAnnotation,
                          properties: Dict[str, Any], field: str,
                          url_params: Dict, request: bool=False,
                          object_property: bool=False) -> List[str]:
    """Generate documentation for the given object annotation.

    :param doctor.resource.ResourceAnnotation annotation:
        Annotation object for the associated handler method.
    :param str field: Sphinx field type to use (e.g. '<json').
    :param list url_params: A list of url parameter strings.
    :param bool request: Whether the schema is for the request or not.
    :param bool object_property: If True it indicates this is a property of
        an object that we are documenting.  This is only set to True when
        called recursively when encountering a property that is an object in
        order to document the properties of it.
    :returns: list of strings, one for each line.
    """
    required_lines = []
    lines = []
    default_field = field
    for prop in sorted(properties.keys()):
        annotated_type = properties[prop]
        # If the property is a url parameter override the field to use
        # param so that it's not documented in the json body or query params.
        field = default_field
        if request and prop in url_params:
            field = 'param'

        types = [str(annotated_type.native_type.__name__)]
        description = annotated_type.description
        is_object = False
        if issubclass(annotated_type, Object):
            is_object = True

        # Document any enum.
        enum = ''
        if issubclass(annotated_type, Enum):
            enum = ' Must be one of: `{}`.'.format(annotated_type.enum)

        field_prop = prop
        if is_object:
            field_prop = '{}|object'.format(prop)
        elif object_property:
            field_prop = '{}|objectproperty'.format(prop)
        # If this is a request param and the property is required
        # add required text and append lines to required_lines.  This
        # will make the required properties appear in alphabetical order
        # before the optional.
        required_arg = False
        if request and prop in annotation.params.required:
            description = '**Required**.  ' + description
            required_lines.append(
                ':{field} {types} {prop}: {description}{enum}'.format(
                    field=field, types=','.join(types), prop=field_prop,
                    description=description, enum=enum))
            required_arg = True
        else:
            lines.append(':{field} {types} {prop}: {description}{enum}'.format(
                field=field, types=','.join(types), prop=field_prop,
                description=description, enum=enum))

        # If the property is of type object we want to recursively document
        # all of it's properties.
        if is_object:
            try:
                object_properties = get_json_object_lines(
                    annotation, annotated_type.properties, field, {}, request,
                    object_property=True)
                if required_arg:
                    required_lines.extend(object_properties)
                else:
                    lines.extend(object_properties)
            except SchemaError as e:
                logging.warning('Not documenting object properties for property'
                                ' %s. Reason: %s', prop, e)
                # If we encountered a schema error trying to document an
                # object's properties we need to remove the `|object[property]`
                # from the line as we are skipping documenting it's properties.
                # This could happen if the property is a reference or is in
                # an external file.  At some point we may want to figure out
                # how to get the value, but for now just skip it.
                if required_arg:
                    required_lines[-1] = required_lines[-1].replace(
                        field_prop, prop)
                else:
                    lines[-1] = lines[-1].replace(field_prop, prop)

    return required_lines + lines


def get_json_lines(annotation: ResourceAnnotation, field: str, route: str,
                   request: bool=False) -> List:
    """Generate documentation lines for the given annotation.

    This only documents schemas of type "object", or type "list" where each
    "item" is an object. Other types are ignored (but a warning is logged).

    :param doctor.resource.ResourceAnnotation annotation:
        Annotation object for the associated handler method.
    :param str field: Sphinx field type to use (e.g. '<json').
    :param str route: The route the annotation is attached to.
    :param bool request: Whether the resource annotation is for the request or
        not.
    :returns: list of strings, one for each line.
    """
    url_params = URL_PARAMS_RE.findall(route)
    if not request:
        return_type = annotation.logic._doctor_signature.return_annotation
        if issubclass(return_type, Array):
            if issubclass(return_type.items, Object):
                properties = return_type.items.properties
                field += 'arr'
            else:
                return []
        elif issubclass(return_type, Object):
            properties = return_type.properties
        else:
            return []
    else:
        parameters = annotation.annotated_parameters
        properties = {k: p.annotation for k, p in parameters.items()}
    return get_json_object_lines(annotation, properties, field, url_params,
                                 request)


def get_name(value) -> str:
    """Return a best guess at the qualified name for a class or function.

    :param value: A class or function object.
    :type value: class or function
    :returns str:
    """
    if value.__module__ == '__builtin__':
        return value.__name__
    else:
        return '.'.join((value.__module__, value.__name__))


def normalize_route(route: str) -> str:
    """Strip some of the ugly regexp characters from the given pattern.

    >>> normalize_route('^/user/<user_id:int>/?$')
    u'/user/(user_id:int)/'
    """
    normalized_route = str(route).lstrip('^').rstrip('$').rstrip('?')
    normalized_route = normalized_route.replace('<', '(').replace('>', ')')
    return normalized_route


def prefix_lines(lines, prefix):
    """Add the prefix to each of the lines.

    >>> prefix_lines(['foo', 'bar'], '  ')
    ['  foo', '  bar']
    >>> prefix_lines('foo\\nbar', '  ')
    ['  foo', '  bar']

    :param list or str lines: A string or a list of strings. If a string is
        passed, the string is split using splitlines().
    :param str prefix: Prefix to add to the lines. Usually an indent.
    :returns: list
    """
    if isinstance(lines, bytes):
        lines = lines.decode('utf-8')
    if isinstance(lines, str):
        lines = lines.splitlines()
    return [prefix + line for line in lines]


class BaseDirective(Directive):

    """Base class for doctor Sphinx directives.

    You probably want to use
    :class:`~doctor.docs.flask.AutoFlaskDirective` instead of
    this class.
    """

    #: Name to use for this directive.
    #:
    #: This is the identifier used within the Sphinx documentation to trigger
    #: this directive. This value should be set by subclasses. For example, in
    #: :class:`~doctor.flask.docs.AutoFlaskDirective`, this is
    #: set to "autoflask".
    directive_name = None

    #: Harness for the Flask app this directive is documenting. This
    #: is responsible for setting up and tearing down the mock app. It is
    #: defined in Sphinx's conf.py file, and set on the directive in
    #: :meth:`~doctor.docs.base.BaseDirective.run_setup`. It should
    #: be an instance of :class:`~doctor.docs.base.BaseHarness`.
    harness = None

    #: Indicates to Sphinx that this directive will yield content.
    has_content = True

    def _make_example(
            self, route, handler, annotation):  # pragma: no cover
        self.harness.setup_request(self, route, handler, annotation)
        headers = self.harness._get_headers(str(route), annotation)
        try:
            response_data = self.harness.request(route, handler, annotation)
            return get_example_lines(headers, **response_data)
        except Exception as e:
            raise SphinxError(
                'Error rendering {method} {route} example: {exc}'.format(
                    method=annotation.http_method, route=route,
                    exc=e)
            )
        finally:
            self.harness.teardown_request(self, route, handler, annotation)

    def _prepare_env(self):  # pragma: no cover
        """Setup the document's environment, if necessary."""
        env = self.state.document.settings.env
        if not hasattr(env, self.directive_name):
            # Track places where we use this directive, so we can check for
            # outdated documents in the future.
            state = DirectiveState()
            setattr(env, self.directive_name, state)
        else:
            state = getattr(env, self.directive_name)
        return env, state

    def _render_rst(self):  # pragma: no cover
        """Render lines of reStructuredText for items yielded by
        :meth:`~doctor.docs.base.BaseHarness.iter_annotations`.
        """
        # Create a mapping of headers to annotations.  We want to group
        # all annotations by a header, but they could be in multiple handlers
        # so we create a map of them here with the heading as the key and
        # the list of associated annotations as a list.  This is so we can
        # sort them alphabetically to make reading the api docs easier.
        heading_to_annotations_map = defaultdict(list)
        for heading, route, handler, annotations in (
                self.harness.iter_annotations()):
            # Set the route and handler as attributes so we can retrieve them
            # when we loop through them all below.
            for annotation in annotations:
                annotation.route = route
                annotation.handler = handler
                heading_to_annotations_map[heading].append(annotation)

        headings = list(heading_to_annotations_map.keys())
        headings.sort()
        previous_heading = None
        for heading in headings:
            annotations = heading_to_annotations_map.get(heading)
            # Sort all the annotations by title.
            annotations.sort(key=lambda a: a.title)
            # Only emit a new heading if the resource has changed.  This
            # esnures that documented endpoints for the same resource all
            # end up under a single heading.
            if previous_heading != heading:
                previous_heading = heading
                yield HEADING_TOKEN + heading
            for annotation in annotations:
                route = annotation.route
                normalized_route = normalize_route(route)
                handler = annotation.handler
                # Adds a title for the endpoint.
                if annotation.title is not None:
                    yield annotation.title
                    yield '#' * len(annotation.title)
                docstring = get_description_lines(getattr(annotation.logic,
                                                          '__doc__', None))
                field = '<json'
                if annotation.http_method in ('DELETE', 'GET'):
                    field = 'query'
                docstring.extend(get_json_lines(
                    annotation, field=field, route=normalized_route,
                    request=True)
                )

                # Document any request headers.
                defined_headers = list(self.harness._get_headers(
                    str(route), annotation).keys())
                defined_headers.sort()
                for header in defined_headers:
                    definition = self.harness.header_definitions.get(
                        header, '')
                    docstring.append(':reqheader {}: {}'.format(
                        header, definition))

                # Document response if a type was defined.
                if annotation.return_annotation != Parameter.empty:
                    docstring.extend(get_json_lines(
                        annotation, field='>json', route=normalized_route))

                docstring.extend(self._make_example(route, handler, annotation))
                for line in http_directive(annotation.http_method,
                                           normalized_route, docstring):
                    yield line

    def run(self):  # pragma: no cover
        """Called by Sphinx to generate documentation for this directive."""
        if self.directive_name is None:
            raise NotImplementedError('directive_name must be implemented by '
                                      'subclasses of BaseDirective')
        env, state = self._prepare_env()
        state.doc_names.add(env.docname)
        directive_name = '<{}>'.format(self.directive_name)
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()
        for line in self._render_rst():
            if line.startswith(HEADING_TOKEN):
                # Remove heading token, then append 2 lines, one with
                # the heading text, and the other with the dashes to
                # underline the heading.
                heading = line[HEADING_TOKEN_LENGTH:]
                result.append(heading, directive_name)
                result.append('-' * len(heading), directive_name)
            else:
                result.append(line, directive_name)
        nested_parse_with_titles(self.state, result, node)
        return node.children

    @classmethod
    def get_outdated_docs(
            cls, app, env, added, changed, removed):  # pragma: no cover
        """Handler for Sphinx's env-get-outdated event.

        This handler gives a Sphinx extension a chance to indicate that some
        set of documents are out of date and need to be re-rendered. The
        implementation here is stupid, for now, and always says that anything
        that uses the directive needs to be re-rendered.

        We should make it smarter, at some point, and have it figure out which
        modules are used by the associated handlers, and whether they have
        actually been updated since the last time the given document was
        rendered.
        """
        state = getattr(env, cls.directive_name, None)
        if state and state.doc_names:
            # This is stupid for now, and always says everything that uses
            # this autodoc generation needs to be updated. We should make this
            # smarter at some point and actually figure out what modules are
            # touched, and whether they have been changed.
            return sorted(state.doc_names)
        else:
            return []

    @classmethod
    def purge_docs(cls, app, env, docname):  # pragma: no cover
        """Handler for Sphinx's env-purge-doc event.

        This event is emitted when all traces of a source file should be cleaned
        from the environment (that is, if the source file is removed, or before
        it is freshly read). This is for extensions that keep their own caches
        in attributes of the environment.

        For example, there is a cache of all modules on the environment. When a
        source file has been changed, the cache's entries for the file are
        cleared, since the module declarations could have been removed from the
        file.
        """
        state = getattr(env, cls.directive_name, None)
        if state and docname in state.doc_names:
            state.doc_names.remove(docname)

    @classmethod
    def run_setup(cls, app):  # pragma: no cover
        config_attr = '{}_harness'.format(cls.directive_name)
        cls.harness = getattr(app.config, config_attr)
        if not cls.harness:
            raise SphinxError('Please set {} in your conf.py'.format(
                config_attr))
        cls.harness.setup_app(app)

    @classmethod
    def run_teardown(cls, app, exception):  # pragma: no cover
        cls.harness.teardown_app(app)

    @classmethod
    def setup(cls, app):  # pragma: no cover
        """Called by Sphinx to setup an extension."""
        if cls.directive_name is None:
            raise NotImplementedError('directive_name must be set by '
                                      'subclasses of BaseDirective')
        if not app.registry.has_domain('http'):
            setup_httpdomain(app)
        app.add_config_value('{}_harness'.format(cls.directive_name),
                             None, 'env')
        app.add_directive(cls.directive_name, cls)
        app.connect('builder-inited', cls.run_setup)
        app.connect('build-finished', cls.run_teardown)
        app.connect('env-get-outdated', cls.get_outdated_docs)
        app.connect('env-purge-doc', cls.purge_docs)


class BaseHarness(object):

    """
    Base class for doctor directive harnesses. A harness is defined
    in Sphinx's conf.py, and the directive invokes the various methods at the
    appropriate times, so the app can bootstrap a mock version of itself.
    """

    def __init__(self, url_prefix):
        super(BaseHarness, self).__init__()
        self.defined_example_values = {}
        self.url_prefix = url_prefix.rstrip('/')
        #: Stores headers for particular methods and routes.
        self.defined_header_values = {}
        #: Stores global headers to use on all requests
        self.headers = {}
        #: Stores definitions for header keys for documentation.
        self.header_definitions = {}

    def iter_annotations(self):  # pragma: no cover
        """Yield a tuple for each schema annotated handler to document.

        This must be implemented by subclasses. See
        :class:`~doctor.docs.flask.AutoFlaskHarness` for an
        example implementation.
        """
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of BaseHarness')

    def define_header_values(self, http_method, route, values, update=False):
        """Define header values for a given request.

        By default, header values are determined from the class attribute
        `headers`. But if you want to change the headers used in the
        documentation for a specific route, this method lets you do that.

        :param str http_method: An HTTP method, like "get".
        :param str route: The route to match.
        :param dict values: A dictionary of headers for the example request.
        :param bool update: If True, the values will be merged into the default
            headers for the request. If False, the values will replace
            the default headers.
        """
        self.defined_header_values[(http_method.lower(), route)] = {
            'update': update,
            'values': values
        }

    def define_example_values(self, http_method, route, values, update=False):
        """Define example values for a given request.

        By default, example values are determined from the example properties
        in the schema. But if you want to change the example used in the
        documentation for a specific route, and this method lets you do that.

        :param str http_method: An HTTP method, like "get".
        :param str route: The route to match.
        :param dict values: A dictionary of parameters for the example request.
        :param bool update: If True, the values will be merged into the default
            example values for the request. If False, the values will replace
            the default example values.
        """
        self.defined_example_values[(http_method.lower(), route)] = {
            'update': update,
            'values': values
        }

    def request(self, route, handler, annotation):
        """Make a request against the app.

        This must be implemented by subclasses. See
        :class:`~doctor.docs.flask.AutoFlaskHarness` for an
        example implementation.
        """
        raise NotImplementedError('This method must be implemented by '
                                  'subclasses of BaseHarness')

    def setup_app(self, sphinx_app):  # pragma: no cover
        """Called once before building documentation.

        :param sphinx_app: Sphinx application object.
        """
        pass

    def setup_request(self, sphinx_directive, route, handler,
                      annotation):   # pragma: no cover
        """Called before each request to the mock app.

        :param BaseDirective sphinx_directive: The directive that is making
            the mock request.
        :param route: Path for the route. For Flask, this will be a Route
            object.
        :param handler: Flask resource for the route.
        :param ResourceAnnotation annotation: Annotation for the request.
        """
        pass

    def teardown_app(self, sphinx_app):  # pragma: no cover
        """Called once after building documentation.

        :param sphinx_app: Sphinx application object.
        """
        pass

    def teardown_request(self, sphinx_directive, route, handler,
                         annotation):   # pragma: no cover
        """Called after each request to the mock app.

        :param BaseDirective sphinx_directive: The directive that is making
            the mock request.
        :param route: Path for the route. For Flask, this will be a Route
            object.
        :param handler: Flask resource for the route.
        :param ResourceAnnotation annotation: Annotation for the request.
        """
        pass

    def _get_annotation_heading(self, handler, route, heading=None):
        """Returns the heading text for an annotation.

        Attempts to get the name of the heading from the handler attribute
        `schematic_title` first.

        If `schematic_title` it is not present, it attempts to generate
        the title from the class path.
        This path: advertiser_api.handlers.foo_bar.FooListHandler
        would translate to 'Foo Bar'

        If the file name with the resource is generically named handlers.py
        or it doesn't have a full path then we attempt to get the resource
        name from the class name.
        So FooListHandler and FooHandler would translate to 'Foo'.
        If the handler class name starts with 'Internal', then that will
        be appended to the heading.
        So InternalFooListHandler would translate to 'Foo (Internal)'

        :param mixed handler: The handler class.  Will be a flask resource class
        :param str route: The route to the handler.
        :returns: The text for the heading as a string.
        """
        if hasattr(handler, '_doctor_heading'):
            return handler._doctor_heading

        heading = ''
        handler_path = str(handler)
        try:
            handler_file_name = handler_path.split('.')[-2]
        except IndexError:
            # In the event there is no path and we just have the class name,
            # get heading from the class name by setting us up to enter the
            # first if statement.
            handler_file_name = 'handler'

        # Get heading from class name
        if handler_file_name.startswith('handler'):
            class_name = handler_path.split('.')[-1]
            internal = False
            for word in CAMEL_CASE_RE.findall(class_name):
                if word == 'Internal':
                    internal = True
                    continue
                elif word.startswith(('List', 'Handler', 'Resource')):
                    # We've hit the end of the class name that contains
                    # words we are interested in.
                    break
                heading += '%s ' % (word,)
            if internal:
                heading = heading.strip()
                heading += ' (Internal)'
        # Get heading from handler file name
        else:
            heading = ' '.join(handler_file_name.split('_')).title()
            if 'internal' in route:
                heading += ' (Internal)'
        return heading.strip()

    def _get_headers(self, route: str, annotation: ResourceAnnotation) -> Dict:
        """Gets headers for the provided route.

        :param route: The route to get example values for.
        :type route: werkzeug.routing.Rule for a flask api.
        :param annotation: Schema annotation for the method to be requested.
        :type annotation: doctor.resource.ResourceAnnotation
        :retruns: A dict containing headers.
        """
        headers = self.headers.copy()
        defined_header_values = self.defined_header_values.get(
            (annotation.http_method.lower(), str(route)))
        if defined_header_values is not None:
            if defined_header_values['update']:
                headers.update(defined_header_values['values'])
            else:
                headers = defined_header_values['values']
        return headers

    def _get_example_values(self, route: str,
                            annotation: ResourceAnnotation) -> Dict[str, Any]:
        """Gets example values for all properties in the annotation's schema.

        :param route: The route to get example values for.
        :type route: werkzeug.routing.Rule for a flask api.
        :param annotation: Schema annotation for the method to be requested.
        :type annotation: doctor.resource.ResourceAnnotation
        :retruns: A dict containing property names as keys and example values
            as values.
        """
        defined_values = self.defined_example_values.get(
            (annotation.http_method.lower(), str(route)))
        if defined_values and not defined_values['update']:
            return defined_values['values']
        values = {
            k: v.annotation.get_example()
            for k, v in annotation.annotated_parameters.items()
        }
        if defined_values:
            values.update(defined_values['values'])

        # If this is a GET route, we need to json dumps any parameters that
        # are lists or dicts.  Otherwise we'll get a 400 error for those params
        if annotation.http_method == 'GET':
            for k, v in values.items():
                if isinstance(v, (list, dict)):
                    values[k] = json.dumps(v)
        return values


class DirectiveState(object):

    """This is used to hold Sphinx serialized state for our directives."""

    def __init__(self):  # pragma: no cover
        super(DirectiveState, self).__init__()
        self.doc_names = set()
