import inspect
import os
from unittest import mock

import pytest

from doctor.flask import (
    handle_http_v3, HTTP400Exception, should_raise_response_validation_errors)
from doctor.response import Response
from doctor.router_v3 import get_params_from_func
from doctor.types import integer, boolean, Object, new_type


ItemId = integer('item id', minimum=1)
Item = new_type(Object, 'item', properties={'item_id': ItemId},
                additional_properties=False, required=['item_id'])
IncludeDeleted = boolean('indicates if deleted items should be included.')
IsDeleted = boolean('Indicates if the item should be marked as deleted')


def get_item(item_id: ItemId, include_deleted: IncludeDeleted=False) -> Item:
    return {'item_id': 1}


@pytest.fixture
def mock_request():
    mock_request_patch = mock.patch('doctor.flask.request')
    yield mock_request_patch.start()
    mock_request_patch.stop()


@pytest.fixture
def mock_get_logic():
    mock_logic = mock.Mock(spec=get_item, return_value={'item_id': 1})
    mock_logic._doctor_signature = inspect.signature(get_item)
    mock_logic._doctor_params = get_params_from_func(mock_logic)
    return mock_logic


def test_handle_http_with_json(mock_request, mock_get_logic):
    mock_request.method = 'POST'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.json = {'item_id': 1, 'include_deleted': True}
    mock_handler = mock.Mock()

    actual = handle_http_v3(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 1}, 201)

    expected_call = mock.call(item_id=1, include_deleted=True)
    assert expected_call == mock_get_logic.call_args


def test_handle_http_non_json(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 3}
    mock_handler = mock.Mock()

    actual = handle_http_v3(mock_handler, (), {}, mock_get_logic)
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

    actual = handle_http_v3(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 1}, 200)

    expected_call = mock.call(item_id=3)
    assert expected_call == mock_get_logic.call_args


def test_handle_http_missing_required_arg(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {}
    mock_handler = mock.Mock()

    with pytest.raises(HTTP400Exception, match='item_id is required'):
        handle_http_v3(mock_handler, (), {}, mock_get_logic)


def test_handle_http_invalid_param(mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/x-www-form-urlencoded'
    mock_request.values = {'item_id': 'string'}
    mock_handler = mock.Mock()

    with pytest.raises(HTTP400Exception, match='Must be a valid number.'):
        handle_http_v3(mock_handler, (), {}, mock_get_logic)


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
        handle_http_v3(mock_handler, (), {}, mock_get_logic)


def test_handle_http_response_instance_return_value(
        mock_request, mock_get_logic):
    mock_request.method = 'GET'
    mock_request.content_type = 'application/json; charset=UTF8'
    mock_request.mimetype = 'application/json'
    mock_request.values = {'item_id': 3}
    mock_get_logic.return_value = Response({'item_id': 3}, {'X-Header': 'Foo'})
    mock_handler = mock.Mock()

    actual = handle_http_v3(mock_handler, (), {}, mock_get_logic)
    assert actual == ({'item_id': 3}, 200, {'X-Header': 'Foo'})


@mock.patch('doctor.flask.current_app')
def test_should_raise_response_validation_errors(mock_app):
    mock_app.config = {'DEBUG': False}
    assert should_raise_response_validation_errors() is False

    mock_app.config = {'DEBUG': True}
    assert should_raise_response_validation_errors() is True

    mock_app.config = {'DEBUG': False}
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
        handle_http_v3(mock_handler, (), {}, mock_get_logic)

    # Should also work with the response is an instance of Response
    mock_get_logic.return_value = Response({'foo': 'bar'})
    with pytest.raises(HTTP400Exception, match=expected):
        handle_http_v3(mock_handler, (), {}, mock_get_logic)
