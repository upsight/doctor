import inspect
import os


class RouterException(Exception):
    """
    An exception specific to errors that can occur in the
    :class:`~doctor.router.Router` class.
    """
    pass


class Router(object):
    """A class that creates routes.

    This class handles dynamically generating handlers for HTTP methods and
    mapping the route to a logic function.

    :param str schema_dir: The absolute path to directory that contains the
        schema files.
    :param class resource_schema_class: The class to use for the
        :class:`~doctor.resource.ResourceSchema` instance.
    :param class default_base_handler: The default base handler that should
        be subclassed when dynamically creating the handlers from the routes
        and logic functions.  This will default to `object` if not specified.
    :param bool raise_response_validation_errors: True to raise errors
        for response validation exceptions, False to just log them
        and return gracefully.
    """

    #: This attribute is incremented every time a new handler class is
    #: generated to ensure uniquness in the handler class names.
    _num = 1

    def __init__(self, schema_dir, resource_schema_class,
                 default_base_handler=None,
                 raise_response_validation_errors=False):
        self.resource_schema_class = resource_schema_class
        self.schema_dir = schema_dir
        self.schemas = {}
        self.raise_response_validation_errors = raise_response_validation_errors
        if default_base_handler is not None:
            self.default_base_handler = default_base_handler
        else:
            self.default_base_handler = object

    def get_schema(self, schema_file):
        """Gets the resource schema for the provided file.

        :param str schema_file: The name of the schema file to load from
            :attr:`~schema_dir`.  e.g. 'app.yaml'
        :returns: An instance of `self.resource_schema_class`.
        """
        if self.schemas.get(schema_file):
            return self.schemas.get(schema_file)
        self.schemas[schema_file] = self.resource_schema_class.from_file(
            os.path.join(self.schema_dir, schema_file),
            self.raise_response_validation_errors)
        return self.schemas[schema_file]

    def _undecorate_func(self, func):
        """Returns the original function from the decorated one.

        The purpose of this function is to return the original `func` in the
        event that it has decorators attached to it, instead of the decorated
        function.

        :param function func: The function to unwrap.
        :returns: The unwrapped function.
        """
        while True:
            if func.__closure__:
                for cell in func.__closure__:
                    if inspect.isfunction(cell.cell_contents):
                        if func.__name__ == cell.cell_contents.__name__:
                            func = cell.cell_contents
                            break
            else:
                break
        return func

    def _get_params_from_func(self, func, omit_args=None):
        """Gets all parameters and required parameters from the func signature.

        This assumes all arguments of a function that don't have default
        values are required, and all others are optional.

        :param function func: The function to collect arguments from.
        :param list(str) omit_args: A list of function args to omit when
            examining the function signature.
        :returns: A tuple containing all parameters of the function signature
            and all required args.
        """
        argspec = inspect.getargspec(self._undecorate_func(func))
        if argspec.defaults:
            required = argspec.args[:-len(argspec.defaults)]
        else:
            required = argspec.args[:]
        params = argspec.args
        if omit_args:
            required = [r for r in required if r not in omit_args]
            params = [p for p in argspec.args if p not in omit_args]
        return (params, required)

    def create_routes(self, docs_group_title, schema_file, routes):
        """Creates a new set of routes.

        Routes will be returned as a list of tuples containing the route and
        handler class to map to.  e.g.

        [
            ('^/app/<app_id:int>/?$', AppHandler),
            ('^/app/?$', AppListHandler),
        ]

        :param str docs_group_title: The documentation title to group the
            routes underneath.
        :param str schema_file: The name of the schema file to use for
            request parameter and response definitions.  e.g. `app.yaml`
        :param dict routes: A dict of routes.  See :ref:`routes-docs` for the
            definition of the dict and possible options.
        :returns: A list of tuples containing the route and handler.  See
            example above.
        """
        schema = self.get_schema(schema_file)
        created_routes = []
        for route, methods in routes.iteritems():
            handler = None
            base_handler_class = methods.pop('base_handler_class',
                                             self.default_base_handler)
            # If a handler_name isn't defined, dynmaically generate one.  We
            # append a number to the Handler class name to ensure uniqueness.
            handler_name = methods.pop('handler_name',
                                       'Handler{}'.format(self._num))
            handler_decorators = methods.pop('decorators', [])
            handler_additional_args = methods.pop('additional_args', {})
            for method in methods:
                opts = routes[route][method]
                method = method.lower()
                if 'logic' not in opts:
                    raise RouterException(
                        '`logic` key not defined for {}: {}'.format(
                            method, opts))

                # Retrieve all params and required params from the logic
                # function signature.
                omit_args = opts.get('omit_args')
                params, required = self._get_params_from_func(
                    opts['logic'], omit_args)
                # If additiona_args was passed update params and required.
                # These are additional arguments that should be documented for
                # the request, but are not part of the logic function's
                # signature.
                additional_args = opts.get('additional_args', {})
                additional_args.update(handler_additional_args)
                if additional_args:
                    params.extend(additional_args.get('optional', []))
                    params.extend(additional_args.get('required', []))
                    required.extend(additional_args.get('required', []))

                # Check if the schema was overridden for the method.
                if opts.get('schema'):
                    method_schema = self.get_schema(opts['schema'])
                else:
                    method_schema = schema

                http_func = getattr(method_schema, 'http_' + method)
                func = http_func(
                    opts['logic'], params=params, required=required,
                    response=opts.get('response'), title=opts.get('title'),
                    allowed_exceptions=opts.get('allowed_exceptions'))
                # Apply all decoraters to the `func`
                decorators = opts.get('decorators', [])
                decorators.extend(handler_decorators)
                for decorator in decorators:
                    func = decorator(func)
                handler_methods_and_properites = {
                    '__name__': handler_name,
                    method: func,
                    'schematic_title': docs_group_title,
                }
                # If this route has more than one http method just add the
                # new method to the existing handler.
                if handler is not None:
                    setattr(handler, method,
                            handler_methods_and_properites[method])
                    # This is specific to Flask.  It's MethodView class
                    # initializes the methods attribute in __new__ so we
                    # need to add all the other http methods we are defining
                    # on the handler after it gets created by type.
                    if hasattr(handler, 'methods'):
                        handler.methods.append(method.upper())
                else:
                    # Dynamically generate a handler class with the http
                    # method attached.
                    handler = type(
                        handler_name, (base_handler_class,),
                        handler_methods_and_properites)
                    # Increment `_num` so that the next handler name created
                    # is different from the previous.
                    self._num += 1
                opts['logic']._handler = handler
            created_routes.append((route, handler))
        return created_routes
