import functools
import inspect

import jsonschema

from .parsers import parse_value
from .schema import Schema


class ResourceSchemaAnnotation(object):

    """Metadata about the schema used for a given request method.

    An instance of this class is attached to each handler method in a
    _schema_annotation attribute. It can be used for introspection about the
    schemas, to generate things like API documentation and hyper schemas from
    the code.

    :param func logic: Logic function which will handle the request.
    :param str http_method: The HTTP request method for this request (e.g. GET).
    :param doctor.resource.ResourceSchema schema: The resource schema
        object for this handler.
    :param dict request_schema: The schema used to validate the request.
    :param dict response_schema: The schema used to validate the response.
    :param str title: A short title for the route.  e.g. 'Create Foo' might
        be used for a POST method on a FooListHandler.
    """

    def __init__(self, logic, http_method, schema, request_schema,
                 response_schema, title=None):
        self.logic = logic
        self.http_method = http_method
        self.schema = schema
        self.request_schema = request_schema
        self.response_schema = response_schema
        self.title = title
        if title is None:
            if http_method.upper() == 'GET':
                self.title = 'Retrieve'
            elif http_method.upper() == 'POST':
                self.title = 'Create'
            elif http_method.upper() == 'PUT':
                self.title = 'Update'
            elif http_method.upper() == 'DELETE':
                self.title = 'Delete'

    @classmethod
    def get_annotation(cls, fn):
        """Find the _schema_annotation attribute for the given function.

        This will descend through decorators until it finds something that has
        the attribute. If it doesn't find it anywhere, it will return None.

        :param func fn: Find the attribute on this function.
        :returns: an instance of
            :class:`~doctor.resource.ResourceSchemaAnnotation` or
            None.
        """
        while fn is not None:
            if hasattr(fn, '_schema_annotation'):
                return fn._schema_annotation
            fn = getattr(fn, 'im_func', fn)
            closure = getattr(fn, '__closure__', None)
            fn = closure[0].cell_contents if closure is not None else None
        return None


