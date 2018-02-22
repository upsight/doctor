import functools
import inspect
from collections import namedtuple
from typing import Callable, List, Tuple

from flask_restful import Resource

from doctor.flask import handle_http_v3


#: A named tuple that holds all, optional, and required request parameters.
Params = namedtuple('Params', ['all', 'optional', 'required'])


class HTTPMethod(object):
    """Represents and HTTP method and it's configuration.

    :param method: The HTTP method.  One of: (delete, get, post, put).
    :param logic: The logic function to be called for the http method.
    """
    def __init__(self, method: str, logic: Callable):
        self.logic = logic
        self.method = method


def delete(func: Callable) -> HTTPMethod:
    """Returns a dict with required args to create a DELETE route.

    :param func: The logic function that should be called.
    :returns: HTTPMethod
    """
    return HTTPMethod('delete', func)


def get(func: Callable) -> HTTPMethod:
    """Returns a dict with required args to create a GET route.

    :param func: The logic function that should be called.
    :returns: HTTPMethod
    """
    return HTTPMethod('get', func)


def post(func: Callable) -> HTTPMethod:
    """Returns a dict with required args to create a POST route.

    :param func: The logic function that should be called.
    :returns: HTTPMethod
    """
    return HTTPMethod('post', func)


def put(func: Callable) -> HTTPMethod:
    """Returns a dict with required args to create a PUT route.

    :param func: The logic function that should be called.
    :returns: HTTPMethod
    """
    return HTTPMethod('put', func)


def get_params_from_func(func: Callable) -> Params:
    """Gets all parameters from a function signature.

    :param func: The function to inspect.
    :returns: A named tuple containing information about all, optional and
        required paramters.
    """
    s = func._doctor_signature
    required = [key for key, p in s.parameters.items() if p.default == p.empty]
    optional = [key for key, p in s.parameters.items() if p.default != p.empty]
    all_params = [key for key in s.parameters.keys()]
    return Params(all_params, optional, required)


def create_http_method(logic: Callable, http_method: str) -> Callable:
    """Create a handler method to be used in a handler class.

    :param callable logic: The underlying function to execute with the
        parsed and validated parameters.
    :param str http_method: HTTP method this will handle.
    :returns: A handler function.
    """
    @functools.wraps(logic)
    def fn(handler, *args, **kwargs):
        return handle_http_v3(handler, args, kwargs, logic)
    return fn


class Route(object):

    """Represents a route.

    :param route: The route path, e.g. `r'^/foo/<int:foo_id>/?$'`
    :param methods: A tuple of defined HTTPMethods for the route.
    :param base_handler_class: The base handler class to use.
    :param handler_name: The name that should be given to the handler class.
    """
    def __init__(self, route: str, methods: Tuple[HTTPMethod],
                 base_handler_class=Resource, handler_name: str=None):
        self.route = route
        self.methods = methods
        self.base_handler_class = base_handler_class
        self.handler_name = handler_name


def create_routes(routes: Tuple[HTTPMethod]) -> List[Tuple[str, Resource]]:
    """Creates handler routes from the provided routes.

    :param routes: A tuple containing the route and another tuple with
        all http methods allowed for the route.
    :returns: A list of tuples containing the route and generated handler.
    """
    created_routes = []
    for r in routes:
        handler = None
        for method in r.methods:
            logic = method.logic
            http_method = method.method
            logic._doctor_signature = inspect.signature(logic)
            params = get_params_from_func(logic)
            logic._doctor_params = params
            http_func = create_http_method(logic, http_method)
            handler_name = r.handler_name or logic.__name__
            handler_methods_and_properties = {
                '__name__': handler_name,
                http_method: http_func,
            }
            if handler is None:
                handler = type(
                    handler_name, (r.base_handler_class,),
                    handler_methods_and_properties)
            else:
                setattr(handler, http_method, http_func)
                # This is specific to Flask.  Its MethodView class
                # initializes the methods attribute in __new__ so we
                # need to add all the other http methods we are defining
                # on the handler after it gets created by type.
                if hasattr(handler, 'methods'):
                    handler.methods.append(http_method.upper())
        created_routes.append((r.route, handler))
    return created_routes
