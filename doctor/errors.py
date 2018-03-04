from typing import Union


class TypeSystemError(Exception):
    """An error that represents an invalid value for a type.

    This is borrowed from apistar:
    https://github.com/encode/apistar/blob/master/apistar/exceptions.py#L1-L15

    :param detail: Detail about the error.
    :param cls: The class type that was being instantiated.
    :param code: The error code.
    :param errors: A dict containing all validation errors during the request.
        The key is the param name and the value is the error message.
    """
    def __init__(self,
                 detail: Union[str, dict]=None,
                 cls: type=None,
                 code: str=None, errors: dict=None) -> None:

        if cls is not None and code is not None:
            cls_errors = getattr(cls, 'errors')
            detail = cls_errors[code].format(**cls.__dict__)

        self.detail = detail
        self.errors = errors
        if errors and len(errors) == 1:
            param = list(errors.keys())[0]
            msg = list(errors.values())[0]
            detail = '{} - {}'.format(param, msg)
        super().__init__(detail)


class SchematicError(ValueError):
    """Base error class for doctor."""
    pass


class ForbiddenError(SchematicError):
    """Raised when a request is forbidden for the authorized user.

    Corresponds to a HTTP 403 Forbidden error.
    """
    pass


class ImmutableError(SchematicError):
    """Raised for immutable errors for a schema.

    Corresponds to a HTTP 409 Conflict error.
    """
    pass


class InvalidValueError(SchematicError):
    """
    Raised for errors when doing more complex validation that
    can't be done in a schema.

    Corresponds to a HTTP 400 Bad Request error.
    """
    pass


class NotFoundError(SchematicError):
    """Raised when a resource is not found.

    Corresponds to a HTTP 404 Not Found error.
    """
    pass


class ParseError(SchematicError):
    """Raised when a value cannot be parsed into an appropriate type."""
    pass


class SchemaError(SchematicError):
    """Raised for errors in a schema."""
    pass


class SchemaLoadingError(SchematicError):
    """Raised when loading a resource and it is invalid."""
    pass


class SchemaValidationError(SchematicError):
    """Raised for errors when validating things against a schema."""

    def __init__(self, message, errors=None):
        super(SchemaValidationError, self).__init__(message)
        self.errors = errors


class UnauthorizedError(SchematicError):
    """Raised when a request is unauthorized.

    Corresponds to a HTTP 401 Unauthorized error.
    """
    pass


class InternalError(SchematicError):
    """Raised when there is an internal server error.

    Corresponds to a HTTP 500 Internal Server Error.
    """
    pass
