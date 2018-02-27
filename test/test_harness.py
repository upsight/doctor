import pytest

from doctor.docs.base import BaseHarness
from doctor.resource import ResourceAnnotation

from .types import Age, Color, ItemId, Name
from .utils import add_doctor_attrs


@pytest.fixture
def annotation():
    def logic(age: Age, name: Name, item_id: ItemId=None, color: Color='green'):
        pass

    logic = add_doctor_attrs(logic)
    annotation = ResourceAnnotation(logic, 'GET')
    return annotation


def test_get_example_values(annotation):
    harness = BaseHarness('/api')
    route = '/foo'
    actual = harness._get_example_values(route, annotation)
    expected = {
        'age': 34,
        'color': 'blue',
        'item_id': 1,
        'name': 'John',
    }
    assert expected == actual
