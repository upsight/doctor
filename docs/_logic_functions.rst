.. _logic-functions:

Logic Functions
---------------

Next, we'll also need some logic functions. doctor's :func:`~doctor.routing.create_routes`
generates HTTP handler methods that wrap normal Python callables, so the
code can focus on more logic and less on HTTP. These handlers and HTTP handler
methods will be automatically generated for you based on your defined routes.

The logic function signature will be used to determine what the request
parameters are for the route/HTTP method and to determine which are required.
Each parameter must specify a `type hint <https://docs.python.org/3/library/typing.html>`_
which is a sublcass of one of the :ref:`builtin doctor types<doctor-types>`.  
These types perform validation on the request parameters passed to the logic
function. See :ref:`doctor-types` for more information.
Any argument without a default value is considered required while others are
optional.  For example in the `create_note` function below, `body` would be a
required request parameter and `done` would be an optional request parameter.

To abstract out the HTTP layer in logic functions, doctor provides
custom exceptions which will be converted to the correct HTTP Exception by
the library.  See the :ref:`error-classes` documentation for
more information on which exception your code should raise.
