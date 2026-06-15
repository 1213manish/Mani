"""
Custom exception handler for DRF.
Returns consistent error response format across the API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Returns errors in the format:
    {
        "error": "Human readable message",
        "code": "ERROR_CODE",
        "details": {...}
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "error": "An error occurred",
            "code": "ERROR",
            "details": response.data,
        }

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data["error"] = "Validation failed"
            error_data["code"] = "VALIDATION_ERROR"
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_data["error"] = "Authentication required"
            error_data["code"] = "AUTHENTICATION_REQUIRED"
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            error_data["error"] = "Permission denied"
            error_data["code"] = "PERMISSION_DENIED"
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            error_data["error"] = "Resource not found"
            error_data["code"] = "NOT_FOUND"
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            error_data["error"] = "Rate limit exceeded"
            error_data["code"] = "RATE_LIMITED"

        response.data = error_data

    return response
