"""FastAPI middleware for production features.

This module provides production-ready middleware for:
- Request/response logging with structured logs
- Request ID tracking for distributed tracing
- Performance monitoring and metrics collection
- Error handling and exception logging
- Security headers (HSTS, CSP, etc.)
- Compression (gzip)
- CORS enhancement
"""

import gzip
import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .exceptions import APIError, MCPSException
from .logging import RequestContext
from .metrics import (
    http_request_duration_seconds,
    http_request_size_bytes,
    http_requests_in_progress,
    http_requests_total,
    http_response_size_bytes,
)

# =============================================================================
# Request ID Middleware
# =============================================================================


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs to all requests.

    This enables distributed tracing by assigning a unique ID to each request
    and propagating it through the request context and response headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with unique ID.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response with request ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Get correlation ID if present (for multi-service requests)
        correlation_id = request.headers.get("X-Correlation-ID")

        # Set request context for logging
        async with RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
        ):
            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            if correlation_id:
                response.headers["X-Correlation-ID"] = correlation_id

            return response


# =============================================================================
# Logging Middleware
# =============================================================================


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses.

    Logs include:
    - Request method, path, query params
    - Response status code
    - Request/response sizes
    - Processing time
    - Client IP and User-Agent
    - Any errors encountered
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response from endpoint
        """
        start_time = time.time()

        # Extract request info
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")

        # Log request
        logger.info(
            f"{method} {path}",
            method=method,
            path=path,
            query=query,
            client=client_host,
            user_agent=user_agent,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            status_code = response.status_code

            # Log response
            log_func = logger.info if status_code < 400 else logger.warning
            log_func(
                f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"{method} {path} - ERROR ({duration_ms:.2f}ms): {str(e)}",
                method=method,
                path=path,
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True,
            )

            raise


# =============================================================================
# Metrics Middleware
# =============================================================================


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all requests.

    Collects:
    - Request count by method, endpoint, status
    - Request duration histogram
    - Request/response sizes
    - In-progress request gauge
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for request.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response from endpoint
        """
        method = request.method
        path = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()

        start_time = time.time()

        try:
            # Get request size
            content_length = request.headers.get("Content-Length")
            if content_length:
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=path,
                ).observe(int(content_length))

            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code

            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=path,
            ).observe(duration)

            # Response size
            if "content-length" in response.headers:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=path,
                ).observe(int(response.headers["content-length"]))

            return response

        finally:
            # Decrement in-progress gauge
            http_requests_in_progress.labels(method=method, endpoint=path).dec()


# =============================================================================
# Error Handler Middleware
# =============================================================================


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors and return proper HTTP responses.

    Converts exceptions to appropriate HTTP responses with:
    - Proper status codes
    - Error details in JSON format
    - Error tracking in logs
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors from request processing.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response (may be error response)
        """
        try:
            return await call_next(request)

        except APIError as e:
            # Handle known API errors
            logger.warning(
                f"API error: {e.message}",
                status_code=e.status_code,
                details=e.details,
            )

            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.__class__.__name__,
                    "message": e.message,
                    "details": e.details,
                },
            )

        except MCPSException as e:
            # Handle application-specific errors
            logger.error(
                f"Application error: {e.message}",
                error_type=e.__class__.__name__,
                details=e.details,
                exc_info=True,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": e.__class__.__name__,
                    "message": e.message,
                    "details": e.details,
                },
            )

        except Exception as e:
            # Handle unexpected errors
            logger.exception(
                f"Unexpected error: {str(e)}",
                error_type=e.__class__.__name__,
            )

            # Don't leak internal error details in production
            from .settings import settings

            if settings.environment == "development":
                error_detail = str(e)
            else:
                error_detail = "An internal error occurred"

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "InternalServerError",
                    "message": error_detail,
                },
            )


# =============================================================================
# Security Headers Middleware
# =============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Adds headers for:
    - Content Security Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HSTS)
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(self, app, hsts_enabled: bool = True):
        """Initialize security headers middleware.

        Args:
            app: FastAPI application
            hsts_enabled: Enable HSTS header (only for HTTPS)
        """
        super().__init__(app)
        self.hsts_enabled = hsts_enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (only for HTTPS)
        if self.hsts_enabled and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


# =============================================================================
# Rate Limit Headers Middleware
# =============================================================================


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit information to response headers.

    Adds headers:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining
    - X-RateLimit-Reset: Time when limit resets
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add rate limit headers.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response with rate limit headers
        """
        response = await call_next(request)

        # Get rate limit info from slowapi (if available)
        if hasattr(request.state, "view_rate_limit"):
            limit_info = request.state.view_rate_limit

            response.headers["X-RateLimit-Limit"] = str(limit_info.limit)
            response.headers["X-RateLimit-Remaining"] = str(limit_info.remaining)
            response.headers["X-RateLimit-Reset"] = str(limit_info.reset)

        return response


