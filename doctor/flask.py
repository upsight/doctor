from __future__ import absolute_import

import logging
import os
from typing import Callable, Dict, List, Tuple, Union


try:
    from flask import current_app, request
    from flask_restful import Resource
    from werkzeug.exceptions import (BadRequest, Conflict, Forbidden,
                                     HTTPException, NotFound, Unauthorized,
                                     InternalServerError)
except ImportError:  # pragma: no cover
    raise ImportError('You must install flask to use the '
                      'doctor.flask module.')

from .constants import HTTP_METHODS_WITH_JSON_BODY
from .errors import (ForbiddenError, ImmutableError, InvalidValueError,
                     NotFoundError, TypeSystemError, UnauthorizedError)
from .response import Response
from .routing import create_routes as doctor_create_routes
from .routing import Route


STATUS_CODE_MAP = {
    'POST': 201,
    'DELETE': 204,
}

ListOrNone = Union[List, None]


class SchematicHTTPException(HTTPException):

    """Schematic specific sub-class of werkzeug's BadRequest.

    Note that this adds a flask-restful specific data attribute to the class,
    as the error wouldn't render properly without it.

    :param description: The error description.
    :param errors: A dict containing all validation errors during the request.
        The key is the param name and the value is the error message.
    """

    def __init__(self, description: str=None, errors: dict=None):
        super(SchematicHTTPException, self).__init__(description)
        self.data = {'status': self.code, 'message': description}
        self.errors = errors

    def __str__(self):
        return '%d: %s: %s' % (self.code, self.name, self.description)


class HTTP400Exception(SchematicHTTPException, BadRequest):
    """Represents a HTTP 400 error.

    :param description: The error description.
    :param errors: A dict containing all validation errors during the request.
        The key is the param name and the value is the error message.
    """
    pass


class HTTP401Exception(SchematicHTTPException, Unauthorized):
    pass


class HTTP403Exception(SchematicHTTPException, Forbidden):
    pass


class HTTP404Exception(SchematicHTTPException, NotFound):
    pass


class HTTP409Exception(SchematicHTTPException, Conflict):
    pass


class HTTP500Exception(SchematicHTTPException, InternalServerError):
    pass


def should_raise_response_validation_errors() -> bool:
    """Returns if the library should raise response validation errors or not.

    If the environment variable `RAISE_RESPONSE_VALIDATION_ERRORS` is set,
    it will return True.

    :returns: True if it should, False otherwise.
    """
    return bool(os.environ.get('RAISE_RESPONSE_VALIDATION_ERRORS', False))


def handle_http(handler: Resource, args: Tuple, kwargs: Dict, logic: Callable):
    """Handle a Flask HTTP request

    :param handler: flask_restful.Resource: An instance of a Flask Restful
        resource class.
    :param tuple args: Any positional arguments passed to the wrapper method.
    :param dict kwargs: Any keyword arguments passed to the wrapper method.
    :param callable logic: The callable to invoke to actually perform the
        business logic for this request.
    """
    try:
        # We are checking mimetype here instead of content_type because
        # mimetype is just the content-type, where as content_type can
        # contain encoding, charset, and language information.  e.g.
        # `Content-Type: application/json; charset=UTF8`
        if (request.mimetype == 'application/json' and
                request.method in HTTP_METHODS_WITH_JSON_BODY):
            # This is a proper typed JSON request. The parameters will be
            # encoded into the request body as a JSON blob.
            request_params = request.json
        else:
            # Try to parse things from normal HTTP parameters
            request_params = request.values
        # Filter out any params not part of the logic signature.
        all_params = logic._doctor_params.all
        params = {k: v for k, v in request_params.items() if k in all_params}
        params.update(**kwargs)

        # Check for required params
        missing = []
        for required in logic._doctor_params.required:
            if required not in params:
                missing.append(required)
        if missing:
            if len(missing) == 1:
                verb = 'is'
                missing = missing[0]
            else:
                verb = 'are'
            error = '{} {} required.'.format(missing, verb)
            raise InvalidValueError(error)

        # Validate and coerce parameters to the appropriate types.
        errors = {}
        sig = logic._doctor_signature
        for name, value in params.items():
            annotation = sig.parameters[name].annotation
            try:
                params[name] = annotation.native_type(annotation(value))
            except TypeSystemError as e:
                errors[name] = e.detail
        if errors:
            raise TypeSystemError(errors, errors=errors)

        # Only pass request parameters defined by the logic signature.
        logic_params = {k: v for k, v in params.items()
                        if k in logic._doctor_params.logic}
        response = logic(*args, **logic_params)

        # response validation
        if sig.return_annotation != sig.empty:
            _response = response
            if isinstance(response, Response):
                _response = response.content
            try:
                sig.return_annotation(_response)
            except TypeSystemError as e:
                response_str = str(_response)
                logging.warning('Response to %s %s does not validate: %s.',
                                request.method, request.path,
                                response_str, exc_info=e)
                if should_raise_response_validation_errors():
                    error = ('Response to {method} {path} `{response}` does not'
                             ' validate: {error}'.format(
                                method=request.method, path=request.path,
                                response=response, error=e.detail))
                    raise TypeSystemError(error)

        if isinstance(response, Response):
            return (response.content, STATUS_CODE_MAP.get(request.method, 200),
                    response.headers)
        return response, STATUS_CODE_MAP.get(request.method, 200)
    except (InvalidValueError, TypeSystemError) as e:
        errors = getattr(e, 'errors', None)
        raise HTTP400Exception(e, errors=errors)
    except UnauthorizedError as e:
        raise HTTP401Exception(e)
    except ForbiddenError as e:
        raise HTTP403Exception(e)
    except NotFoundError as e:
        raise HTTP404Exception(e)
    except ImmutableError as e:
        raise HTTP409Exception(e)
    except Exception as e:
        # Always re-raise exceptions when DEBUG is enabled for development.
        if current_app.config.get('DEBUG', False):
            raise
        allowed_exceptions = logic._doctor_allowed_exceptions
        if allowed_exceptions and any(isinstance(e, cls)
                                      for cls in allowed_exceptions):
            raise
        logging.exception(e)
        raise HTTP500Exception('Uncaught error in logic function')


def create_routes(routes: Tuple[Route]) -> List[Tuple[str, Resource]]:
    """A thin wrapper around create_routes that passes in flask specific values.

    :param routes: A tuple containing the route and another tuple with
        all http methods allowed for the route.
    :returns: A list of tuples containing the route and generated handler.
    """
    return doctor_create_routes(
        routes, handle_http, default_base_handler_class=Resource)
