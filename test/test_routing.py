import inspect

from flask_restful import Resource

from doctor.flask import handle_http
from doctor.routing import (
    create_routes, delete, get, post, put, HTTPMethod, Route)
from doctor.utils import Params

from .types import Age, Foo, FooId, Foos, IsAlive, Name


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


class TestRouting(object):

    def test_httpmethod(self):
        m = HTTPMethod('get', get_foo, allowed_exceptions=[ValueError],
                       title='Retrieve')
        assert 'get' == m.method
        assert get_foo == m.logic
        assert inspect.signature(get_foo) == m.logic._doctor_signature
        expected = Params(
            all=['name', 'age', 'is_alive'],
            optional=['is_alive'],
            required=['name', 'age'],
            logic=['name', 'age', 'is_alive'])
        assert expected == m.logic._doctor_params
        assert [ValueError] == m.logic._doctor_allowed_exceptions
        assert 'Retrieve' == m.logic._doctor_title

    def test_delete(self):
        expected = HTTPMethod('delete', get_foo,
                              allowed_exceptions=[ValueError], title='Title')
        a = delete(get_foo, allowed_exceptions=[ValueError], title='Title')
        assert a.method == expected.method
        assert a.logic == expected.logic
        assert a.logic._doctor_title == 'Title'
        assert a.logic._doctor_allowed_exceptions == [ValueError]

    def test_get(self):
        expected = HTTPMethod('get', get_foo, allowed_exceptions=[ValueError],
                              title='Title')
        actual = get(get_foo, allowed_exceptions=[ValueError], title='Title')
        assert actual.method == expected.method
        assert actual.logic == expected.logic
        assert actual.logic._doctor_title == 'Title'
        assert actual.logic._doctor_allowed_exceptions == [ValueError]

    def test_post(self):
        expected = HTTPMethod('post', get_foo, allowed_exceptions=[ValueError],
                              title='Title')
        actual = post(get_foo, allowed_exceptions=[ValueError], title='Title')
        assert actual.method == expected.method
        assert actual.logic == expected.logic
        assert actual.logic._doctor_title == 'Title'
        assert actual.logic._doctor_allowed_exceptions == [ValueError]

    def test_put(self):
        expected = HTTPMethod('put', get_foo, allowed_exceptions=[ValueError],
                              title='Title')
        actual = put(get_foo, allowed_exceptions=[ValueError], title='Title')
        assert actual.method == expected.method
        assert actual.logic == expected.logic
        assert actual.logic._doctor_title == 'Title'
        assert actual.logic._doctor_allowed_exceptions == [ValueError]

    def test_create_routes(self):
        class MyHandler(Resource):
            pass

        routes = (
            Route('^/foo/?$', (
                get(get_foos, title='Retrieve List'),
                post(create_foo)), base_handler_class=MyHandler,
                handler_name='MyHandler', heading='Foo'),
            Route('^/foo/<int:foo_id>/?$', (
                delete(delete_foo),
                get(get_foo),
                put(update_foo)), heading='Foo'),
        )
        actual = create_routes(routes, handle_http, Resource)

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

        # verify heading attr was added to handler
        assert handler._doctor_heading == 'Foo'

        # verify params for get
        params = handler.get._doctor_params
        expected = Params(
            all=['is_alive'], required=[], optional=['is_alive'],
            logic=['is_alive'])
        assert expected == params

        # verify signature
        sig = handler.get._doctor_signature
        expected = inspect.signature(get_foos)
        assert expected == sig

        # verify custom title
        assert 'Retrieve List' == handler.get._doctor_title

        # verify params for post
        params = handler.post._doctor_params
        expected = Params(
            all=['name'], required=['name'], optional=[], logic=['name'])
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
