.. _router-docs:

Router
======

The :class:`~doctor.router.Router` class dynamically generates
compatible handlers for doctor.  The 
:meth:`~doctor.router.Router.create_routes` method provides many
configuration options for the generated handler and associated methods.  Below
is an example using all configuration options.

.. code-block:: python

    from doctor.flask import FlaskResourceSchema

    from myapp.errors import MyException
    from myapp.handler import BaseHandler
    from myapp.logic import create_note, get_note

    router = Router('./schema_dir/', FlaskResourceSchema)
    routes = router.create_routes('Notes (v1)', 'notes.yaml', routes={
        '/notes/': {
            # Generated handler options
            'additional_args': {
                'required': ['auth'],
            },
            'base_handler_class': BaseHandler,
            'decorators': [check_auth],
            'handler_name': 'NoteListHandler',

            # Definitions of allowed http methods for the generated handler.
            'get': {
                'logic': get_note,
                'omit_args': ['page'],
            },
            'post': {
                'additional_args': {
                    'optional': ['source'],
                    'required': ['secret_token'],
                },
                'allowed_exceptions': [MyException],
                'decorators': [admin_required],
                'logic': create_note,
                'response': 'note',
                'title': 'Create Note',
            }
        }
    })

.. _routes-docs:

Routes
------

The `routes` argument to :meth:`~doctor.router.Router.create_routes`
takes a dictionary.  Let's examine it's structure.  The keys are simply routes
and the values are a dict of allowed http methods.  e.g.

.. code-block:: python

    {
         '/notes/': {
            # ... define allowed http methods and any optional handler options
         },
         '/note/<int:note_id>/': {
            # ...
        },
    }

Next let's take a look at the dictionary that is the value for each route key.
You must define a key for each allowable http method.  `delete`, `get`, `post`,
and `put` are supported.  Each key should have a dictionary as it's value and
should define at the very least a `logic` key whose value is the function to 
execute when that HTTP method is called for the route. See :ref:`HTTP Method Options <http-method-options>`
for all avalable options.  Expanding on the above example:

.. code-block:: python

    {
         '/notes/': {
            'get': {
                'logic': get_notes,
            },
            'post': {
                'logic': create_note,
            }
         },
         '/note/<int:note_id>/': {
            'delete': {
                'logic': delete_note,
            },
            'get': {
                'logic': get_note,
            },
            'put': {
                'logic': update_note,
            },
        },
    }

In addition to the keys that correspond to allowed http methods you can also
define several keys that will apply to the generated handler class and/or all
of it's http methods.  See :ref:`generated handler options <generated-handler-options>`
for a all available options.

.. _generated-handler-options:

Generated Handler Options
-------------------------

- `additional_args` is an optional dict that can contain keys `optional` and
  `required`.  The values for these keys should be a list of strings that are
  arguments that you want to be documented and validated on the request, but
  are not part of the logic function's signature.  An example scenario for this
  is when a decorator is used that authenticates a user and expects a specific
  parameter on the request that it uses to do authentication, but is not used
  in the logic function.  These additional arguments will be applied to all
  defined http methods for the route.
- `base_handler_class` is the class that should be used as the base class of
  the dynmaically generated handler  class.  This is only required if you 
  wanted to use a different base class than the default for a particular route.
- `decorators` is a list of decorators that should be applied to the generated
  handler method.  These are used for special cases where the decorator may
  need to access `self` of the handler.  The decorators will be applied in the
  order they appear in the list after any decorators declared on the http
  method if any.  These decorators will be applied to all defined http methods
  for the route.
- `handler_name` is the name that should be used for the generated handler class
  name.  By default the name will be `Handler{num}` where `num` is the current
  number of generated handlers.  This option is provided if you need control
  over the name of the handler for another purpose.

.. code-block:: python

    {
        '/notes/': {
            'additional_args': {
                'optional': ['source'],
                'required': ['auth'],
            },
            'base_handler_class': MyCustomBaseHandler,
            'decorators': [check_auth],
            'handler_name': 'NoteListHandlerV1',

            # all defined http methods for this route...
            'get': {
                # ...
            },
        }
    }

.. _http-method-options:

HTTP Method Options
-------------------

Each HTTP method defined for a route can use any of the following options for
additional configuration:

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

.. code-block:: python

    {
        '/notes/': {
            # Definitions of allowed http methods for the generated handler.
            'post': {
                'additional_args': {
                    'optional': ['source'],
                    'required': ['secret_token'],
                },
                'allowed_exceptions': [MyException],
                'decorators': [admin_required],
                'logic': create_note,
                'response': 'note',
                'title': 'Create Note',
            }
        }
    })

.. automodule:: doctor.router
    :members:
    :private-members:
    :show-inheritance:

