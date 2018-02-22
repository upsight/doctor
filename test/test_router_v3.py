import inspect

from flask_restful import Resource

from doctor.router_v3 import (
    create_routes, delete, get, get_params_from_func, post, put, HTTPMethod,
    Params, Route)
from doctor.types import array, boolean, integer, string


Name = string('name', min_length=1)
Age = integer('age', minimum=1, maximum=120)
IsAlive = boolean('Is alive?')
FooId = integer('foo id')
Foo = string('foo')
Foos = array('foos', items=Foo)


def delete_foo(foo_id: FooId):
    pass


def get_foo(name: Name, age: Age, is_alive: IsAlive=True) -> Foo:
    return ''


def get_foos(is_alive: IsAlive=True) -> Foos:
    return ''


def create_foo(name: Name) -> Foo:
    return ''


def update_foo(foo_id: FooId, name: Name, is_alive: IsAlive=True) -> Foo:
    return ''


def no_params() -> Foo:
    return ''


class TestRouterV3(object):

    def test_delete(self):
        expected = HTTPMethod('delete', get_foo)
        a = delete(get_foo)
        assert a.method == expected.method
        assert a.logic == expected.logic

    def test_get(self):
        expected = HTTPMethod('get', get_foo)
        actual = get(get_foo)
        assert actual.method == expected.method
        assert actual.logic == expected.logic

    def test_post(self):
        expected = HTTPMethod('post', get_foo)
        actual = post(get_foo)
        assert actual.method == expected.method
        assert actual.logic == expected.logic

    def test_put(self):
        expected = HTTPMethod('put', get_foo)
        actual = put(get_foo)
        assert actual.method == expected.method
        assert actual.logic == expected.logic

    def test_get_params_from_func(self):
        get_foo._doctor_signature = inspect.signature(get_foo)
        expected = Params(
            all=['name', 'age', 'is_alive'],
            optional=['is_alive'],
            required=['name', 'age'])
        assert expected == get_params_from_func(get_foo)

    def test_get_params_from_func_no_params(self):
        no_params._doctor_signature = inspect.signature(no_params)
        expected = Params([], [], [])
        assert expected == get_params_from_func(no_params)

    def test_create_routes(self):
        class MyHandler(Resource):
            pass

        routes = (
            Route('^/foo/?$', (
                get(get_foos),
                post(create_foo)), base_handler_class=MyHandler,
                handler_name='MyHandler'),
            Route('^/foo/<int:foo_id>/?$', (
                delete(delete_foo),
                get(get_foo),
                put(update_foo))),
        )
        actual = create_routes(routes)

        # 2 routes created
        assert 2 == len(actual)

        # verify the first route
        route, handler = actual[0]
        assert r'^/foo/?$' == route

        # verify it's an instance of our base handler class.
        assert issubclass(handler, MyHandler)
        # verify it used our custom handler name
        assert 'MyHandler' == handler.__name__

        # verify each http method was added
        assert hasattr(handler, 'get')
        assert hasattr(handler, 'post')

        # verify params for get
        params = handler.get._doctor_params
        expected = Params(
            all=['is_alive'], required=[], optional=['is_alive'])
        assert expected == params

        # verify signature
        sig = handler.get._doctor_signature
        expected = inspect.signature(get_foos)
        assert expected == sig

        # verify params for post
        params = handler.post._doctor_params
        expected = Params(
            all=['name'], required=['name'], optional=[])
        assert expected == params

        # verify signature
        sig = handler.post._doctor_signature
        expected = inspect.signature(create_foo)
        assert expected == sig

        # verify the second route
        route, handler = actual[1]
        assert '^/foo/<int:foo_id>/?$' == route
        # verify each http method was added
        assert hasattr(handler, 'get')
        assert hasattr(handler, 'delete')
        assert hasattr(handler, 'put')
