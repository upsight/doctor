from __future__ import absolute_import

import logging
import os
from typing import Callable, Dict, List, Tuple, Union


try:
    import flask_restful
    from flask import current_app, request
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


STATUS_CODE_MAP = {
    'POST': 201,
    'DELETE': 204,
}

ListOrNone = Union[List, None]


class SchematicHTTPException(HTTPException):

    """Schematic specific sub-class of werkzeug's BadRequest.

    Note that this adds a flask-restful specific data attribute to the class,
    as the error wouldn't render properly without it.
    """

    def __init__(self, description=None, errobj=None):
        super(SchematicHTTPException, self).__init__(description)
        self.data = {'status': self.code, 'message': description}
        self.errobj = errobj

    def __str__(self):
        return '%d: %s: %s' % (self.code, self.name, self.description)


class HTTP400Exception(SchematicHTTPException, BadRequest):
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

    If the app config has DEBUG set to True or the environment variable
    `RAISE_RESPONSE_VALIDATION_ERRORS` is set, it will return True.

    :returns: True if it should, False otherwise.
    """
    return (current_app.config.get('DEBUG', False) or
            bool(os.environ.get('RAISE_RESPONSE_VALIDATION_ERRORS', False)))


def handle_http(handler: flask_restful.Resource, args: Tuple, kwargs: Dict,
                logic: Callable):
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

        # Validate and coerce parameters to the appropriate types.
        for required in logic._doctor_params.required:
            if required not in params:
                raise InvalidValueError(f'{required} is required.')
        sig = logic._doctor_signature
        for name, value in params.items():
            annotation = sig.parameters[name].annotation
            params[name] = annotation(value)

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
                    raise

        if isinstance(response, Response):
            return (response.content, STATUS_CODE_MAP.get(request.method, 200),
                    response.headers)
        return response, STATUS_CODE_MAP.get(request.method, 200)
    except (InvalidValueError, TypeSystemError) as e:
        errors = getattr(e, 'errors', None)
        raise HTTP400Exception(e, errobj=errors)
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
