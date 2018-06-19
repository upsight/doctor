import inspect
from typing import Callable

from doctor.utils import get_params_from_func


def add_doctor_attrs(func, req_obj_type: Callable = None):
    """Adds required _doctor* attrs to a function so it can be used in tests.

    :param req_obj_type: A doctor :class:`~doctor.types.Object` type that the
        request body should be converted to.
    """
    sig = inspect.signature(func)
    func._doctor_req_obj_type = req_obj_type
    params = get_params_from_func(func)
    func._doctor_allowed_exceptions = None
    func._doctor_signature = sig
    func._doctor_params = params
    return func
