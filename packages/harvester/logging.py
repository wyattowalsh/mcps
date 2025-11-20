"""Structured logging configuration for MCPS.

This module provides production-ready logging with:
- Structured JSON logging for production environments
- Request ID tracking for distributed tracing
- Correlation IDs for multi-service requests
- Log aggregation support (ELK, Loki, CloudWatch)
- Contextual logging with metadata
- Performance-optimized log formatting
"""

import contextvars
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from .settings import settings

# Context variables for distributed tracing
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
correlation_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
user_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)


# =============================================================================
# Structured Log Formatting
# =============================================================================


def json_formatter(record: Dict[str, Any]) -> str:
    """Format log record as JSON for production environments.

    Args:
        record: Log record dictionary from loguru

    Returns:
        JSON-formatted log string
    """
    # Extract contextual information
    request_id = request_id_ctx.get()
    correlation_id = correlation_id_ctx.get()
    user_id = user_id_ctx.get()

    # Build structured log entry
    log_entry = {
        # Timestamp
        "timestamp": record["time"].isoformat(),
        "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        # Log level
        "level": record["level"].name,
        "severity": record["level"].name,  # For GCP compatibility
        # Message
        "message": record["message"],
        # Source information
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        # Process information
        "process": record["process"].id if record["process"] else None,
        "thread": record["thread"].id if record["thread"] else None,
        # Distributed tracing
        "request_id": request_id,
        "correlation_id": correlation_id,
        "user_id": user_id,
        # Environment
        "environment": settings.environment,
        "service": "mcps",
    }

    # Add exception information if present
    if record["exception"]:
        exc_type, exc_value, exc_tb = record["exception"]
        log_entry["exception"] = {
            "type": exc_type.__name__ if exc_type else None,
            "message": str(exc_value),
            "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        }

    # Add extra fields
    if record["extra"]:
        log_entry["extra"] = record["extra"]

    return json.dumps(log_entry, default=str)


def text_formatter(record: Dict[str, Any]) -> str:
    """Format log record as human-readable text for development.

    Args:
        record: Log record dictionary from loguru

    Returns:
        Formatted log string
    """
    # Get contextual information
    request_id = request_id_ctx.get()
    correlation_id = correlation_id_ctx.get()

    # Build context string
    context_parts = []
    if request_id:
        context_parts.append(f"req={request_id[:8]}")
    if correlation_id:
        context_parts.append(f"corr={correlation_id[:8]}")

    context = f" [{' '.join(context_parts)}]" if context_parts else ""

    # Format message
    time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = record["level"].name.ljust(8)
    location = f"{record['module']}:{record['function']}:{record['line']}"

    message = f"{time_str} | {level} | {location}{context} | {record['message']}"

    # Add exception if present
    if record["exception"]:
        exc_type, exc_value, exc_tb = record["exception"]
        message += "\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    return message


# =============================================================================
# Logger Configuration
# =============================================================================


def configure_logging() -> None:
    """Configure logging based on environment settings.

    This function should be called once at application startup.
    """
    # Remove default logger
    logger.remove()

    # Determine log format
    if settings.log_format == "json":
        formatter = json_formatter
    else:
        formatter = text_formatter

    # Console logging
    logger.add(
        sys.stderr,
        format=formatter,
        level=settings.log_level,
        colorize=settings.log_format == "text" and sys.stderr.isatty(),
        backtrace=settings.environment == "development",
        diagnose=settings.environment == "development",
        enqueue=True,  # Async logging for better performance
    )

    # File logging (if configured)
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path),
            format=formatter,
            level=settings.log_level,
            rotation=f"{settings.log_rotation_size} MB",
            retention=settings.log_retention,
            compression="gz",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

    # Log initial configuration
    logger.info(
        f"Logging configured: "
        f"level={settings.log_level}, "
        f"format={settings.log_format}, "
        f"environment={settings.environment}"
    )


# =============================================================================
# Context Managers for Distributed Tracing
# =============================================================================


class RequestContext:
    """Context manager for request-scoped logging.

    This ensures all logs within a request have the same request_id
    and correlation_id for distributed tracing.

    Example:
        async with RequestContext(request_id="abc123"):
            logger.info("Processing request")  # Will include request_id
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Initialize request context.

        Args:
            request_id: Unique request identifier
            correlation_id: Correlation ID for multi-service requests
            user_id: User identifier
        """
        self.request_id = request_id
        self.correlation_id = correlation_id
        self.user_id = user_id
        self.tokens: list = []

    def __enter__(self) -> "RequestContext":
        """Enter context."""
        if self.request_id:
            self.tokens.append(request_id_ctx.set(self.request_id))
        if self.correlation_id:
            self.tokens.append(correlation_id_ctx.set(self.correlation_id))
        if self.user_id:
            self.tokens.append(user_id_ctx.set(self.user_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        for token in self.tokens:
            token.var.reset(token)

    async def __aenter__(self) -> "RequestContext":
        """Async enter context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async exit context."""
        self.__exit__(exc_type, exc_val, exc_tb)


# =============================================================================
# Helper Functions
# =============================================================================


def get_request_id() -> Optional[str]:
    """Get current request ID from context.

    Returns:
        Request ID or None
    """
    return request_id_ctx.get()


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context.

    Returns:
        Correlation ID or None
    """
    return correlation_id_ctx.get()


def get_user_id() -> Optional[str]:
    """Get current user ID from context.

    Returns:
        User ID or None
    """
    return user_id_ctx.get()


def log_with_context(
    level: str,
    message: str,
    **extra: Any,
) -> None:
    """Log message with additional context.

    Args:
        level: Log level (info, warning, error, etc.)
        message: Log message
        **extra: Additional fields to include in log
    """
    log_func = getattr(logger, level.lower())
    log_func(message, **extra)


# =============================================================================
# Performance Logging
# =============================================================================


class PerformanceLogger:
    """Context manager for logging execution time.

    Example:
        async with PerformanceLogger("database_query"):
            result = await db.query()
        # Logs: "database_query completed in 123.45ms"
    """

    def __init__(
        self,
        operation: str,
        level: str = "info",
        threshold_ms: Optional[float] = None,
    ):
        """Initialize performance logger.

        Args:
            operation: Name of operation being measured
            level: Log level to use
            threshold_ms: Only log if execution time exceeds this threshold
        """
        self.operation = operation
        self.level = level
        self.threshold_ms = threshold_ms
        self.start_time: Optional[float] = None

    def __enter__(self) -> "PerformanceLogger":
        """Enter context."""
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        import time

        if self.start_time is None:
            return

        elapsed_ms = (time.time() - self.start_time) * 1000

        # Only log if above threshold
        if self.threshold_ms and elapsed_ms < self.threshold_ms:
            return

        log_func = getattr(logger, self.level)
        log_func(
            f"{self.operation} completed in {elapsed_ms:.2f}ms",
            operation=self.operation,
            duration_ms=elapsed_ms,
        )

    async def __aenter__(self) -> "PerformanceLogger":
        """Async enter context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async exit context."""
        self.__exit__(exc_type, exc_val, exc_tb)


# =============================================================================
# Logging Decorators
# =============================================================================


def log_execution_time(
    operation: Optional[str] = None,
    level: str = "info",
) -> Any:
    """Decorator to log function execution time.

    Args:
        operation: Operation name (defaults to function name)
        level: Log level

    Example:
        @log_execution_time()
        async def fetch_data():
            await asyncio.sleep(1)
    """
    import functools

    def decorator(func):
        nonlocal operation
        if operation is None:
            operation = func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with PerformanceLogger(operation, level):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceLogger(operation, level):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Sentry Integration (Optional)
# =============================================================================


def configure_sentry() -> None:
    """Configure Sentry error tracking if enabled.

    This function initializes Sentry SDK for error tracking and
    performance monitoring in production environments.
    """
    if not settings.sentry_enabled or not settings.sentry_dsn:
        logger.debug("Sentry integration disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Configure Sentry with FastAPI integration
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=settings.sentry_profiles_sample_rate,
            send_default_pii=False,  # Don't send PII
            attach_stacktrace=True,
            integrations=[
                LoggingIntegration(
                    level=None,  # Capture all levels
                    event_level=None,  # Don't send logs as events
                ),
            ],
            before_send=_sentry_before_send,
        )

        logger.success(f"Sentry initialized for environment: {settings.environment}")

    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _sentry_before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter Sentry events before sending.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop event
    """
    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["service"] = "mcps"

    # Add contextual information
    request_id = get_request_id()
    if request_id:
        event["tags"]["request_id"] = request_id

    return event


# Initialize logging on module import
configure_logging()
