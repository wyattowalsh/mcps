---
title: Health Check API Endpoints
description: Health check and monitoring API endpoints
---

# Health Check API Endpoints

MCPS provides comprehensive health check endpoints for monitoring service health and readiness.

## Overview

Health endpoints allow you to:
- Monitor service availability
- Check database connectivity
- Verify cache health
- Track connection pool status
- Implement readiness and liveness probes

## Endpoints

### GET /health

Basic health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00.123Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 86400
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy

**Example:**

```bash
curl http://localhost:8000/health
```

### GET /health/db

Database health check with connection pool metrics.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00.123Z",
  "database": {
    "healthy": true,
    "latency_ms": 2.45,
    "database_type": "postgresql",
    "database_url": "postgresql+asyncpg://mcps:****@localhost:5432/mcps",
    "pool_size": 20,
    "pool_checked_in": 18,
    "pool_checked_out": 2,
    "pool_overflow": 0,
    "pool_timeout": 30
  }
}
```

**Status Codes:**
- `200 OK`: Database is healthy
- `503 Service Unavailable`: Database is unhealthy

**Example:**

```bash
curl http://localhost:8000/health/db
```

### GET /health/cache

Redis cache health check.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00.123Z",
  "cache": {
    "healthy": true,
    "latency_ms": 1.23,
    "version": "7.0.5",
    "used_memory": "2.5M",
    "connected_clients": 5,
    "uptime_seconds": 86400,
    "hits": 15234,
    "misses": 1523,
    "hit_rate": 0.909
  }
}
```

**Status Codes:**
- `200 OK`: Cache is healthy
- `503 Service Unavailable`: Cache is unhealthy

**Example:**

```bash
curl http://localhost:8000/health/cache
```

### GET /readiness

Kubernetes readiness probe endpoint.

Checks if the service is ready to accept traffic (database and cache are available).

**Response:**

```json
{
  "ready": true,
  "checks": {
    "database": "healthy",
    "cache": "healthy"
  }
}
```

**Status Codes:**
- `200 OK`: Service is ready
- `503 Service Unavailable`: Service is not ready

### GET /liveness

Kubernetes liveness probe endpoint.

Checks if the service is alive (basic health check).

**Response:**

```json
{
  "alive": true
}
```

**Status Codes:**
- `200 OK`: Service is alive
- `503 Service Unavailable`: Service should be restarted

### GET /metrics

Prometheus metrics endpoint.

Returns metrics in Prometheus text format.

**Example:**

```bash
curl http://localhost:8000/metrics
```

See [Monitoring Guide](../guides/monitoring.md) for details.

## Usage in Kubernetes

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health/db
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

## Monitoring

### Health Check Script

```bash
#!/bin/bash
# check-health.sh

API_URL="http://localhost:8000"

# Check basic health
if ! curl -f -s $API_URL/health > /dev/null; then
  echo "ERROR: API is unhealthy"
  exit 1
fi

# Check database
if ! curl -f -s $API_URL/health/db > /dev/null; then
  echo "ERROR: Database is unhealthy"
  exit 1
fi

# Check cache
if ! curl -f -s $API_URL/health/cache > /dev/null; then
  echo "WARNING: Cache is unhealthy (non-critical)"
fi

echo "All health checks passed"
exit 0
```

## See Also

- [Monitoring Guide](../guides/monitoring.md)
- [Production Deployment](../guides/production-deployment.md)
- [Architecture](../architecture.md)
