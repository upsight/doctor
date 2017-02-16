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
