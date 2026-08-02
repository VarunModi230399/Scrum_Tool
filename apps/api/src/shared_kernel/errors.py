class AppError(Exception):
    """Base class for domain/application errors that map to a client-facing API error."""

    code = "UNKNOWN_ERROR"
    status_code = 500

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


class UnauthenticatedError(AppError):
    code = "UNAUTHENTICATED"
    status_code = 401
