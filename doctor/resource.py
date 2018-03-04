from typing import Callable

from .schema import Schema
from .types import SuperType


#: A mapping of HTTP method to title that should be used for it in
#: API documentation.
HTTP_METHOD_TITLES = {
    'DELETE': 'Delete',
    'GET': 'Retrieve',
    'POST': 'Create',
    'PUT': 'Update',
}


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
            self.title = HTTP_METHOD_TITLES.get(http_method.upper())

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


class ResourceAnnotation(object):

    """Metadata about the types used for a given request method.

    :param logic: The logic function for the resource.
    :param http_method: The http method for this resource.  One of `DELETE`,
        `GET`, `POST` or `PUT`.
    :param title: The title to be used by the api documentation for this
        resource.
    """

    def __init__(self, logic: Callable, http_method: str, title: str=None):
        self.annotated_parameters = {
            k: p for k, p in logic._doctor_signature.parameters.items()
            if issubclass(p.annotation, SuperType)
        }
        self.http_method = http_method.upper()
        self.logic = logic
        self.params = logic._doctor_params
        self.return_annotation = logic._doctor_signature.return_annotation
        self.title = title
        if title is None:
            self.title = HTTP_METHOD_TITLES.get(http_method.upper())


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
