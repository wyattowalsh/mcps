---
title: Redis Caching Guide
description: Comprehensive guide to Redis caching in MCPS
---

# Redis Caching Guide

MCPS uses Redis for high-performance caching to reduce database load and improve response times.

## Overview

The caching layer provides:

- **Connection Pooling:** Efficient Redis connection management
- **Async Support:** Full async/await compatibility
- **Cache Decorators:** Easy function-level caching
- **TTL Management:** Automatic expiration of cached data
- **Pattern Invalidation:** Clear related cache entries
- **Health Monitoring:** Built-in health checks and metrics
- **Graceful Degradation:** Continues operation if Redis is unavailable

## Architecture

```{mermaid}
flowchart LR
    APP[Application] --> DECORATOR[Cache Decorator]
    DECORATOR --> CHECK{Cache Hit?}
    CHECK -->|Yes| RETURN[Return Cached]
    CHECK -->|No| FUNC[Execute Function]
    FUNC --> DB[(Database)]
    DB --> CACHE[Store in Cache]
    CACHE --> RETURN

    subgraph Redis
        POOL[Connection Pool]
        KEYS[Cached Keys]
    end

    CHECK -.->|Read| POOL
    CACHE -.->|Write| POOL
    POOL --> KEYS

    style CHECK fill:#fff3cd
    style RETURN fill:#d4edda
    style CACHE fill:#e1f5ff
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Redis Connection
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Connection Pool
REDIS_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=5

# Cache Behavior
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300
CACHE_FAIL_SILENTLY=true
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Full Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_DB` | Redis database number | `0` |
| `REDIS_PASSWORD` | Redis password (if required) | - |
| `REDIS_POOL_SIZE` | Connection pool size | `10` |
| `REDIS_SOCKET_TIMEOUT` | Socket timeout in seconds | `5` |
| `CACHE_ENABLED` | Enable/disable caching | `true` |
| `CACHE_TTL_DEFAULT` | Default TTL in seconds | `300` |
| `CACHE_FAIL_SILENTLY` | Continue on cache errors | `true` |

```{tip}
Set `CACHE_FAIL_SILENTLY=true` in production to ensure cache failures don't break your application.
```

## Usage

### Basic Operations

#### Get/Set Values

```python
from packages.harvester.cache import get_cache

# Get cache instance
cache = await get_cache()

# Set a value (with TTL)
await cache.set("user:123", {"name": "Alice", "role": "admin"}, ttl=600)

# Get a value
user = await cache.get("user:123")
print(user)  # {'name': 'Alice', 'role': 'admin'}

# Check if key exists
exists = await cache.exists("user:123")
print(exists)  # True

# Get remaining TTL
ttl = await cache.get_ttl("user:123")
print(ttl)  # ~600 seconds
```

#### Delete Values

```python
# Delete single key
await cache.delete("user:123")

# Delete multiple keys
await cache.delete("user:123", "user:456", "user:789")

# Delete by pattern
deleted = await cache.clear_pattern("user:*")
print(f"Deleted {deleted} keys")
```

#### Counters

```python
# Increment counter
views = await cache.increment("post:123:views")
print(views)  # 1

# Increment by custom amount
views = await cache.increment("post:123:views", amount=5)
print(views)  # 6
```

### Cache Decorators

#### @cached Decorator

Cache function results automatically:

```python
from packages.harvester.cache import cached

@cached(ttl=600, key_prefix="server")
async def get_server_details(server_id: int):
    """Get server details (cached for 10 minutes)."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Server).where(Server.id == server_id)
        )
        return result.scalar_one_or_none()

# First call: hits database
server = await get_server_details(123)

# Second call: returns from cache
server = await get_server_details(123)  # Fast!
```

**Decorator Parameters:**

- `ttl`: Time to live in seconds (default: 300)
- `key_prefix`: Prefix for cache key
- `key_builder`: Custom function to build cache key

#### Custom Key Builder

```python
def build_cache_key(user_id: int, include_deleted: bool = False):
    """Custom cache key builder."""
    return f"{user_id}:deleted={include_deleted}"

@cached(ttl=300, key_prefix="user", key_builder=build_cache_key)
async def get_users(user_id: int, include_deleted: bool = False):
    # ... fetch users
    pass
```

#### @invalidate_cache Decorator

Invalidate cache after mutations:

```python
from packages.harvester.cache import invalidate_cache

@invalidate_cache("server:*")
async def update_server(server_id: int, data: dict):
    """Update server and invalidate all server caches."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()

        for key, value in data.items():
            setattr(server, key, value)

        await session.commit()
        return server

# This will clear all keys matching "server:*"
await update_server(123, {"name": "New Name"})
```

## Cache Patterns

### Read-Through Caching

