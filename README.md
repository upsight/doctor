doctor
======

This module assists in using JSON schemas to validate data in our Python APIs. 
It provides helpers for parsing and validating requests and responses in 
Flask apps, and also supports generic schema validation for plain dictionaries.

Documentation is available [at readthedocs][docs].

Running Tests
-------------

Tests can be run with [Tox]. It will handle installing dependencies into a
virtualenv, running nosetests, and rebuilding documentation.

Then run Tox:

```bash
cd doctor
tox
```

You can pass arguments to nosetests directly:

```bash
tox -- test/test_flask.py
```

[docs]: https://readthedocs.com
[tox]: https://testrun.org/tox/latest/
