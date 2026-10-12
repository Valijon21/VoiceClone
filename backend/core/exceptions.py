"""Structured DRF exception handler preventing secret leaks and returning uniform JSON errors."""

import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("voiceclone.api")


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Return unified structured error responses for all DRF views.

    Shape:
    {
        "error_code": "ERROR_NAME",
        "message": "Human-readable explanation",
        "details": { ... }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = "API_ERROR"
        message = "An error occurred during request processing."

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_code = "VALIDATION_ERROR"
            message = "The submitted data is invalid or malformed."
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = "AUTHENTICATION_REQUIRED"
            message = "Authentication credentials were not provided or are invalid."
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_code = "PERMISSION_DENIED"
            message = "You do not have permission to perform this action."
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "RESOURCE_NOT_FOUND"
            message = "The requested resource could not be found."
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_code = "RATE_LIMIT_EXCEEDED"
            message = "Request rate limit exceeded. Please retry later."

        details = response.data if isinstance(response.data, dict) else {"error": response.data}
        response.data = {
            "error_code": error_code,
            "message": message,
            "details": details,
        }
        return response

    # Unhandled 500 exceptions
    logger.exception("Unhandled server exception encountered", exc_info=exc)
    return Response(
        {
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please contact system support.",
            "details": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