Automatically load data into cache on first access:

```python
@cached(ttl=600, key_prefix="repository")
async def get_repository_info(owner: str, repo: str):
    """Fetch repository info from GitHub (cached)."""
    # On cache miss, fetches from GitHub
    # On cache hit, returns from Redis
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}"
        )
        return response.json()
```

### Write-Through Caching

Update cache whenever database is updated:

```python
async def update_server_stats(server_id: int, stats: dict):
    """Update server stats in both database and cache."""
    async with async_session_maker() as session:
        # Update database
        result = await session.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()
        server.stats = stats
        await session.commit()

        # Update cache
        cache = await get_cache()
        await cache.set(f"server:{server_id}:stats", stats, ttl=300)
```

### Cache-Aside Pattern

Check cache first, load on miss:

```python
async def get_trending_servers(limit: int = 10):
    """Get trending servers with cache-aside pattern."""
    cache = await get_cache()
    cache_key = f"trending:servers:{limit}"

    # Check cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    # Cache miss - fetch from database
    async with async_session_maker() as session:
        result = await session.execute(
            select(Server)
            .order_by(Server.stars.desc())
            .limit(limit)
        )
        servers = result.scalars().all()

        # Store in cache
        await cache.set(cache_key, servers, ttl=600)
        return servers
```

### Time-Based Invalidation

Cache with automatic expiration:

```python
@cached(ttl=3600, key_prefix="stats")
async def get_daily_stats():
    """Get daily statistics (cached for 1 hour)."""
    async with async_session_maker() as session:
        # Calculate stats from database
        result = await session.execute(
            select(
                func.count(Server.id).label("total_servers"),
                func.avg(Server.stars).label("avg_stars"),
                func.sum(Server.forks).label("total_forks"),
            )
        )
        return result.one()._asdict()
```

## Health Checks

### Manual Health Check

```python
from packages.harvester.cache import get_cache

cache = await get_cache()
health = await cache.health_check()

print(health)
# {
#   'healthy': True,
#   'latency_ms': 2.45,
#   'version': '7.0.5',
#   'used_memory': '2.5M',
#   'connected_clients': 5,
#   'uptime_seconds': 86400
# }
```

### API Health Endpoint

```bash
# Check cache health
curl http://localhost:8000/health/cache

# Example response:
{
  "status": "healthy",
  "cache": {
    "healthy": true,
    "latency_ms": 2.45,
    "version": "7.0.5",
    "used_memory": "2.5M",
    "connected_clients": 5
  }
}
```

## Cache Invalidation Strategies

### 1. Time-Based (TTL)

Best for: Data that changes predictably

```python
# Cache for 5 minutes
@cached(ttl=300)
async def get_server_list():
    pass
```

### 2. Event-Based

Best for: Data updated by specific actions

```python
@invalidate_cache("server:*")
async def create_server(data: dict):
    """Creating a server invalidates server list cache."""
    pass
```

### 3. Pattern-Based

Best for: Related data groups

```python
# Clear all user-related caches
cache = await get_cache()
await cache.clear_pattern("user:*")
await cache.clear_pattern("profile:*")
await cache.clear_pattern("settings:*")
```

### 4. Manual Invalidation

Best for: Complex scenarios

```python
async def rebuild_cache():
    """Manually rebuild cache after bulk operations."""
    cache = await get_cache()

    # Clear old cache
    await cache.clear_pattern("stats:*")

    # Warm new cache
    await get_daily_stats()  # Cached function
    await get_trending_servers()  # Cached function
```

## Performance Optimization

### Connection Pooling

```python
# In settings.py
REDIS_POOL_SIZE=20  # Increase for high concurrency
REDIS_SOCKET_TIMEOUT=10  # Increase for slow networks
```

### TTL Guidelines

| Data Type | Recommended TTL | Reason |
|-----------|----------------|--------|
| Static data | 1 hour - 1 day | Rarely changes |
| User profiles | 15 - 30 minutes | Moderate changes |
| API responses | 5 - 10 minutes | Frequent updates |
| Search results | 1 - 5 minutes | Real-time needs |
| Aggregated stats | 10 - 60 minutes | Expensive to compute |

### Batch Operations

```python
# Instead of multiple gets:
for server_id in server_ids:
    server = await cache.get(f"server:{server_id}")

# Use pipeline (future enhancement):
# results = await cache.mget([f"server:{id}" for id in server_ids])
```

## Monitoring

### Redis Metrics

Monitor these Redis metrics:

- **Hit Rate:** Cache hits / (hits + misses)
- **Memory Usage:** Total memory used by Redis
- **Evictions:** Keys evicted due to memory limits
- **Connection Count:** Active client connections
- **Command Latency:** Average command execution time

### Application Metrics