class ResourceSchema(Schema):

    """
    This class extends :class:`~doctor.schema.Schema` with methods
    for generating HTTP handler functions that automatically parse and
    validate the request and response objects with a given schema.
    """

    def __init__(self, schema, handle_http=None,
                 raise_response_validation_errors=False, **kwargs):
        """
        :param dict schema: The JSON schema to use for this resource.
        :param function handle_http: The HTTP handler function that should be
            used to wrap the logic functions. You would normally pass
            :func:`doctor.flask.handle_http`.
        :param bool raise_response_validation_errors: True to raise errors
            for response validation exceptions, False to just log them
            and return gracefully.
        """
        super(ResourceSchema, self).__init__(schema, **kwargs)
        self.handle_http = handle_http
        self.raise_response_validation_errors = raise_response_validation_errors

    def _create_request_schema(self, params, required):
        """Create a JSON schema for a request.

        :param list params: A list of keys specifying which definitions from
            the base schema should be allowed in the request.
        :param list required: A subset of the params that the requester must
            specify in the request.
        :returns: a JSON schema dict
        """
        # We allow additional properties because the data this will validate
        # may also include kwargs passed by decorators on the handler method.
        schema = {'additionalProperties': True,
                  'definitions': self.resolve('#/definitions'),
                  'properties': {},
                  'required': required or (),
                  'type': 'object'}
        for param in params:
            schema['properties'][param] = {
                '$ref': '#/definitions/{}'.format(param)}
        return schema

    def _parse_params(self, params, request_schema):
        """Use the request schema to coerce string params.

        This is used for HTTP requests, in which the form parameters are all
        strings, but need to be converted to the appropriate types before
        validating them.

        :param dict params: The parameters specified in the request.
        :param dict request_schema: The JSON schema for the request.
        :returns: a dict of params parsed from the input dict.
        """
        parsed_params = {}
        properties = request_schema['properties']
        for key in properties:
            if key not in params:
                continue
            prop_schema = self.resolve('#' + key, properties)
            _, value = parse_value(
                params[key], self.resolve('#type', prop_schema), key)
            parsed_params[key] = value
        return parsed_params

    def _create_http_method(self, logic, http_method, request=None,
                            response=None, params=None, required=None,
                            before=None, after=None, allowed_exceptions=None,
                            title=None):
        """Create a handler method to be used in a handler class.

        :param callable logic: The underlying function to execute with the
            parsed and validated parameters.
        :param str http_method: HTTP method this will handle.
        :param str request: A key specifying which schema definition should be
            expected in the request.
        :param str response: A key specifying which schema definition should be
            expected in the response.
        :param list(str) params: A list of keys specifying which definitions
            from the base schema should be allowed in the request.
        :param list(str) required: A subset of the params that the requester
            must specify in the request.
        :param callable before: A method to run prior to executing handle_http.
        :param callable after: A method to run after executinghandle_http.
        :param list(class) allowed_exceptions: If specified, these exception
            classes will be re-raised instead of turning them into 500 errors.
        :param str title: A short title for the route.  e.g. 'Create Foo' might
            be used for a POST method on a FooListHandler.
        :returns: a handler function
        """
        if request:
            request_schema = self.resolve('#/definitions/{}'.format(request))
            request_validator = jsonschema.Draft4Validator(
                request_schema, resolver=self.resolver,
                format_checker=jsonschema.draft4_format_checker)
        elif params:
            request_schema = self._create_request_schema(params, required)
            request_validator = jsonschema.Draft4Validator(
                request_schema, resolver=self.resolver,
                format_checker=jsonschema.draft4_format_checker)
        else:
            request_schema = request_validator = None
        if response:
            response_schema = self.resolve('#/definitions/{}'.format(response))
            response_validator = jsonschema.Draft4Validator(
                response_schema, resolver=self.resolver,
                format_checker=jsonschema.draft4_format_checker)
        else:
            response_schema = response_validator = None

        before = before if before else (lambda *args, **kwargs: None)
        after = after if after else (lambda *args, **kwargs: None)

        try:
            logic._argspec = inspect.getargspec(logic)
        except TypeError:
            logic._argspec = inspect.getargspec(logic.__call__)

        @functools.wraps(logic)
        def fn(handler, *args, **kwargs):
            before(handler, *args, **kwargs)
            result = self.handle_http(
                self, handler, args, kwargs, logic,
                request_schema, request_validator,
                response_validator, allowed_exceptions)
            after(handler, result, *args, **kwargs)
            return result

        fn.required_args = required or []
        fn._schema_annotation = ResourceSchemaAnnotation(
            fn, http_method.upper(), self, request_schema, response_schema,
            title)
        return fn

    def http_delete(self, logic, request=None, response=None, params=None,
                    required=None, before=None, after=None,
                    allowed_exceptions=None, title=None):
        """Create a handler method for a delete request.

        :see: :meth:`_create_http_method`
        """
        return self._create_http_method(
            logic, 'DELETE', request=request, response=response, params=params,
            required=required, before=before, after=after,
            allowed_exceptions=allowed_exceptions, title=title)

    def http_get(self, logic, request=None, response=None, params=None,
                 required=None, before=None, after=None,
                 allowed_exceptions=None, title=None):
        """Create a handler method for a get request.

        :see: :meth:`_create_http_method`
        """
        return self._create_http_method(
            logic, 'GET', request=request, response=response, params=params,
            required=required, before=before, after=after,
            allowed_exceptions=allowed_exceptions, title=title)

    def http_post(self, logic, request=None, response=None, params=None,
                  required=None, before=None, after=None,
                  allowed_exceptions=None, title=None):
        """Create a handler method for a post request.

        :see: :meth:`_create_http_method`
        """
        return self._create_http_method(
            logic, 'POST', request=request, response=response, params=params,
            required=required, before=before, after=after,
            allowed_exceptions=allowed_exceptions, title=title)

    def http_put(self, logic, request=None, response=None, params=None,
                 required=None, before=None, after=None,
                 allowed_exceptions=None, title=None):
        """Create a handler method for a put request.

        :see: :meth:`_create_http_method`
        """
        return self._create_http_method(
            logic, 'PUT', request=request, response=response, params=params,
            required=required, before=before, after=after,
            allowed_exceptions=allowed_exceptions, title=title)
