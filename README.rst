doctor
======

|docs|

This module assists in using JSON schemas to validate data in our Python APIs. 
It provides helpers for parsing and validating requests and responses in 
Flask apps, and also supports generic schema validation for plain dictionaries.

Documentation is available at readthedocs_

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