```python
# Track cache performance in your app
from packages.harvester.metrics import cache_hit_counter, cache_miss_counter

@cached(ttl=300, key_prefix="api")
async def api_call(endpoint: str):
    # Metrics are tracked automatically by decorator
    pass
```

## Troubleshooting

### Connection Errors

**Problem:** `CacheConnectionError: Failed to connect to Redis`

**Solutions:**

```bash
# 1. Check Redis is running
docker-compose ps redis

# 2. Test connection manually
redis-cli -h localhost -p 6379 ping
# Expected: PONG

# 3. Check environment variables
echo $REDIS_URL
echo $REDIS_HOST

# 4. Check Docker network
docker-compose logs redis

# 5. Restart Redis
docker-compose restart redis
```

### Cache Misses

**Problem:** High cache miss rate

**Solutions:**

```python
# 1. Increase TTL
@cached(ttl=600)  # Increase from 300 to 600

# 2. Warm cache on startup
async def warm_cache():
    await get_trending_servers()
    await get_daily_stats()

# 3. Check cache key consistency
# Make sure key builders are deterministic
```

### Memory Issues

**Problem:** Redis running out of memory

**Solutions:**

```bash
# 1. Check memory usage
redis-cli INFO memory

# 2. Set maxmemory policy in docker-compose.yml
command:
  - --maxmemory 256mb
  - --maxmemory-policy allkeys-lru

# 3. Reduce TTL for large objects
@cached(ttl=60)  # Shorter TTL for large data

# 4. Compress large values (future enhancement)
```

### Silent Failures

**Problem:** Cache errors not visible

**Solution:**

```bash
# For debugging, disable silent failures
CACHE_FAIL_SILENTLY=false
```

## Best Practices

### 1. Cache Keys

```{admonition} Good Practice
:class: tip

- Use descriptive prefixes: `server:`, `user:`, `stats:`
- Include version numbers: `api:v1:servers`
- Use consistent delimiters: `:` not `-` or `_`
- Keep keys short but meaningful
```

```python
# Good
cache_key = "server:123:stats"

# Bad
cache_key = "the_statistics_for_server_number_123_including_all_metrics"
```

### 2. TTL Selection

```{admonition} Good Practice
:class: tip

- Set TTL based on data volatility
- Use longer TTL for expensive operations
- Shorter TTL for user-facing data
- Never use TTL=None for unbounded data
```

### 3. Error Handling

```{admonition} Good Practice
:class: tip

- Always enable `CACHE_FAIL_SILENTLY` in production
- Add fallback logic for cache failures
- Monitor cache health regularly
- Log cache errors for debugging
```

```python
@cached(ttl=300, key_prefix="api")
async def get_data(id: int):
    try:
        # Your code here
        return data
    except Exception as e:
        # Fallback to database on cache error
        logger.warning(f"Cache failed, using database: {e}")
        return await fetch_from_database(id)
```

### 4. Cache Warming

```{admonition} Good Practice
:class: tip

- Warm frequently accessed data on startup
- Use background tasks for cache warming
- Prioritize expensive queries
```

```python
async def startup_event():
    """Warm cache on application startup."""
    cache = await get_cache()

    # Warm trending servers
    await get_trending_servers()

    # Warm statistics
    await get_daily_stats()

    logger.info("Cache warmed successfully")
```

## Advanced Topics

### Custom Serialization

For complex objects, implement custom serializers:

```python
from dataclasses import asdict
from packages.harvester.cache import RedisCache

class CustomCache(RedisCache):
    def _serialize(self, value):
        if hasattr(value, '__dict__'):
            return json.dumps(asdict(value)).encode()
        return super()._serialize(value)
```

### Distributed Caching

For multi-server deployments:

```bash
# Use Redis Cluster
REDIS_URL=redis://redis-cluster:6379/0

# Or Redis Sentinel for HA
REDIS_URL=redis://sentinel:26379/0?sentinel=mymaster
```

### Cache Stampede Prevention

Prevent multiple requests from hitting database simultaneously:

```python
import asyncio
from asyncio import Lock

_locks = {}

@cached(ttl=300, key_prefix="server")
async def get_server_with_lock(server_id: int):
    """Prevent cache stampede with locks."""
    lock_key = f"lock:server:{server_id}"

    if lock_key not in _locks:
        _locks[lock_key] = Lock()

    async with _locks[lock_key]:
        # Only one request fetches data at a time
        return await fetch_server_from_db(server_id)
```

## See Also

- [Production Deployment](production-deployment.md) - Redis deployment in production
- [Monitoring Guide](monitoring.md) - Cache monitoring and metrics
- [API Health Endpoints](../api/health-endpoints.md) - Health check documentation
- [Architecture](../architecture.md) - System architecture overview
