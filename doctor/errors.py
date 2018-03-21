from typing import Union


class DoctorError(ValueError):
    """Base error class for Doctor."""
    def __init__(self, message, errors: dict = None):
        self.errors = errors
        super().__init__(message)


#: Alias for DoctorError, for backwards compatibility.
SchematicError = DoctorError


class ForbiddenError(DoctorError):
    """Raised when a request is forbidden for the authorized user.

    Corresponds to a HTTP 403 Forbidden error.
    """
    pass


class ImmutableError(DoctorError):
    """Raised for immutable errors for a schema.

    Corresponds to a HTTP 409 Conflict error.
    """
    pass


class InternalError(DoctorError):
    """Raised when there is an internal server error.

    Corresponds to a HTTP 500 Internal Server Error.
    """
    pass


class InvalidValueError(DoctorError):
    """
    Raised for errors when doing more complex validation that
    can't be done in a schema.

    Corresponds to a HTTP 400 Bad Request error.
    """
    pass


class NotFoundError(DoctorError):
    """Raised when a resource is not found.

    Corresponds to a HTTP 404 Not Found error.
    """
    pass


class ParseError(DoctorError):
    """Raised when a value cannot be parsed into an appropriate type."""
    pass


class SchemaError(DoctorError):
    """Raised for errors in a schema."""
    pass


class SchemaLoadingError(DoctorError):
    """Raised when loading a resource and it is invalid."""
    pass


class SchemaValidationError(DoctorError):
    """Raised for errors when validating things against a schema."""

    def __init__(self, message, errors=None):
        super(SchemaValidationError, self).__init__(message)
        self.errors = errors


class TypeSystemError(DoctorError):
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
                 detail: Union[str, dict] = None,
                 cls: type = None,
                 code: str = None,
                 errors: dict = None) -> None:

        if cls is not None and code is not None:
            cls_errors = getattr(cls, 'errors')
            detail = cls_errors[code].format(**cls.__dict__)

        self.detail = detail
        if errors and len(errors) == 1:
            param = list(errors.keys())[0]
            msg = list(errors.values())[0]
            detail = '{} - {}'.format(param, msg)
        super().__init__(detail, errors=errors)


class UnauthorizedError(DoctorError):
    """Raised when a request is unauthorized.

    Corresponds to a HTTP 401 Unauthorized error.
    """
    pass
