"""Custom exception hierarchy for MCPS.

This module provides a comprehensive exception hierarchy for better error handling
and debugging across the application.
"""

from typing import Any, Dict, Optional


class MCPSException(Exception):
    """Base exception for all MCPS errors.

    All custom exceptions should inherit from this base class to allow
    for easy catching of all application-specific exceptions.
    """

    def __init__(
        self,
        message: str,
        *,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize MCPS exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# Database Exceptions
# =============================================================================


class DatabaseError(MCPSException):
    """Base exception for database-related errors."""

    pass


class ConnectionError(DatabaseError):
    """Database connection failed."""

    pass


class QueryError(DatabaseError):
    """Database query failed."""

    pass


class TransactionError(DatabaseError):
    """Database transaction failed."""

    pass


class MigrationError(DatabaseError):
    """Database migration failed."""

    pass


class PoolExhaustedError(DatabaseError):
    """Connection pool exhausted."""

    pass


# =============================================================================
# Cache Exceptions
# =============================================================================


class CacheError(MCPSException):
    """Base exception for cache-related errors."""

    pass


class CacheConnectionError(CacheError):
    """Redis connection failed."""

    pass


class CacheOperationError(CacheError):
    """Cache operation failed."""

    pass


class CacheSerializationError(CacheError):
    """Failed to serialize/deserialize cached data."""

    pass


# =============================================================================
# Adapter Exceptions
# =============================================================================


class AdapterError(MCPSException):
    """Base exception for adapter-related errors."""

    pass


class AdapterConnectionError(AdapterError):
    """External API connection failed."""

    pass


class AdapterRateLimitError(AdapterError):
    """External API rate limit exceeded."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            **kwargs: Additional arguments
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AdapterAuthenticationError(AdapterError):
    """External API authentication failed."""

    pass


class AdapterResponseError(AdapterError):
    """External API returned invalid response."""

    pass


class AdapterTimeoutError(AdapterError):
    """External API request timed out."""

    pass


# =============================================================================
# Validation Exceptions
# =============================================================================


class ValidationError(MCPSException):
    """Base exception for validation errors."""

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Any = None,
        **kwargs: Any,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Value that failed validation
            **kwargs: Additional arguments
        """
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        if self.value is not None:
            result["value"] = str(self.value)
        return result


class SchemaValidationError(ValidationError):
    """Schema validation failed."""

    pass


class ConfigurationError(ValidationError):
    """Configuration validation failed."""

    pass


# =============================================================================
# Harvester Exceptions
# =============================================================================


class HarvesterError(MCPSException):
    """Base exception for harvester-related errors."""

    pass


class ParseError(HarvesterError):
    """Failed to parse data."""

    pass


class ExtractionError(HarvesterError):
    """Failed to extract data."""

    pass


class DependencyAnalysisError(HarvesterError):
    """Dependency analysis failed."""

    pass


# =============================================================================
# API Exceptions
# =============================================================================


class APIError(MCPSException):
    """Base exception for API-related errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        **kwargs: Any,
    ):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            **kwargs: Additional arguments
        """
        super().__init__(message, **kwargs)
        self.status_code = status_code


class NotFoundError(APIError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any):
        """Initialize not found error.

        Args:
            message: Error message
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=404, **kwargs)


class UnauthorizedError(APIError):
    """Unauthorized access."""

    def __init__(self, message: str = "Unauthorized", **kwargs: Any):
        """Initialize unauthorized error.

        Args:
            message: Error message
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(APIError):
    """Forbidden access."""

    def __init__(self, message: str = "Forbidden", **kwargs: Any):
        """Initialize forbidden error.

        Args:
            message: Error message
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=403, **kwargs)


class BadRequestError(APIError):
    """Bad request."""

    def __init__(self, message: str = "Bad request", **kwargs: Any):
        """Initialize bad request error.

        Args:
            message: Error message
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=400, **kwargs)


class RateLimitExceededError(APIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class ServiceUnavailableError(APIError):
    """Service temporarily unavailable."""

    def __init__(self, message: str = "Service unavailable", **kwargs: Any):
        """Initialize service unavailable error.

        Args:
            message: Error message
            **kwargs: Additional arguments
        """
        super().__init__(message, status_code=503, **kwargs)


# =============================================================================
# Task Exceptions
# =============================================================================


class TaskError(MCPSException):
    """Base exception for background task errors."""

    pass


class TaskExecutionError(TaskError):
    """Task execution failed."""

    pass


class TaskSchedulingError(TaskError):
    """Task scheduling failed."""

    pass


class TaskTimeoutError(TaskError):
    """Task execution timed out."""

    pass


# =============================================================================
# Export Exceptions
# =============================================================================


class ExportError(MCPSException):
    """Base exception for export-related errors."""

    pass


class SerializationError(ExportError):
    """Failed to serialize data for export."""

    pass


class FileWriteError(ExportError):
    """Failed to write export file."""

    pass


# =============================================================================
# Security Exceptions
# =============================================================================


class SecurityError(MCPSException):
    """Base exception for security-related errors."""

    pass


class MaliciousCodeDetectedError(SecurityError):
    """Potentially malicious code detected."""

    pass


class InsecureDependencyError(SecurityError):
    """Insecure dependency detected."""

    pass
