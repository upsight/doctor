import inspect

from doctor.utils import get_params_from_func


def add_doctor_attrs(func):
    """Adds required _doctor* attrs to a function so it can be used in tests."""
    sig = inspect.signature(func)
    params = get_params_from_func(func)
    func._doctor_signature = sig
    func._doctor_params = params
    return func
