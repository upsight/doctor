Release History
===============

Next release (in development)
-----------------------------

v1.2.1 (2017-07-07)
-------------------

- Fixed sphinx build error encountered on Sphinx v1.6.1+ when checking if the
  http domain has already been added.

v1.2.0 (2017-07-07)
-------------------

- Added support for Python 3.

v1.1.4 (2017-05-04)
-------------------

- Updates doctor to not parse json bodies on GET/DELETE requests, and instead
  try to parse them from the query string or form parameters.
- Fixes a bug introducded in v1.1.3. This bug would only occur if a
  logic function was decorated and that decorator passed a positional
  argument to the logic function. Doctor would think the positional
  argument passed by the decorator was a required request parameter even
  if it was specified to be omitted in the router using omit_args.

v1.1.3 (2017-04-28)
-------------------

- Added new InternalError class to represent non-doctor internal errors.
- Updated sphinx pin version to be minimum 1.5.4 and added new `env` kwarg
  to make_field amd make_xref.
- Fixed bug where extra parameters passed on json requests would cause a `TypeError`
  if the logic function used a decorator.
- Made sure to make decorators a set when applying them to a logic function
  when creating routes.  This is to prevent a decorator from wrapping a 
  function twice if it's defined at the logic level and handler level when
  creating routes.

v1.1.2 (2017-02-27)
-------------------

- Fixes a bug where the logic function wouldn't be undecorated properly.

v1.1.1 (2017-02-27)
-------------------

- Made logic function exceptions always raise when applicaiton is in
  debug mode.
- Updated error message to be clearer when a logic function raises an
  exception.

v1.1.0 (2017-02-20)
-------------------

- Added ability to override the schema used for an individual endpoint.

v1.0.1 (2017-02-17)
-------------------

- Making required changes to setup.py for pypi.

v1.0.0 (2017-02-16)
--------------------

- Initial release.
