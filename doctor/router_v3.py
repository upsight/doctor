import functools
import inspect
from collections import namedtuple
from typing import Any, Callable, Dict, Tuple

import flask_restful

from doctor.flask import handle_http_v3


def delete(func: Callable) -> Dict[str, Any]:
    """Returns a dict with required args to create a DELETE route.

    :param func: The logic function that should be called.
    :returns: dict
    """
    return {
        'logic': func,
        'http_method': 'delete',
    }


def get(func: Callable) -> Dict[str, Any]:
    """Returns a dict with required args to create a GET route.

    :param func: The logic function that should be called.
    :returns: dict
    """
    return {
        'logic': func,
        'http_method': 'get',
    }


def post(func: Callable) -> Dict[str, Any]:
    """Returns a dict with required args to create a POST route.

    :param func: The logic function that should be called.
    :returns: dict
    """
    return {
        'logic': func,
        'http_method': 'post',
    }


def put(func: Callable) -> Dict[str, Any]:
    """Returns a dict with required args to create a PUT route.

    :param func: The logic function that should be called.
    :returns: dict
    """
    return {
        'logic': func,
        'http_method': 'put',
    }


def get_params_from_func(func):
    Params = namedtuple('Params', ['all', 'optional', 'required'])
    s = func._doctor_signature
    required = [key for key, p in s.parameters.items() if p.default == p.empty]
    optional = [key for key, p in s.parameters.items() if p.default != p.empty]
    all_params = [key for key in s.parameters.keys()]
    return Params(all_params, optional, required)


def create_http_method(logic, http_method):
    @functools.wraps(logic)
    def fn(handler, *args, **kwargs):
        return handle_http_v3(handler, args, kwargs, logic)
    return fn


def create_routes(routes: Tuple[str, Tuple]):
    """Creates routes.

    :param routes: A tuple containing the route and another tuple with
        all http methods allowed for the route.
    :returns:
    """
    created_routes = []
    for route, methods in routes:
        handler = None
        for method in methods:
            logic = method['logic']
            http_method = method['http_method']
            logic._doctor_signature = inspect.signature(logic)
            params = get_params_from_func(logic)
            logic._doctor_params = params
            http_func = create_http_method(logic, http_method)
            handler_name = logic.__name__
            handler_methods_and_properties = {
                '__name__': handler_name,
                http_method: http_func,
            }
            if handler is None:
                handler = type(
                    handler_name, (flask_restful.Resource,),
                    handler_methods_and_properties)
            else:
                setattr(handler, http_method, http_func)
                # This is specific to Flask.  Its MethodView class
                # initializes the methods attribute in __new__ so we
                # need to add all the other http methods we are defining
                # on the handler after it gets created by type.
                if hasattr(handler, 'methods'):
                    handler.methods.append(http_method.upper())
        created_routes.append((route, handler))
    return created_routes
