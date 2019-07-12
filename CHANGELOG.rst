Release History
===============

Next release (in development)
-----------------------------

v3.13.5 (2019-07-12)
--------------------

* Fixed incorrect type hint.

v3.13.4 (2019-07-12)
--------------------

* Fixed a few incorrect type hints.

v3.13.3 (2019-07-12)
--------------------

* Fixed missing import.

v3.13.2 (2019-07-12)
--------------------

* Fixed return types for quick type functions. mypy does not support more
  strict typing when using the builtin `type` function to dynamically
  generate a class.  The only way for it to not complain about these
  functions it to omit the the return type or specify `typing.Any`.

v3.13.1 (2019-07-03)
--------------------

* Implemented PEP-561 using inline type hints.

v3.13.0 (2019-04-29)
--------------------

* Added case_insensitive option to Enum type.
* Added lowercase_value option to Enum type.
* added uppercase_value option to Enum type.

v3.12.3 (2019-04-22)
--------------------

* Fixed a bug that caused object reference links to be duplicated when documenting
  a request param or response property that was a list of dicts.

v3.12.2 (2019-02-04)
--------------------

* Fixed a bug when using `new_type` that did not copy all attributes of
  the class being passed to it.  See issue #123 for more details.

v3.12.1 (2019-01-11)
--------------------

* Removed syntax for variable annotations and switched back to mypy comment hints in
  order to support python versions >= 3.5 and < 3.6

v3.12.0 (2019-01-11)
--------------------

* Added ability to add custom validation to types.
* Fixed bug where you could not specify a custom description when using
  the `new_type` type function when the type provided had it's own description
  attribute.

v3.11.0 (2019-01-04)
--------------------

* Document default values for optional request params by inspecting
  the logic function signature.

v3.10.3 (2018-12-12)
--------------------

* Fixed UnionType types from not getting passed to logic functions.
* Fixed UnionType types from not getting documented in api docs.
* Fixed bug with native_type for UnionType which could cause an error parsing
  the value, even if it conformed to one of the n types defined.

v3.10.2 (2018-12-10)
--------------------

* Fixed bug introducded in v3.10.1 when doctor attempted to generate api
  documentation when an endpoint had a request parameter that was an array of
  objects.

v3.10.1 (2018-12-07)
--------------------

* Fixed bug when using UnionType as it was missing a `native_type` attribute.
* Fixed bug when using Array where items is a list of types for each index.
  Documentation was generating exceptions when processing an annotation using
  this type.
* Added ability to document what type(s) an array's items are in the api
  documentation.

v3.10.0 (2018-11-28)
--------------------

* Added optional `parser` attribute to doctor types that allows the ability
  to specify a callable to parse the request parameter before it gets validated.
  See the documentation for more information.

v3.9.0 (2018-07-13)
-------------------

* Added new `UnionType` to types that allows a value to be one of `n` types.
* Don't filter out request parameters not defined in the type object for routes
  that specify a `req_obj_type`.

v3.8.2 (2018-07-02)
-------------------

* Added JSON body to error message when parsing JSON fails.
* Fixed bug that caused AttributError when creating routes in flask >= 1.0.0

v3.8.1 (2018-06-26)
-------------------

* Fixed an `AttributeError` when a logic function contained a parameter in it's
  signature that was not annotated by a doctor type and a request parameter
  in a form or query request also contained a variable that matched it's name.

v3.8.0 (2018-06-21)
-------------------

* Added ability to specify a callable that can be run before and/or after
  a logic function is called when defining a route.  See documentation for
  an example.

v3.7.0 (2018-06-19)
-------------------

* Added ability to specify for a particular route a request Object type that
  a json body should be validated against and passed to the logic function.
  This allows the base json body to be passed as a parameter without having
  to have the logic function variable match a request parameter.  The full
  json body will simply be passed as the first parameter to the logic function.

v3.6.1 (2018-05-21)
-------------------

* Fixed bug when documenting resource objects where we should have been
  calling Object.get_example() instead of constructing it ourselves from
  the object's properties.  That is what `get_example` does behind the scenes,
  but it will also use a user defined example if one is available. This is
  especially useful for Object's without any properties that you still want to
  document an example for.

v3.6.0 (2018-05-16)
-------------------

* Added the ability to document object resources in the api documentation.
  Any api endpoints that have an object or an array of objects in it's request
  parameters will include a link to the documentation about the object.

v3.5.0 (2018-05-11)
-------------------

* Added ability to specify which request parameter a type should map to it's
  annotated logic function variable.  See `param_name` in the types 
  documentation for more information.

