"""Prometheus metrics for MCPS.

This module provides comprehensive metrics collection using Prometheus:
- Request metrics (latency, throughput, errors)
- Database metrics (query time, connection pool)
- Cache metrics (hit rate, latency)
- Business metrics (servers indexed, harvest success rate)
- System metrics (memory, CPU)
- Background task metrics
"""

import functools
import time
from typing import Any, Callable, Optional, TypeVar

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)
from prometheus_client.core import CollectorRegistry

from .settings import settings

# Type variable for decorators
T = TypeVar("T")

# =============================================================================
# Registry
# =============================================================================

# Create custom registry (allows multiple apps in same process)
registry = CollectorRegistry()

# =============================================================================
# Application Info
# =============================================================================

app_info = Info(
    "mcps_app",
    "MCPS application information",
    registry=registry,
)

app_info.info(
    {
        "version": "1.0.0",
        "environment": settings.environment,
        "python_version": "3.12",
    }
)

# =============================================================================
# HTTP Request Metrics
# =============================================================================

http_requests_total = Counter(
    "mcps_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "mcps_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

http_request_size_bytes = Summary(
    "mcps_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

http_response_size_bytes = Summary(
    "mcps_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

http_requests_in_progress = Gauge(
    "mcps_http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=registry,
)

# =============================================================================
# Database Metrics
# =============================================================================

db_queries_total = Counter(
    "mcps_db_queries_total",
    "Total database queries",
    ["operation", "table"],
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "mcps_db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry,
)

db_connection_pool_size = Gauge(
    "mcps_db_connection_pool_size",
    "Database connection pool size",
    registry=registry,
)

db_connection_pool_checked_out = Gauge(
    "mcps_db_connection_pool_checked_out",
    "Database connections currently checked out",
    registry=registry,
)

db_connection_pool_overflow = Gauge(
    "mcps_db_connection_pool_overflow",
    "Database connection pool overflow count",
    registry=registry,
)

db_connection_errors_total = Counter(
    "mcps_db_connection_errors_total",
    "Total database connection errors",
    ["error_type"],
    registry=registry,
)

# =============================================================================
# Cache Metrics
# =============================================================================

cache_operations_total = Counter(
    "mcps_cache_operations_total",
    "Total cache operations",
    ["operation", "status"],
    registry=registry,
)

cache_hit_rate = Gauge(
    "mcps_cache_hit_rate",
    "Cache hit rate (0-1)",
    registry=registry,
)

cache_operation_duration_seconds = Histogram(
    "mcps_cache_operation_duration_seconds",
    "Cache operation latency in seconds",
    ["operation"],
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
    registry=registry,
)

cache_memory_bytes = Gauge(
    "mcps_cache_memory_bytes",
    "Cache memory usage in bytes",
    registry=registry,
)

cache_keys_total = Gauge(
    "mcps_cache_keys_total",
    "Total number of keys in cache",
    registry=registry,
)

# =============================================================================
# Business Metrics
# =============================================================================

servers_total = Gauge(
    "mcps_servers_total",
    "Total number of servers indexed",
    ["host_type"],
    registry=registry,
)

servers_verified = Gauge(
    "mcps_servers_verified",
    "Number of verified servers",
    registry=registry,
)

servers_health_score = Histogram(
    "mcps_servers_health_score",
    "Server health score distribution",
    buckets=(0, 20, 40, 60, 80, 100),
    registry=registry,
)

harvest_operations_total = Counter(
    "mcps_harvest_operations_total",
    "Total harvest operations",
    ["source", "status"],
    registry=registry,
)

harvest_duration_seconds = Histogram(
    "mcps_harvest_duration_seconds",
    "Harvest operation duration in seconds",
    ["source"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry,
)

harvest_items_total = Counter(
    "mcps_harvest_items_total",
    "Total items harvested",
    ["source", "item_type"],
    registry=registry,
)

social_posts_total = Gauge(
    "mcps_social_posts_total",
    "Total social media posts indexed",
    ["platform"],
    registry=registry,
)

social_sentiment_score = Histogram(
    "mcps_social_sentiment_score",
    "Social media sentiment score distribution",
    ["platform"],
    buckets=(-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0),
    registry=registry,
)

# =============================================================================
# Background Task Metrics
# =============================================================================

background_tasks_total = Counter(
    "mcps_background_tasks_total",
    "Total background tasks executed",
    ["task_name", "status"],
    registry=registry,
)

background_task_duration_seconds = Histogram(
    "mcps_background_task_duration_seconds",
    "Background task duration in seconds",
    ["task_name"],
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
    registry=registry,
)

background_tasks_running = Gauge(
    "mcps_background_tasks_running",
    "Number of background tasks currently running",
    registry=registry,
)

scheduled_jobs_total = Gauge(
    "mcps_scheduled_jobs_total",
    "Total number of scheduled jobs",
    registry=registry,
)

# =============================================================================
# System Metrics
# =============================================================================

system_memory_bytes = Gauge(
    "mcps_system_memory_bytes",
    "System memory usage in bytes",
    ["type"],
    registry=registry,
)

system_cpu_percent = Gauge(
    "mcps_system_cpu_percent",
    "System CPU usage percentage",
    registry=registry,
)

# =============================================================================
# API Key Metrics
# =============================================================================

api_key_requests_total = Counter(
    "mcps_api_key_requests_total",
    "Total API requests by key",
    ["api_key_hash", "endpoint"],
    registry=registry,
)

rate_limit_exceeded_total = Counter(
    "mcps_rate_limit_exceeded_total",
    "Total rate limit exceeded events",
    ["endpoint", "user"],
    registry=registry,
)

# =============================================================================
# Metrics Collection Functions
# =============================================================================


def collect_db_pool_metrics(pool: Any) -> None:
    """Collect database connection pool metrics.

    Args:
        pool: SQLAlchemy connection pool
    """
    try:
        db_connection_pool_size.set(pool.size())
        db_connection_pool_checked_out.set(pool.checkedout())
        db_connection_pool_overflow.set(pool.overflow())
    except Exception:
        pass  # Silently fail if pool doesn't support these methods


def collect_cache_metrics(cache_info: dict) -> None:
    """Collect cache metrics from Redis.

    Args:
        cache_info: Redis INFO command output
    """
    try:
        # Memory usage
        used_memory = cache_info.get("used_memory", 0)
        cache_memory_bytes.set(used_memory)

        # Key count
        db_keys = cache_info.get("db0", {})
        if isinstance(db_keys, dict):
            cache_keys_total.set(db_keys.get("keys", 0))

    except Exception:
        pass  # Silently fail


def collect_system_metrics() -> None:
    """Collect system metrics (memory, CPU).

    This uses psutil if available, otherwise falls back to basic metrics.
    """
    try:
        import psutil

        # Memory metrics
        memory = psutil.virtual_memory()
        system_memory_bytes.labels(type="total").set(memory.total)
        system_memory_bytes.labels(type="available").set(memory.available)
        system_memory_bytes.labels(type="used").set(memory.used)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_percent.set(cpu_percent)

    except ImportError:
        # psutil not installed, use basic Python metrics
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        system_memory_bytes.labels(type="process").set(usage.ru_maxrss * 1024)

    except Exception:
        pass  # Silently fail


# =============================================================================
# Metric Decorators
# =============================================================================


def track_time(
    metric: Histogram,
    labels: Optional[dict] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to track execution time in a Prometheus histogram.

    Args:
        metric: Prometheus Histogram to track time in
        labels: Optional labels for the metric

    Returns:
        Decorated function

    Example:
        @track_time(db_query_duration_seconds, {"operation": "select", "table": "servers"})
        async def get_servers():
            return await db.query(Server).all()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def count_calls(
    metric: Counter,
    labels: Optional[dict] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to count function calls.

    Args:
        metric: Prometheus Counter to increment
        labels: Optional labels for the metric

    Returns:
        Decorated function

    Example:
        @count_calls(harvest_operations_total, {"source": "github", "status": "success"})
        async def harvest_github():
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            result = await func(*args, **kwargs)
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)
            if labels:
                metric.labels(**labels).inc()
            else:
                metric.inc()
            return result

        # Return appropriate wrapper
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# Metrics Endpoint
# =============================================================================


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    # Collect latest system metrics
    collect_system_metrics()

    # Generate metrics output
    return generate_latest(registry)


# =============================================================================
# Context Managers
# =============================================================================


class MetricTimer:
    """Context manager for timing operations and recording to histogram.

    Example:
        async with MetricTimer(db_query_duration_seconds, operation="select"):
            result = await db.query()
    """

    def __init__(self, metric: Histogram, **labels: Any):
        """Initialize metric timer.

        Args:
            metric: Histogram metric to record to
            **labels: Labels for the metric
        """
        self.metric = metric
        self.labels = labels
        self.start_time: Optional[float] = None

    def __enter__(self) -> "MetricTimer":
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timer and record metric."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            if self.labels:
                self.metric.labels(**self.labels).observe(duration)
            else:
                self.metric.observe(duration)

    async def __aenter__(self) -> "MetricTimer":
        """Async start timer."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async stop timer."""
        self.__exit__(exc_type, exc_val, exc_tb)


class InProgressGauge:
    """Context manager for tracking in-progress operations.

    Example:
        async with InProgressGauge(http_requests_in_progress, method="GET"):
            result = await process_request()
    """

    def __init__(self, metric: Gauge, **labels: Any):
        """Initialize in-progress gauge.

        Args:
            metric: Gauge metric to track
            **labels: Labels for the metric
        """
        self.metric = metric
        self.labels = labels

    def __enter__(self) -> "InProgressGauge":
        """Increment gauge."""
        if self.labels:
            self.metric.labels(**self.labels).inc()
        else:
            self.metric.inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Decrement gauge."""
        if self.labels:
            self.metric.labels(**self.labels).dec()
        else:
            self.metric.dec()

    async def __aenter__(self) -> "InProgressGauge":
        """Async increment gauge."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async decrement gauge."""
        self.__exit__(exc_type, exc_val, exc_tb)
