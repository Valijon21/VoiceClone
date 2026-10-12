"""Structured log filters and context helpers for correlation tracing (TASK-LOG-1)."""

import contextvars
import logging

# Context variable preserving request correlation ID across async and thread boundaries
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")


def set_log_context(request_id: str, user_id: str = "anonymous") -> None:
    """Set correlation ID and user ID for current execution context."""
    request_id_ctx.set(request_id)
    user_id_ctx.set(user_id)


def clear_log_context() -> None:
    """Reset log context after request completes."""
    request_id_ctx.set("-")
    user_id_ctx.set("anonymous")


class CorrelationLogFilter(logging.Filter):
    """
    Injects request_id and user_id attributes into every log record.
    Ensures thread-safe, consistent log entries across all loggers.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id") or record.request_id == "-":
            record.request_id = request_id_ctx.get("-")
        if not hasattr(record, "user_id") or record.user_id == "anonymous":
            record.user_id = user_id_ctx.get("anonymous")
        return True