# =============================================================================
# Compression Middleware Factory
# =============================================================================


def create_compression_middleware(
    minimum_size: int = 500,
    compresslevel: int = 6,
) -> type:
    """Create GZip compression middleware with custom settings.

    Args:
        minimum_size: Minimum response size in bytes to compress
        compresslevel: Compression level (1-9, higher = more compression)

    Returns:
        Configured GZipMiddleware class
    """

    class CustomGZipMiddleware(GZipMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                minimum_size=minimum_size,
                compresslevel=compresslevel,
            )

    return CustomGZipMiddleware


# =============================================================================
# Health Check Bypass Middleware
# =============================================================================


class HealthCheckBypassMiddleware(BaseHTTPMiddleware):
    """Middleware to bypass logging/metrics for health check endpoints.

    This prevents health check requests from polluting logs and metrics.
    """

    def __init__(self, app, bypass_paths: list[str] = None):
        """Initialize health check bypass middleware.

        Args:
            app: FastAPI application
            bypass_paths: List of paths to bypass (default: ["/health", "/healthz", "/ready"])
        """
        super().__init__(app)
        self.bypass_paths = bypass_paths or ["/health", "/healthz", "/ready", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Bypass middleware for health check paths.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response from endpoint
        """
        # Mark request as health check if it matches bypass paths
        if request.url.path in self.bypass_paths:
            request.state.is_health_check = True

        return await call_next(request)


# =============================================================================
# Supabase Auth Middleware
# =============================================================================


class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to verify Supabase JWT tokens.

    This middleware extracts and verifies JWT tokens from the Authorization header,
    attaching user information to the request state if authentication succeeds.

    Public endpoints (health, metrics, docs) skip authentication.
    For other endpoints, authentication is optional unless explicitly required.
    """

    def __init__(
        self,
        app,
        public_paths: list[str] = None,
        enabled: bool = True,
    ):
        """Initialize Supabase auth middleware.

        Args:
            app: FastAPI application
            public_paths: List of paths that don't require authentication
            enabled: Enable/disable auth middleware (useful for testing)
        """
        super().__init__(app)
        self.public_paths = public_paths or [
            "/health",
            "/healthz",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
        ]
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verify JWT token and attach user to request.

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint

        Returns:
            Response or 401 error if auth fails
        """
        # Skip auth if disabled or path is public
        if not self.enabled or any(
            request.url.path.startswith(path) for path in self.public_paths
        ):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Allow unauthenticated access but don't set user
            return await call_next(request)

        token = auth_header.replace("Bearer ", "")

        try:
            # Import here to avoid circular imports
            from .supabase import is_supabase_configured, supabase

            # Check if Supabase is configured
            if not is_supabase_configured():
                logger.warning("Supabase auth attempted but not configured")
                return await call_next(request)

            # Verify token with Supabase
            client = supabase()
            user_response = client.auth.get_user(token)

            # Attach user to request state
            if user_response and user_response.user:
                request.state.user = user_response.user
                request.state.user_id = user_response.user.id
                logger.debug(
                    f"Authenticated user: {user_response.user.id}",
                    extra={"user_id": user_response.user.id},
                )

        except ImportError:
            logger.warning("Supabase package not installed, skipping auth")
        except Exception as e:
            logger.warning(f"Auth verification failed: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"},
            )

        return await call_next(request)