v3.4.0 (2018-05-04)
-------------------

* Added long description to setup.py for pypi rendering.

v3.3.0 (2018-05-04)
-------------------

- Updated API documentation to also include a link to the logic function
  associated with the endpoint being documented.

v3.2.0 (2018-03-22)
-------------------

- Added ability to validate/document content of Response instances.

v3.1.0 (2018-03-21)
-------------------

- Renamed base error class to DoctorError and made TypeSystemError also
  inherit from DoctorError. DoctorError is still aliased as SchematicError
  for backwards compatibility.
- Added errors property to base DoctorError, so all Doctor errors can include
  additional details in a standard way.

v3.0.1 (2018-03-19)
-------------------

- Fixed the enum type to include possible choices in error message.

v3.0.0 (2018-03-13)
-------------------

- First public release of v3.0.0

v3.0.0-beta.7 (2018-03-12)
--------------------------

- Updates parsing of query/form params to parse null values properly.
- Makes a copy of the logic function to preserve doctor attributes if
  the logic function is shared between routes.

v3.0.0-beta.6 (2018-03-08)
--------------------------

- Updated handle_http to parse query and form parameters from strings to
  their expected type before we do validation on them.
- Fixed issue where if multiple decorators were used on a logic function
  and each one added param annotations the outer most decorator would
  erase any param annotations added from the previous decorator.
- Added a nullable attribute to all types to signify that None is a valid value
  for the type, in addition to it's native type.


v3.0.0-beta.5 (2018-03-05)
--------------------------

- Fixed doctor attempting to document non doctor type params (#70)
- String with format of date now returns datetime.date (#69)
- Fixed swallowing of TypeError from SuperType class in Object init (#68)
- Changed the flask code to only raise response validation errors if an
  environment variable is set. Before it also raised them when DEBUG
  was True in the config. In practice this was incredibly annoying and
  slowed down development. Especially in the case where a datetime
  string was returned that didn't include timezone information. Updated
  the docs to reflect this too.
- Fixed issue that could create duplicate handler names which would
  cause an exception in flask restful (#67 )
- Made the `JsonSchema` doctor type work in validating/coercing params
  in the api and for generating api documentation.

v3.0.0-beta.4 (2018-03-02)
--------------------------

- Made validation errors better when raising http 400 exceptions.  They now
  will display all missing required fields and all validation errors along with
  have the param in the error message.
- Fixed issue with doctor types being passed to logic functions.  Instead the
  native types are now passed to prevent downstream issues from other code
  encountering unexpected/unknown types.

v3.0.0-beta.3 (2018-02-28)
--------------------------

- Added default example values for all doctor types.
- Documentation updates
- Updated doctor code to work agnostic of the framework so eventually
  other backends than flask could be used.

V3.0.0-beta (2018-02-27)
------------------------

- First beta release of 3.0. This is a backwards incompatible change.  It drops
  support for python 2 and defining request parameters through the usage of json
  schemas. It's still possible to use the json schemas from previous versions
  of doctor to generate new doctor types using doctor.types.json_schema_type.
  See the documentation for more information.


v1.4.0 (2018-03-13)
-------------------

- Added status_code to Response class.

v1.3.5 (2018-01-23)
-------------------

- Fixed a few deprecation warnings about inspect.getargspec when running
  doctor using python 3.  It will now use inspect.getfullargspec.  This
  also fixes the issue of not being able to use type hints on logic functions
  in python 3.

v1.3.4 (2017-12-04)
-------------------

- Removed set operation on decorators when applying them to the logic function.
  Since set types don't have an explicit order it caused unpredicatable
  behavior as the decorators weren't always applied to the logic function
  in the same order with every call.

v1.3.3 (2017-10-18)
-------------------

- Add request option to router HTTP method dictionary, which allows you to
  override the schema used to validate the request body.

v1.3.2 (2017-09-18)
-------------------

- Fixed response validation when the response was an instance of
  doctor.response.Response

v1.3.1 (2017-08-29)
-------------------

- Fixed bug when auto generating documentation for GET endpoints that contained
  a parameter that was an array or object.  It wasn't getting json dumped, so
  when the request was made to generate the example response it would get a
  400 error.
- Fixed a few typos and bugs in the README quick start example.

v1.3.0 (2017-08-11)
-------------------

- Added a Response class that can be returned from logic functions in order
  to add/modify response headers.

v1.2.2 (2017-07-10)
-------------------

- More fixes for Python 3.

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
