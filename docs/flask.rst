Using in Flask
==============

doctor provides some helpers to for usage in a flask-restful
application. You can find an example in
:download:`app.py <examples/flask/app.py>`. To run this application, you'll
first need to install both doctor, flask, and flask-restful. Then
run:

.. code-block:: bash

    python app.py

The application will be running on http://127.0.0.1:5000.

.. include:: _doctor_types.rst

.. include:: _logic_functions.rst

.. literalinclude:: examples/flask/app.py
    :start-after: mark-logic
    :end-before: # --

.. include:: _routes.rst

.. literalinclude:: examples/flask/app.py
    :start-after: mark-routes
    :end-before: # --

We then create our Flask app and add our created resources to it.  These
resources are created by calling :func:`~doctor.routing.create_routes` with
our routes we defined above.

.. literalinclude:: examples/flask/app.py
    :start-after: mark-app
    :end-before: # --

Passing Request Body as an Object to a Logic Function
-----------------------------------------------------

If you need to pass the entire request body as an object like parameter instead
of specifying each individual key in the logic function, you can specify which
type the body should conform to when defining your route.

.. code-block:: python

    # Define the type the request body should conform to.
    from doctor.types import integer, Object, string

    class FooObject(Object):
        description = 'A foo.'
        properties = {
            'name': string('The name of the foo.'),
            'id': integer('The ID of the foo.'),
        }
        required = ['id']

    # Define your logic function as normal.
    def update_foo(foo: FooObject):
        print(foo.name, foo.id)
        # ...

    # Defining the route, use `req_obj_type` kwarg to specify the type.
    from doctor import create_routes, put, Route

    create_routes((
        Route('/foo/', methods=[
            put(update_foo, req_obj_type=FooObject)]
        )
    ))

This allows you to simply send the following json body:

.. code-block:: json

    {
      "name": "a name",
      "id": 1
    }

Without specifying a value for `req_obj_type` when defining the route, you would
have to send a `foo` key in your json body for it to validate and properly
send the request data to your logic function:

.. code-block:: json

    {
      "foo": {
        "name": "a name",
        "id": 1
      }
    }


Adding Response Headers
-----------------------

If you need more control over the response, your logic function can return a
:class:`~doctor.response.Response` instance.  For example if you would like
to have your logic function force download a csv file you could do the following:

.. code-block:: python

    from doctor.response import Response

    def download_csv():
        data = '1,2,3\n4,5,6\n'
        return Response(data, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=data.csv',
        })

The :class:`~doctor.response.Response` class takes the response data as the
first parameter and a dict of HTTP response headers as the second parameter.
The response headers can contain standard and any custom values.

Response Validation
-------------------

doctor can also validate your responses.

Enabling
########

By default doctor will only raise exceptions for invalid response when there is a
truthy value for the environment variable `RAISE_RESPONSE_VALIDATION_ERRORS`.
This will cause a HTTP 400 error which wil give details on why the response is
not valid.  If either of those conditions are not true only a warning will be
logged.

Usage
#####

To tell doctor to validate a response you must define a return annotation on
your logic function.  Simply use doctor types to define a valid response and
annotate it on your logic function.

.. code-block:: python

    from doctor import types

    Color = types.enum('A color', enum=['blue', 'green'])
    Colors = types.array('Array of colors', items=Color)

    def get_colors() -> Colors:
        # ... logic to fetch colors
        return colors

The return value of `get_colors` will be validated against the type that we
created. If we have enabled raising response validation errors  and our
response does not validate, we will get a 400 response.  If the above example
returned an array with an integer like `[1]` our response would look like:

```
Response to GET /colors `[1]` does not validate: {0: 'Must be a valid choice.'}
```

Example API Documentation
-------------------------

This API documentation is generated using the ``autoflask`` Sphinx directive.
See the section on :doc:`docs` for more information.

.. autoflask::


Flask Module Documentation
--------------------------

.. automodule:: doctor.flask
    :members:
