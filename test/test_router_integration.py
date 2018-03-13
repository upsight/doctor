from functools import wraps

from doctor.flask import create_routes
from doctor.routing import get, Route

from .base import FlaskTestCase
from .types import ItemId, Name


def adds_positional_arg_to_func(arg=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(arg, *args, **kwargs)
        return wrapper
    return decorator


@adds_positional_arg_to_func(55)
def logic_func(pos_arg, item_id: ItemId, name: Name=None):
    return {
        'item_id': item_id,
        'name': name,
        'pos_arg': pos_arg,
    }


class RouterIntegrationTestCase(FlaskTestCase):

    def get_routes(self):
        routes = (
            Route('/test/', methods=(
                get(logic_func),), heading='Test'),
        )
        return create_routes(routes)

    def test_decorated_logic_func_passes_arg_to_func(self):
        """
        This test verifies everything works properly if our logic function
        is decorated and the decorator passes an extra positional argument to
        it.  This was broken in v1.1.3 as it would cause a 400 saying that
        `pos_arg` is required as a request parameter since it was not taking
        into accout `omit_args` and just determining required arguments based
        on the function signature's non-keyword arguments.
        """
        response = self.client.get('/test/', query_string={'item_id': 1})
        expected = {
            'item_id': 1,
            'name': None,
            'pos_arg': 55,
        }
        self.assertEqual(expected, response.json)
