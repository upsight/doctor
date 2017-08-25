doctor
======
|docs| |build| |pypi|

This module allows you to use JSON schemas to validate data in Flask Python APIs 
and auto generate documentation.  An example of the generated API documentation can 
be `found in the docs <http://doctor.readthedocs.io/en/latest/flask.html#example-api-documentation>`_.
It also provides helpers for parsing and validating requests and responses in 
Flask apps, and supports generic schema validation for plain dictionaries.

Install
-------

doctor can easily be installed using pip:

    $ pip install doctor
   
Quick Start
-----------

Create a json schema with a few definitions to describe our request parameters.

.. code-block:: yaml

    ---
    $schema: 'http://json-schema.org/draft-04/schema#'
    definitions:
      foo_id:
        description: The ID of the foo.
        type: integer
        example: 1
      fetch_bars:
        description: Fetches bars associated with a Foo.
        type: boolean
        example: true
        
Define the logic function that our endpoint will route to:

.. code-block:: python

    def get_foo(foo_id, fetch_bars=False):
        """Fetches the Foo object and optionally related bars."""
        return Foo.get_by_id(foo_id, fetch_bars=fetch_bars)
        
Now tie the endpoint to the logic function with a router.

.. code-block:: python

    from flask import Flask
    from flask_restful import Api
    from doctor.flask import FlaskRouter
    
    all_routes = []
    router = FlaskRouter('/path/to/schema/dir')
    all_routes.extend(router.create_routes('Foo (v1)', 'foo.yaml', {
        '/foo/<int:foo_id>/': {
            'get': {
                'logic': get_foo,
            },
        },
    }))
    
    app = Flask(__name__)
    api = Api(app)
    for route, resource in routes:
        api.add_resource(resource, route)
    
That's it, you now have a functioning API endpoint you can curl and the request is automatically validated for you based on your
schema.  Positional arguments in your logic function are considered required request parameters and keyword arguments are considered
optional.  As a bonus, using the `autoflask <http://doctor.readthedocs.io/en/latest/docs.html>`_ sphinx directive, you will also get
automatically generated API documentation.
   
Documentation
-------------

Documentation and a full example is available at readthedocs_.
   
Running Tests
-------------

Tests can be run with tox_. It will handle installing dependencies into a
virtualenv, running nosetests, and rebuilding documentation.

Then run Tox:

.. code-block:: bash

    cd doctor
    tox


You can pass arguments to nosetests directly:

.. code-block:: bash

    tox -- test/test_flask.py


.. _readthedocs: http://doctor.readthedocs.io/en/latest/index.html
.. _tox: https://testrun.org/tox/latest/

.. |docs| image:: https://readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: http://doctor.readthedocs.io/en/latest/index.html
    
.. |build| image:: https://api.travis-ci.org/upsight/doctor.svg?branch=master
    :alt: Build Status
    :scale: 100%
    :target: https://travis-ci.org/upsight/doctor
    
.. |pypi| image:: https://img.shields.io/pypi/v/doctor.svg
    :alt: Pypi
    :scale: 100%
    :target: https://pypi.python.org/pypi/doctor/
