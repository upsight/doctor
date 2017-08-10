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

.. include:: _schema.rst

.. include:: _logic_functions.rst

.. literalinclude:: examples/flask/app.py
    :start-after: mark-logic
    :end-before: # --

.. include:: _routes.rst

Finally, we specify the routes and create the application. The first step is
initializing the :class:`~doctor.flask.FlaskRouter` class.
We must pass the absolute path to the directory where all of our schema
files reside.


.. literalinclude:: examples/flask/app.py
    :start-after: mark-app
    :end-before: # --

Adding Response Headers
-----------------------

If you need more control over the response, your logic function can return a
:class:`~doctor.flask.FlaskResponse` instance.  For example if you would like
to have your logic function force download a csv file you could do the following:

.. code-block:: python

    from doctor.flask import FlaskResponse

    def download_csv():
        data = '1,2,3\n4,5,6\n'
        return FlaskResponse(
            data, content_type='text/csv', 
            content_disposition='attachment; filename=data.csv')

See :class:`~doctor.response.Response` for all possible response headers that
:class:`~doctor.flask.FlaskResponse` can be instantiated with.

Example API Documentation
-------------------------

This API documentation is generated using the ``autoflask`` Sphinx directive.
See the section on :doc:`docs` for more information.

.. autoflask::


Flask Module Documentation
--------------------------

.. automodule:: doctor.flask
    :members:

.. automodule:: doctor.response
    :members:
