Doctor Types
------------

:ref:`doctor types<doctor-types>` are classes that represent your request data
and your responses.  Each parameter of your logic function must specify a 
`type hint <https://docs.python.org/3/library/typing.html>`_
which is a sublcass of one of the :ref:`builtin doctor types<doctor-types>`.  
These types perform validation on the request parameters passed to the logic
function. See :ref:`doctor-types` for more information.

.. literalinclude:: examples/flask/app.py
    :start-after: mark-types
    :end-before: # --
