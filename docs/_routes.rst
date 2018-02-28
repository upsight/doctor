Creating Routes
---------------

Routes map a url to one or more HTTP methods which each map to a specific
logic function.  We define our routes by instantiating a :class:`~doctor.routing.Route`.
A :class:`~doctor.routing.Route` requires 2 arguments.  The first is the
URL-metching pattern e.g. `/foo/<int:foo_id>/`.  The second is a tuple of allowed
:class:`~doctor.routing.HTTPMethod` s for the matching pattern:
:func:`~doctor.routing.get`, :func:`~doctor.routing.post`,
:func:`~doctor.routing.put` and :func:`~doctor.routing.delete`.

The HTTP method functions take one required argument which is the
:ref:`logic function<logic-functions>` to call when the http method for that
uri is called.
