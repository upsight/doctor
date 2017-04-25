.. _error-classes:

Error Classes
-------------

These error classes should be used in your :ref:`logic-functions` to abstract
out the HTTP layer.  Doctor provides custom exceptions which will be converted
to the correct HTTP Exception by the library. This allows logic functions to be
easily reused by other logic in your code base without it having knowledge of
the HTTP layer.

.. automodule:: doctor.errors
    :members:
    :private-members:
    :show-inheritance:
