import inspect
from unittest import mock

import pytest

from doctor.flask import handle_http_v3, HTTP400Exception
from doctor.response import Response
from doctor.router_v3 import get_params_from_func
from doctor.types import integer, boolean, Object, new_type


ItemId = integer('item id', minimum=1)
Item = new_type(Object, 'item', properties={'item_id': ItemId})
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
