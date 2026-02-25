import logging
import time

logger = logging.getLogger("apps")


class RequestLoggingMiddleware:
    """
    Production-grade request logging middleware.
    Logs: user, method, path, status, and execution duration (ms).
    Does NOT log request bodies, passwords, tokens, or headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()

        response = self.get_response(request)

        duration_ms = (time.monotonic() - start_time) * 1000

        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = request.user.pk

        method = request.method
        path = request.path
        status = response.status_code

        log_level = logging.INFO
        if 400 <= status < 500:
            log_level = logging.WARNING
        elif status >= 500:
            log_level = logging.ERROR

        logger.log(
            log_level,
            "user=%s | method=%s | path=%s | status=%s | duration=%.0fms",
            user_id,
            method,
            path,
            status,
            duration_ms,
        )

        return response
