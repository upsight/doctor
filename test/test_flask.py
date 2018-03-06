import inspect
import os
from functools import wraps

import mock
import pytest

from doctor.flask import (
    handle_http, HTTP400Exception, should_raise_response_validation_errors)
from doctor.response import Response
from doctor.utils import (
    add_param_annotations, get_params_from_func, Params, RequestParamAnnotation)

from .types import Auth, Colors, Item, ItemId, IncludeDeleted


def check_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    params = [
        RequestParamAnnotation('auth', Auth, True),
    ]
    _wrapper = add_param_annotations(wrapper, params)
    return _wrapper


def get_item(item_id: ItemId, include_deleted: IncludeDeleted=False) -> Item:
    return {'item_id': 1}


def create_item(item: Item, colors: Colors) -> Item:
    return {'item_id': 1}


@pytest.fixture
def mock_request():
    mock_request_patch = mock.patch('doctor.flask.request')
    yield mock_request_patch.start()
    mock_request_patch.stop()


@pytest.fixture
def mock_get_logic():
    mock_logic = mock.MagicMock(spec=get_item, return_value={'item_id': 1})
    mock_logic._doctor_signature = inspect.signature(get_item)
    mock_logic._doctor_params = get_params_from_func(mock_logic)
    return mock_logic


@pytest.fixture
def mock_post_logic():
    mock_logic = mock.MagicMock(spec=create_item, return_value={'item_id': 1})
    mock_logic._doctor_signature = inspect.signature(create_item)
    mock_logic._doctor_params = get_params_from_func(mock_logic)
    return mock_logic


def test_handle_http_with_json(mock_request, mock_get_logic):
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.json = {'item_id': 1, 'include_deleted': True}
    mock_handler = mock.Mock()

    actual = handle_http(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 1}, 201)

    expected_call = mock.call(item_id=1, include_deleted=True)
    assert expected_call == mock_get_logic.call_args


def test_handle_http_object_array_types(mock_request, mock_post_logic):
    """
    This test verifies that we pass native types to the logic function rather
    than the doctor types that annotate the parameters of the logic function.
    This is done to prevent downstream issues from happening by passing say
    an Integer instance instead of an int to pymysql.  pymysql doesn't know
    about this type and tries to escape it like a string which causes an
    AttributeError.
    """
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.json = {'item': {'item_id': 1}, 'colors': ['blue', 'green']}

    mock_handler = mock.Mock()
    actual = handle_http(mock_handler, (), {}, mock_post_logic)
    assert actual == ({'item_id': 1}, 201)

    expected_call = mock.call(item={'item_id': 1}, colors=['blue', 'green'])
    assert expected_call == mock_post_logic.call_args

    # Verify we're passing native types and not doctor types to logic functions
    kwargs = mock_post_logic.call_args[1]
    assert type(kwargs['item']) is dict
    assert type(kwargs['colors']) is list


def test_handle_http_non_json(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 3}
    mock_handler = mock.Mock()

    actual = handle_http(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 1}, 200)

    expected_call = mock.call(item_id=3)
    assert expected_call == mock_get_logic.call_args


def test_handle_http_unsupported_http_method_with_body(
        mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.values = {'item_id': 3}
    mock_handler = mock.Mock()

    actual = handle_http(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 1}, 200)

    expected_call = mock.call(item_id=3)
    assert expected_call == mock_get_logic.call_args


def test_handle_http_missing_required_arg(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {}
    mock_handler = mock.Mock()

    with pytest.raises(HTTP400Exception, match='item_id is required'):
        handle_http(mock_handler, (), {}, mock_get_logic)


def test_handle_http_missing_multiple_required_args(
        mock_request, mock_post_logic):
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.json = {}

    mock_handler = mock.Mock()
    with pytest.raises(HTTP400Exception,
                       match="\['item', 'colors'\] are required."):
        handle_http(mock_handler, (), {}, mock_post_logic)


def test_handle_http_multiple_invalid_args(mock_request, mock_post_logic):
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.json = {'item': 1, 'colors': 'blue'}

    mock_handler = mock.Mock()
    expected_msg = ("{'item': 'Must be an object.', "
                    "'colors': 'Must be a list.'}")
    with pytest.raises(HTTP400Exception, match=expected_msg):
        handle_http(mock_handler, (), {}, mock_post_logic)


def test_handle_http_decorator_adds_param_annotations(
        mock_request, mock_get_logic):
    """
    This test verifies if a decorator uses doctor.utils.add_param_annotations
    to add params to the logic function that we fail to validate if the added
    params are missing or invalid.
    """
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 1}
    mock_handler = mock.Mock()
    logic = check_auth(get_item)

    expected_params = Params(all=['item_id', 'include_deleted', 'auth'],
                             optional=['include_deleted'],
                             required=['item_id', 'auth'],
                             logic=['item_id', 'include_deleted'])
    assert expected_params == logic._doctor_params
    with pytest.raises(HTTP400Exception, match='auth is required'):
        handle_http(mock_handler, (), {}, logic)

    # Add auth and it should validate
    mock_request.values = {'item_id': 1, 'auth': 'auth'}
    actual = handle_http(mock_handler, (), {}, logic)
    assert actual == ({'item_id': 1}, 200)


def test_handle_http_invalid_param(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 'string'}
    mock_handler = mock.Mock()

    with pytest.raises(HTTP400Exception, match='Must be a valid number.'):
        handle_http(mock_handler, (), {}, mock_get_logic)


@mock.patch('doctor.flask.current_app')
def test_handle_http_allowed_exception(mock_app, mock_request, mock_get_logic):
    mock_app.config = {'DEBUG': False}
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 1}
    mock_handler = mock.Mock()
    mock_get_logic.side_effect = ValueError('Allowed')
    mock_get_logic._doctor_allowed_exceptions = [ValueError]

    with pytest.raises(ValueError, match='Allowed'):
        handle_http(mock_handler, (), {}, mock_get_logic)


def test_handle_http_response_instance_return_value(
        mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.values = {'item_id': 3}
    mock_get_logic.return_value = Response({'item_id': 3}, {'X-Header': 'Foo'})
    mock_handler = mock.Mock()

    actual = handle_http(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 3}, 200, {'X-Header': 'Foo'})


def test_should_raise_response_validation_errors():
    assert should_raise_response_validation_errors() is False

    os.environ['RAISE_RESPONSE_VALIDATION_ERRORS'] = '1'
    assert should_raise_response_validation_errors() is True


@mock.patch('doctor.flask.current_app')
def test_handle_http_response_validation(
        mock_app, mock_request, mock_get_logic):
    mock_app.config = {'DEBUG': False}

    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 3}
    mock_handler = mock.Mock()
    mock_get_logic.return_value = {'foo': 'bar'}

    expected = ("{'item_id': 'This field is required.', "
                "'foo': 'Additional properties are not allowed.'}")
    with pytest.raises(HTTP400Exception, match=expected):
        handle_http(mock_handler, (), {}, mock_get_logic)

    # Should also work with the response is an instance of Response
    mock_get_logic.return_value = Response({'foo': 'bar'})
    with pytest.raises(HTTP400Exception, match=expected):
        handle_http(mock_handler, (), {}, mock_get_logic)
