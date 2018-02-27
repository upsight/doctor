Generating API Documentation
============================

You can use Doctor to generate Sphinx documentation for your API. It
will introspect the list of routes for your Flask app, and will use
the values from your schema to generate a list of parameters for those routes.

For example, to generate API documentation for the example Flask app, you
would add ``doctor.docs.flask`` to the extensions list in Sphinx's
conf.py file:

.. code-block:: python

    extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.coverage',
        'sphinx.ext.viewcode',
        'doctor.docs.flask',
    ]

You'll also need to import and instantiate
:class:`~doctor.docs.flask.AutoFlaskHarness` in conf.py:

.. code-block:: python

    from doctor.docs.flask import AutoFlaskHarness
    autoflask_harness = AutoFlaskHarness(
        routes_filename='examples/flask/app.py',
        url_prefix='http://127.0.0.1:8080')

This harness class provides setup and teardown handlers that are used to load
your Flask application. The documentation directives use the harness to
introspect and make mock requests against your app. If you have custom setup
and teardown steps that you would like to take (such as loading fixtures into
a database), you can subclass it and customize it. Take a look at
:class:`~doctor.docs.base.BaseHarness` for a list of the hooks that
are available.

If you are adding extra logic to the harness and subclassing
:class:`~doctor.docs.flask.AutoFlaskHarness`, make note of the
signature of :func:`~doctor.docs.flask.AutoFlaskHarness.setup_app`.
The sphinx_app parameter is not the Flask application.  To access the Flask
application object, use `self.app`.  e.g.

.. code-block:: python

    from doctor.docs.flask import AutoFlaskHarness
    from myapp import db
    class MyCustomHarness(AutoFlaskHarness):
        def setup_app(self, sphinx_app):
            super(MyCustomHarness, self).setup_app(sphinx_app)
            with self.app.app_context():
                db.init_app(self.app) # initialize sqlalchemy db extension

Then, add an ``autoflask`` directive to one of your rst files:

.. code-block:: rst

    API Documentation
    -----------------

    .. autoflask::

When you run Sphinx, it will render documentation like this:

.. autoflask::

Grouping Related API Endpoints Under A Heading
----------------------------------------------

You can specify a heading to group together related api routes when generating
api documentation.  To do this, simply pass a value to the `heading` kwarg
when defining your Route.

.. code-block:: python

    from doctor.routing import delete, get, put, post, Route

    routes = (
        Route('/', methods=(
            get(status, title='Show API Version'),), heading='API Status'),
        Route('/note/', methods=(
            get(get_notes, title='Get Notes'),
            post(create_note, title='Create Note'), heading='Notes')
        ),
        Route('/note/<int:note_id>/', methods=(
            delete(delete_note, title='Delete Note'),
            get(get_note, title='Get Note'),
            put(update_note, title='Update Note'), heading='Notes')
        ),
    )

Customizing API Endpoint Headings
---------------------------------

You can specify a short title when creating the routes which will show up as a
sub link below the group heading.  To do this, pass a value to `title` kwarg
when defining your http methods for a route.  If a title is not provided, one 
will be generated based on the http method. The automatic title will be one of 
`Retrieve`, `Delete`, `Create`, or `Update`.

.. code-block:: python

    from doctor.routing import delete, get, put, post, Route

    routes = (
        Route('/', methods=(
            get(status, title='Show API Version'),)),
        Route('/note/', methods=(
            get(get_notes, title='Get Notes'),
            post(create_note, title='Create Note'))
        ),
        Route('/note/<int:note_id>/', methods=(
            delete(delete_note, title='Delete Note'),
            get(get_note, title='Get Note'),
            put(update_note, title='Update Note'))
        ),
    )

Overriding Example Values For Specific Endpoints
------------------------------------------------

Sometimes you need to set a very specific value for a parameter in a request
when generating documentation.  doctor supports this behavior by
using :func:`~doctor.docs.base.BaseHarness.define_example_values`.
This method allows you to override parameters on a per request basis.  To do
this subclass the :class:`~doctor.docs.flask.AutoFlaskHarness`
and override the :func:`~doctor.docs.base.BaseHarness.setup_app`
method.  Then you can define example values for a particular route and method.

.. code-block:: python

    from doctor.docs.flask import AutoFlaskHarness

    class MyHarness(AutoFlaskHarness):
        def setup_app(self, sphinx_app):
            super(MyHarness, self).setup_app(sphinx_app)
            self.define_example_values('GET', '^/foo/bar/?$', {'foobar': 1})

The above code sample will change the parameters sent when sending a `GET`
request to `/foo/bar` when generating documentation for that route.  You can
call this method for as many routes as you need to provide custom parameters.

Remember if you create your own harness you'll need to update the harness class
that you instantiate in `conf.py`.

.. note:: For a flask api the 2nd parameter passed to 
          :func:`~doctor.docs.base.BaseHarness.define_example_values`
          is the route pattern as a string.  e.g. `/foo/bar/`.

Documenting and Sending Headers on Requests
-------------------------------------------

If you need to pass header values for a request you can define them in two ways.

The first method will add the header to all requests when generating
documentation.  An example where this may be useful is an Authorization header.
To add this simply define a `headers` dict on your harness.  If you would like
to provide a definition in the documentation for the header, also define a
`header_definitions` dict where the header key matches the header you wish to
document.

.. code-block:: python

    from doctor.docs.flask import AutoFlaskHarness

    class MyHarness(AutoFlaskHarness):
        headers = {'Authorization': 'testtoken'}
        header_definitions = {
            'Authorization': 'The auth token for the authenticated user.'}

        def setup_app(self, sphinx_app):
            super(MyHarness, self).setup_app(sphinx_app)

If you need to define a header for a specific route and method you can set
those up in your harness using :func:`~doctor.docs.base.BaseHarness.define_header_values`.

.. code-block:: python

    from doctor.docs.flask import AutoFlaskHarness

    class MyHarness(AutoFlaskHarness):
        headers = {'Authorization': 'testtoken'}
        header_definitions = {
            'Authorization': 'The auth token for the authenticated user.',
            'X-GeoIp-Country': 'An ISO 3166-1 alpha-2 country code.'}

        def setup_app(self, sphinx_app):
            super(MyHarness, self).setup_app(sphinx_app)
            self.define_header_values('GET', '/foo/bar/', {'X-GeoIp-Country': 'US'})

The above harness will send the `Authorization` header on all requests and will
additionally send the `X-GeoIp-Country` header on a GET request to `/foo/bar/`.


Module Documentation
--------------------

.. automodule:: doctor.docs.base
    :members:
    :private-members:
    :show-inheritance:

.. automodule:: doctor.docs.flask
    :members:
    :private-members:
    :show-inheritance:
