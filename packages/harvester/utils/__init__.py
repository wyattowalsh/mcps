"""Utils - Rate limiters, Tenacity retries, and other utilities.

This package contains utility functions and decorators for common tasks
like rate limiting and retry logic.
"""

from .checkpointing import (
    get_failed_urls,
    get_pending_urls,
    get_processing_status,
    increment_attempts,
    mark_processing_completed,
    mark_processing_failed,
    mark_processing_skipped,
    mark_processing_started,
    reset_processing_log,
)
from .http_client import (
    HTTPClientError,
    close_client,
    fetch_bytes,
    fetch_json,
    fetch_text,
    get_client,
    http_client_context,
)

__all__ = [
    # Checkpointing functions
    "get_processing_status",
    "mark_processing_started",
    "mark_processing_completed",
    "mark_processing_failed",
    "mark_processing_skipped",
    "increment_attempts",
    "get_failed_urls",
    "get_pending_urls",
    "reset_processing_log",
    # HTTP client utilities
    "get_client",
    "close_client",
    "http_client_context",
    "fetch_json",
    "fetch_text",
    "fetch_bytes",
    "HTTPClientError",
]
