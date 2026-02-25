import logging

from rest_framework.views import exception_handler
from rest_framework import status as http_status

logger = logging.getLogger("apps")

# Map HTTP status codes to readable error codes
STATUS_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "THROTTLED",
    500: "INTERNAL_ERROR",
}

# Default human-readable messages per code
DEFAULT_MESSAGES = {
    400: "The request was invalid or cannot be served.",
    401: "Authentication credentials were not provided or are invalid.",
    403: "You do not have permission to perform this action.",
    404: "The requested resource was not found.",
    405: "This HTTP method is not allowed on this endpoint.",
    429: "Too many requests. Please try again later.",
    500: "An unexpected internal server error occurred.",
}


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler that wraps all error responses in a
    standardized envelope:

    {
        "success": false,
        "error": {
            "code": "BAD_REQUEST",
            "message": "...",
            "details": { ... } or null
        }
    }
    """
    # Let DRF handle the exception first to get a Response object
    response = exception_handler(exc, context)

    if response is None:
        # DRF did not handle it (e.g. unhandled server error)
        # Return None so Django's default 500 handling kicks in
        return None

    status_code = response.status_code
    error_code = STATUS_CODE_MAP.get(status_code, f"ERROR_{status_code}")
    details = None
    message = DEFAULT_MESSAGES.get(status_code, "An error occurred.")

    # Extract meaningful message and details from the original response
    data = response.data

    if isinstance(data, dict):
        # DRF validation errors: {"field": ["error1", ...]}
        # or simple errors: {"detail": "..."}
        if "detail" in data:
            message = str(data["detail"])
        else:
            # Serializer validation errors — preserve as details
            details = data
            message = "Validation failed."
    elif isinstance(data, list):
        # Some DRF errors come as a list
        message = "; ".join(str(e) for e in data)

    # Log the error
    view_name = ""
    if context.get("view"):
        view_name = context["view"].__class__.__name__

    logger.log(
        logging.WARNING if status_code < 500 else logging.ERROR,
        "API error | view=%s | status=%s | code=%s | message=%s",
        view_name,
        status_code,
        error_code,
        message,
    )

    # Build standardized response
    response.data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
        },
    }

    return response
