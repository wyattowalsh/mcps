"""Redis caching layer for MCPS.

This module provides a production-ready Redis caching layer with:
- Connection pooling and health checks
- Async/await support
- Cache decorators for easy integration
- TTL management
- Cache invalidation strategies
- Serialization/deserialization
"""

import asyncio
import functools
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar, Union

import redis.asyncio as aioredis
from loguru import logger
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from .exceptions import (
    CacheConnectionError,
    CacheOperationError,
    CacheSerializationError,
)
from .settings import settings

# Type variable for generic functions
T = TypeVar("T")


class RedisCache:
    """Redis cache manager with async support.

    This class provides a high-level interface for Redis caching operations
    with connection pooling, error handling, and automatic serialization.
    """

    def __init__(self) -> None:
        """Initialize Redis cache manager."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connected: bool = False

    async def connect(self) -> None:
        """Establish connection to Redis.

        Raises:
            CacheConnectionError: If connection fails
        """
        if self._connected:
            logger.debug("Redis cache already connected")
            return

        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                settings.redis_url_computed,
                max_connections=settings.redis_pool_size,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=settings.redis_socket_timeout,
                socket_keepalive=True,
                health_check_interval=30,
            )

            # Create Redis client
            self._client = Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            self._connected = True
            logger.success(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")

        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheConnectionError(
                "Failed to connect to Redis",
                details={"url": settings.redis_url_computed},
                original_error=e,
            )

    async def disconnect(self) -> None:
        """Close Redis connection gracefully."""
        if not self._connected:
            return

        try:
            if self._client:
                await self._client.close()
            if self._pool:
                await self._pool.disconnect()

            self._connected = False
            logger.info("Disconnected from Redis")

        except RedisError as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Check Redis connection health.

        Returns:
            Dictionary with health check results

        Raises:
            CacheConnectionError: If health check fails
        """
        import time

        if not self._connected or not self._client:
            return {"healthy": False, "error": "Not connected"}

        try:
            start_time = time.time()
            await self._client.ping()
            latency_ms = (time.time() - start_time) * 1000

            # Get Redis info
            info = await self._client.info()

            return {
                "healthy": True,
                "latency_ms": round(latency_ms, 2),
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            return {"healthy": False, "error": str(e)}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found

        Raises:
            CacheOperationError: If operation fails
        """
        if not self._connected or not self._client:
            if settings.cache_enabled:
                raise CacheConnectionError("Not connected to Redis")
            return None

        try:
            value = await self._client.get(key)
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return None

            logger.debug(f"Cache hit: {key}")
            return self._deserialize(value)

        except RedisError as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            if settings.cache_fail_silently:
                return None
            raise CacheOperationError(
                f"Failed to get cache key '{key}'",
                details={"key": key},
                original_error=e,
            )

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)

        Returns:
            True if successful, False otherwise

        Raises:
            CacheOperationError: If operation fails
        """
        if not self._connected or not self._client:
            if settings.cache_enabled:
                raise CacheConnectionError("Not connected to Redis")
            return False

        try:
            serialized = self._serialize(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)

            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except (RedisError, CacheSerializationError) as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            if settings.cache_fail_silently:
                return False
            raise CacheOperationError(
                f"Failed to set cache key '{key}'",
                details={"key": key, "ttl": ttl},
                original_error=e,
            )

    async def delete(self, *keys: str) -> int:
        """Delete keys from cache.

        Args:
            *keys: Cache keys to delete

        Returns:
            Number of keys deleted

        Raises:
            CacheOperationError: If operation fails
        """
        if not self._connected or not self._client:
            if settings.cache_enabled:
                raise CacheConnectionError("Not connected to Redis")
            return 0

        try:
            count = await self._client.delete(*keys)
            logger.debug(f"Cache delete: {count} keys removed")
            return count

        except RedisError as e:
            logger.error(f"Cache delete failed: {e}")
            if settings.cache_fail_silently:
                return 0
            raise CacheOperationError(
                "Failed to delete cache keys",
                details={"keys": keys},
                original_error=e,
            )

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._connected or not self._client:
            return False

        try:
            return await self._client.exists(key) > 0
        except RedisError:
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")

        Returns:
            Number of keys deleted

        Raises:
            CacheOperationError: If operation fails
        """
        if not self._connected or not self._client:
            if settings.cache_enabled:
                raise CacheConnectionError("Not connected to Redis")
            return 0

        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                count = await self._client.delete(*keys)
                logger.info(f"Cleared {count} cache keys matching pattern '{pattern}'")
                return count

            return 0

        except RedisError as e:
            logger.error(f"Cache clear pattern failed: {e}")
            if settings.cache_fail_silently:
                return 0
            raise CacheOperationError(
                f"Failed to clear cache pattern '{pattern}'",
                details={"pattern": pattern},
                original_error=e,
            )

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter.

        Args:
            key: Counter key
            amount: Amount to increment by

        Returns:
            New value after increment

        Raises:
            CacheOperationError: If operation fails
        """
        if not self._connected or not self._client:
            if settings.cache_enabled:
                raise CacheConnectionError("Not connected to Redis")
            return 0

        try:
            return await self._client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Cache increment failed for key '{key}': {e}")
            if settings.cache_fail_silently:
                return 0
            raise CacheOperationError(
                f"Failed to increment cache key '{key}'",
                details={"key": key, "amount": amount},
                original_error=e,
            )

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, or None if key doesn't exist or has no TTL
        """
        if not self._connected or not self._client:
            return None

        try:
            ttl = await self._client.ttl(key)
            return ttl if ttl > 0 else None
        except RedisError:
            return None

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage in Redis.

        Args:
            value: Value to serialize

        Returns:
            Serialized bytes

        Raises:
            CacheSerializationError: If serialization fails
        """
        try:
            return json.dumps(value, default=str).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(
                "Failed to serialize value for cache",
                original_error=e,
            )

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from Redis.

        Args:
            value: Serialized bytes

        Returns:
            Deserialized value

        Raises:
            CacheSerializationError: If deserialization fails
        """
        try:
            return json.loads(value.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError) as e:
            raise CacheSerializationError(
                "Failed to deserialize cached value",
                original_error=e,
            )


# Global cache instance
_cache: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """Get or create the global cache instance.

    Returns:
        RedisCache instance
    """
    global _cache
    if _cache is None:
        _cache = RedisCache()
        if settings.cache_enabled:
            await _cache.connect()
    return _cache


# =============================================================================
# Cache Decorators
# =============================================================================


def cache_key_builder(*args: Any, **kwargs: Any) -> str:
    """Build cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Create a stable string representation
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # Hash for consistent length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 300)
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key

    Returns:
        Decorated function

    Example:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Skip cache if disabled
            if not settings.cache_enabled:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = cache_key_builder(*args, **kwargs)

            cache_key = f"{key_prefix}:{func.__name__}:{key_suffix}"

            # Try to get from cache
            cache = await get_cache()
            cached_value = await cache.get(cache_key)

            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to invalidate cache after function execution.

    Args:
        pattern: Cache key pattern to invalidate

    Returns:
        Decorated function

    Example:
        @invalidate_cache("user:*")
        async def update_user(user_id: int, data: dict):
            return await db.update_user(user_id, data)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            result = await func(*args, **kwargs)

            # Invalidate cache if enabled
            if settings.cache_enabled:
                cache = await get_cache()
                await cache.clear_pattern(pattern)

            return result

        return wrapper

    return decorator
