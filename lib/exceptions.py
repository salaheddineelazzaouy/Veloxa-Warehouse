from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class DomainError(Exception):
    code = "DOMAIN_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, code=None):
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


class InsufficientStock(DomainError):
    code = "INSUFFICIENT_STOCK"
    status_code = status.HTTP_409_CONFLICT


class DuplicateReference(DomainError):
    code = "DUPLICATE_REFERENCE"
    status_code = status.HTTP_409_CONFLICT


class InvalidMovement(DomainError):
    code = "INVALID_MOVEMENT"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class PermissionDenied(DomainError):
    code = "PERMISSION_DENIED"
    status_code = status.HTTP_403_FORBIDDEN


class NotFound(DomainError):
    code = "NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


def custom_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": exc.code, "detail": exc.message},
            status=exc.status_code,
        )
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {"error": "NOT_FOUND", "detail": "Resource not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return exception_handler(exc, context)
