Creating Routes
---------------

Routes map a url to one or more HTTP methods which each map to a specific
logic function.  We define our routes by calling the 
:meth:`~doctor.router.Router.create_routes`
method and passing it the title for the group of routes, the yaml file to use
for the request and response definitions, and a dict of routes.  Full 
documentation on this topic can be found in the :ref:`router-docs` documentation.

The dict of routes is a dict that has the route as keys that map to another dict
where the keys are HTTP methods (delete, get, post, put). Note that the
note_id URL parameter in the route below is actually enumerated as a normal
param and is a required parameter. This is necessary to ensure that the
parameter is correctly coerced and passed to the logic functions. The HTTP
method keys map to another dict that contain options for that particular method.
The only required key is `logic` which is the logic function to execute when the
HTTP method is called for that route.  Below are all key/value pairs that can be
included in the HTTP method dict.

- `additional_args` is an optional dict that can contain keys `optional` and
  `required`.  The values for these keys should be a list of strings that are
  arguments that you want to be documented and validated on the request, but
  are not part of the logic function's signature.  An example scenario for this
  is when a decorator is used that authenticates a user and expects a specific
  parameter on the request that it uses to do authentication, but is not used
  in the logic function.
- `allowed_exceptions` should be an optional list of exception classes which
  should be re-raised. Uncaught exceptions will normally be turned into HTTP
  500 errors, but if an exception class is enumerated in this list, it will
  instead be re-raised.
- `decorators` is a list of decorators that should be applied to the generated
  handler method.  These are used for special cases where the decorator may
  need to access `self` of the handler.  The decorators will be applied in the
  order they appear in the list.
- `logic` is required and should be a function to execute when the HTTP method
  is called for the route.
- `omit_args` is a list of strings that correspond to logic function arguments
  that should be omitted when considering which values to require for the
  request parameters.  This would typically only be required if the logic
  function was decorated by another function that passed an additional
  argument to it that isn't an actual request paramter.
- `response` should be a key from the definitions section of the schema that
  identifies which definition should be used to validate the response returned
  by the logic function.
- `title` is a custom title to use as the header for the route/method.  If a
  title is not provided, one will be generated based on the http method. The
  automatic title will be one of `Retrieve`, `Delete`, `Create`, or `Update`.
