"""Request correlation and structured request-response audit middleware (TASK-LOG-2)."""

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .logging import clear_log_context, set_log_context

logger = logging.getLogger("voiceclone.request")
security_logger = logging.getLogger("voiceclone.security")
error_logger = logging.getLogger("voiceclone.error")


def get_client_ip(request: HttpRequest) -> str:
    """Safely extract remote client IP address."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "-")


class RequestCorrelationMiddleware:
    """
    Middleware that:
    1. Extracts or generates an X-Request-ID for end-to-end tracing.
    2. Populates ContextVars for all downstream log entries.
    3. Measures and logs request latency, status code, IP, and user identity.
    4. Categorizes 4xx security rejections into security.log and 5xx into error.log.
    5. Appends X-Request-ID to outgoing HTTP headers for client correlation.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 1. Resolve or generate correlation request ID
        req_id = request.headers.get("X-Request-ID")
        if not req_id or len(req_id) > 64:
            req_id = f"req_{uuid.uuid4().hex[:16]}"
        request.request_id = req_id

        # 2. Extract user and client IP
        user_identifier = "anonymous"
        if hasattr(request, "user") and request.user.is_authenticated:
            user_identifier = str(request.user.username)
        set_log_context(req_id, user_identifier)

        client_ip = get_client_ip(request)
        start_time = time.time()

        # Log request entrance (DEBUG / INFO)
        logger.info("--> %s %s client=%s user=%s", request.method, request.path, client_ip, user_identifier)

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            error_logger.exception(
                "UNCAUGHT_EXCEPTION %s %s duration=%sms user=%s client=%s: %s",
                request.method,
                request.path,
                duration_ms,
                user_identifier,
                client_ip,
                str(exc),
            )
            clear_log_context()
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code

        # Post-authentication user check (e.g. after SessionAuthentication runs in view)
        if user_identifier == "anonymous" and hasattr(request, "user") and request.user.is_authenticated:
            user_identifier = str(request.user.username)
            set_log_context(req_id, user_identifier)

        # 4. Structured audit logging based on response status
        if status_code in (401, 403):
            security_logger.warning(
                "ACCESS_DENIED %s %s status=%d duration=%sms client=%s user=%s",
                request.method,
                request.path,
                status_code,
                duration_ms,
                client_ip,
                user_identifier,
            )
        elif status_code >= 500:
            error_logger.error(
                "SERVER_ERROR %s %s status=%d duration=%sms client=%s user=%s",
                request.method,
                request.path,
                status_code,
                duration_ms,
                client_ip,
                user_identifier,
            )
        else:
            logger.info(
                "<-- %s %s status=%d duration=%sms client=%s user=%s",
                request.method,
                request.path,
                status_code,
                duration_ms,
                client_ip,
                user_identifier,
            )

        # 5. Attach X-Request-ID header to client response
        response["X-Request-ID"] = req_id
        clear_log_context()
        return response
