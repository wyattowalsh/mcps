---
title: Monitoring & Observability Guide
description: Comprehensive guide to monitoring and observability in MCPS
---

# Monitoring & Observability Guide

MCPS provides comprehensive monitoring and observability through Prometheus metrics, structured logging, and error tracking.

## Overview

The monitoring stack includes:

- **Prometheus Metrics:** Application and business metrics
- **Structured Logging:** JSON logs for aggregation and analysis
- **Sentry Error Tracking:** Real-time error monitoring and alerting
- **Health Checks:** Service health endpoints
- **Distributed Tracing:** Request ID and correlation ID tracking
- **Performance Monitoring:** Execution time tracking and profiling

## Architecture

```{mermaid}
flowchart LR
    APP[MCPS Application] --> METRICS[Prometheus<br/>Metrics]
    APP --> LOGS[Structured<br/>Logs]
    APP --> SENTRY[Sentry<br/>Errors]

    METRICS --> PROM[Prometheus<br/>Server]
    LOGS --> LOKI[Loki/ELK<br/>Aggregation]
    SENTRY --> DASHBOARD[Sentry<br/>Dashboard]

    PROM --> GRAFANA[Grafana<br/>Dashboards]
    LOKI --> GRAFANA

    subgraph Observability Stack
        PROM
        LOKI
        SENTRY
        GRAFANA
    end

    style APP fill:#e1f5ff
    style METRICS fill:#d4edda
    style LOGS fill:#fff3cd
    style SENTRY fill:#f8d7da
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                   # json or text
LOG_FILE=logs/mcps.log           # Log file path (optional)
LOG_ROTATION_SIZE=100            # MB before rotation
LOG_RETENTION=10                 # Number of log files to keep

# Metrics Configuration
METRICS_ENABLED=true
METRICS_PORT=9090

# Sentry Configuration
SENTRY_ENABLED=true
SENTRY_DSN=https://[key]@sentry.io/[project]
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1   # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1 # 10% profiling
```

### Configuration Options

| Variable | Description | Default | Production |
|----------|-------------|---------|------------|
| `LOG_LEVEL` | Minimum log level | `INFO` | `INFO` or `WARNING` |
| `LOG_FORMAT` | Log format | `text` | `json` |
| `LOG_FILE` | Log file path | - | `logs/mcps.log` |
| `LOG_ROTATION_SIZE` | Rotation size (MB) | `100` | `100-500` |
| `LOG_RETENTION` | Files to keep | `10` | `30-90` |
| `METRICS_ENABLED` | Enable metrics | `true` | `true` |
| `SENTRY_ENABLED` | Enable Sentry | `false` | `true` |
| `SENTRY_TRACES_SAMPLE_RATE` | Transaction sampling | `0.1` | `0.05-0.1` |

```{tip}
Use `LOG_FORMAT=json` in production for better log aggregation and parsing.
```

## Prometheus Metrics

### Available Metrics

#### HTTP Metrics

```python
# Total HTTP requests
mcps_http_requests_total{method="GET", endpoint="/servers", status="200"}

# HTTP request duration (histogram)
mcps_http_request_duration_seconds{method="GET", endpoint="/servers"}

# HTTP request size (summary)
mcps_http_request_size_bytes{method="POST", endpoint="/servers"}

# HTTP response size (summary)
mcps_http_response_size_bytes{method="GET", endpoint="/servers"}

# Requests in progress (gauge)
mcps_http_requests_in_progress{method="GET", endpoint="/servers"}
```

#### Database Metrics

```python
# Total database queries
mcps_db_queries_total{operation="select", table="server"}

# Query duration (histogram)
mcps_db_query_duration_seconds{operation="insert", table="server"}

# Connection pool metrics
mcps_db_connection_pool_size
mcps_db_connection_pool_checked_out
mcps_db_connection_pool_overflow

# Connection errors
mcps_db_connection_errors_total{error_type="timeout"}
```

#### Cache Metrics

```python
# Cache operations
mcps_cache_operations_total{operation="get", status="hit"}
mcps_cache_operations_total{operation="get", status="miss"}

# Cache hit rate (0-1)
mcps_cache_hit_rate

# Cache operation duration
mcps_cache_operation_duration_seconds{operation="get"}

# Cache memory usage
mcps_cache_memory_bytes

# Total cache keys
mcps_cache_keys_total
```

#### Business Metrics

```python
# Total servers indexed
mcps_servers_total{host_type="github"}

# Server health score distribution
mcps_servers_health_score

# Harvest operations
mcps_harvest_operations_total{source="github", status="success"}
mcps_harvest_duration_seconds{source="npm"}
mcps_harvest_items_total{source="pypi", item_type="tool"}

# Social media metrics
mcps_social_posts_total{platform="reddit"}
mcps_social_sentiment_score{platform="twitter"}
```

#### Background Task Metrics

```python
# Background task execution
mcps_background_tasks_total{task_name="harvest_github", status="success"}
mcps_background_task_duration_seconds{task_name="harvest_github"}

# Tasks currently running
mcps_background_tasks_running

# Total scheduled jobs
mcps_scheduled_jobs_total
```

#### System Metrics

```python
# Memory usage
mcps_system_memory_bytes{type="total"}
mcps_system_memory_bytes{type="available"}
mcps_system_memory_bytes{type="used"}

# CPU usage
mcps_system_cpu_percent
```

### Accessing Metrics

#### Metrics Endpoint

```bash
# Get all metrics
curl http://localhost:8000/metrics

# Expected output (Prometheus format):
# TYPE mcps_http_requests_total counter
mcps_http_requests_total{method="GET",endpoint="/servers",status="200"} 1523
# TYPE mcps_db_query_duration_seconds histogram
mcps_db_query_duration_seconds_bucket{operation="select",table="server",le="0.005"} 145
```

#### Using Prometheus

Configure Prometheus to scrape MCPS metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mcps'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Using Metrics in Code

#### Decorator Usage

```python
from packages.harvester.metrics import (
    track_time,
    count_calls,
    db_query_duration_seconds,
    harvest_operations_total,
)

# Track execution time
@track_time(db_query_duration_seconds, {"operation": "select", "table": "servers"})
async def get_all_servers():
    async with async_session_maker() as session:
        result = await session.execute(select(Server))
        return result.scalars().all()

# Count function calls
@count_calls(harvest_operations_total, {"source": "github", "status": "success"})
async def harvest_github_repo(url: str):
    # ... harvest logic
    pass
```

#### Context Manager Usage

```python
from packages.harvester.metrics import MetricTimer, InProgressGauge, http_request_duration_seconds

# Time operations
async def process_request():
    async with MetricTimer(http_request_duration_seconds, method="GET", endpoint="/servers"):
        # ... processing logic
        result = await fetch_servers()
    return result

# Track in-progress operations
async def handle_request():
    async with InProgressGauge(http_requests_in_progress, method="POST"):
        # ... request handling
        pass
```

#### Manual Metric Recording

```python
from packages.harvester.metrics import (
    http_requests_total,
    servers_total,
    cache_hit_rate,
)

# Increment counter
http_requests_total.labels(method="GET", endpoint="/servers", status="200").inc()

# Set gauge
servers_total.labels(host_type="github").set(1523)

# Record value in histogram
cache_hit_rate.set(0.85)
```

## Structured Logging

### Log Formats

#### JSON Format (Production)

```json
{
  "timestamp": "2025-11-19T10:30:00.123Z",
  "time": "2025-11-19 10:30:00.123",
  "level": "INFO",
  "severity": "INFO",
  "message": "Server harvested successfully",
  "logger": "packages.harvester.adapters.github",
  "module": "github",
  "function": "harvest",
  "line": 145,
  "process": 1234,
  "thread": 5678,
  "request_id": "abc123",
  "correlation_id": "xyz789",
  "user_id": "user@example.com",
  "environment": "production",
  "service": "mcps",
  "extra": {
    "server_id": 123,
    "stars": 1500,
    "health_score": 95
  }
}
```

#### Text Format (Development)

```
2025-11-19 10:30:00.123 | INFO     | github:harvest:145 [req=abc123 corr=xyz789] | Server harvested successfully
```

### Using Logging

#### Basic Logging

```python
from loguru import logger

# Simple logging
logger.info("Server indexed successfully")
logger.warning("Cache miss for key: user:123")
logger.error("Failed to connect to database")

# With extra context
logger.info(
    "Server harvested",
    server_id=123,
    stars=1500,
    health_score=95,
)
```

#### Request Context Logging

```python
from packages.harvester.logging import RequestContext
from loguru import logger
import uuid

async def process_request(request):
    # All logs within this context will have the same request_id
    async with RequestContext(
        request_id=str(uuid.uuid4()),
        correlation_id=request.headers.get("X-Correlation-ID"),
        user_id=request.user.id if request.user else None,
    ):
        logger.info("Processing request")  # Includes request_id
        result = await do_work()
        logger.info("Request completed")    # Same request_id
        return result
```

#### Performance Logging

```python
from packages.harvester.logging import PerformanceLogger, log_execution_time

# Context manager
async def fetch_data():
    async with PerformanceLogger("database_query", threshold_ms=100):
        result = await db.query()
    # Logs: "database_query completed in 123.45ms" (if > 100ms)

# Decorator
@log_execution_time("fetch_servers", level="info")
async def fetch_servers():
    await asyncio.sleep(1)
    return servers
```

### Log Aggregation

#### Loki Configuration

```yaml
# docker-compose.yml
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yaml:/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - ./logs:/mcps/logs
    - ./promtail-config.yaml:/etc/promtail/config.yml
  command: -config.file=/etc/promtail/config.yml
```

#### ELK Stack Configuration

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /mcps/logs/*.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "mcps-logs-%{+yyyy.MM.dd}"
```

## Sentry Error Tracking

### Configuration

```python
# Sentry is automatically configured if SENTRY_ENABLED=true
# and SENTRY_DSN is set in environment
```

### Error Reporting

```python
from loguru import logger

try:
    result = await risky_operation()
except Exception as e:
    # This error is automatically sent to Sentry
    logger.exception("Operation failed")
    raise
```

### Manual Error Capture

```python
import sentry_sdk

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Capture message
sentry_sdk.capture_message("Something went wrong", level="error")

# Add context
with sentry_sdk.push_scope() as scope:
    scope.set_tag("server_id", 123)
    scope.set_context("server", {"name": "example", "stars": 1500})
    sentry_sdk.capture_exception(exception)
```

### Transaction Monitoring

```python
import sentry_sdk

# Monitor transaction performance
with sentry_sdk.start_transaction(name="harvest_github"):
    with sentry_sdk.start_span(op="fetch", description="Fetch repository"):
        data = await fetch_repo()

    with sentry_sdk.start_span(op="parse", description="Parse metadata"):
        parsed = parse_data(data)

    with sentry_sdk.start_span(op="store", description="Store in database"):
        await store_data(parsed)
```

## Health Checks

### Available Endpoints

#### Basic Health Check

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

#### Database Health Check

```bash
curl http://localhost:8000/health/db

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00Z",
  "database": {
    "healthy": true,
    "latency_ms": 2.45,
    "database_type": "postgresql",
    "pool_size": 20,
    "pool_checked_in": 18,
    "pool_checked_out": 2,
    "pool_overflow": 0
  }
}
```

#### Cache Health Check

```bash
curl http://localhost:8000/health/cache

# Response:
{
  "status": "healthy",
  "timestamp": "2025-11-19T10:30:00Z",
  "cache": {
    "healthy": true,
    "latency_ms": 1.23,
    "version": "7.0.5",
    "used_memory": "2.5M",
    "connected_clients": 5,
    "uptime_seconds": 86400
  }
}
```

### Kubernetes Health Probes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: mcps
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /health/db
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2
```

## Grafana Dashboards

### Sample Dashboard Configuration

```json
{
  "dashboard": {
    "title": "MCPS Overview",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "targets": [
          {
            "expr": "rate(mcps_http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Database Query Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, mcps_db_query_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "mcps_cache_hit_rate"
          }
        ]
      },
      {
        "title": "Servers Indexed",
        "targets": [
          {
            "expr": "mcps_servers_total"
          }
        ]
      }
    ]
  }
}
```

### Key Metrics to Monitor

#### Application Performance

- **Request Rate:** `rate(mcps_http_requests_total[5m])`
- **Request Latency (p95):** `histogram_quantile(0.95, mcps_http_request_duration_seconds_bucket)`
- **Error Rate:** `rate(mcps_http_requests_total{status=~"5.."}[5m])`
- **Requests in Progress:** `mcps_http_requests_in_progress`

#### Database Performance

- **Query Latency (p95):** `histogram_quantile(0.95, mcps_db_query_duration_seconds_bucket)`
- **Connection Pool Utilization:** `mcps_db_connection_pool_checked_out / mcps_db_connection_pool_size`
- **Connection Errors:** `rate(mcps_db_connection_errors_total[5m])`

#### Cache Performance

- **Cache Hit Rate:** `mcps_cache_hit_rate`
- **Cache Latency:** `mcps_cache_operation_duration_seconds`
- **Cache Memory:** `mcps_cache_memory_bytes`

#### Business Metrics

- **Servers Indexed:** `mcps_servers_total`
- **Harvest Success Rate:** `rate(mcps_harvest_operations_total{status="success"}[1h]) / rate(mcps_harvest_operations_total[1h])`
- **Average Health Score:** `avg(mcps_servers_health_score)`

## Alerting

### Prometheus Alert Rules

```yaml
# alerts.yml
groups:
  - name: mcps_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(mcps_http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/second"

      # Database connection pool exhaustion
      - alert: DatabasePoolExhausted
        expr: mcps_db_connection_pool_checked_out / mcps_db_connection_pool_size > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool near exhaustion"

      # Cache unavailable
      - alert: CacheUnavailable
        expr: up{job="mcps", path="/health/cache"} == 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Redis cache is unavailable"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, mcps_http_request_duration_seconds_bucket) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API latency is high"
          description: "95th percentile latency is {{ $value }}s"
```

## Troubleshooting

### No Metrics Available

**Problem:** `/metrics` endpoint returns empty or no data

**Solutions:**

```bash
# 1. Check metrics are enabled
echo $METRICS_ENABLED  # Should be "true"

# 2. Check endpoint is accessible
curl http://localhost:8000/metrics

# 3. Restart application
docker-compose restart mcps-api
```

### Logs Not Appearing

**Problem:** Logs are not being written

**Solutions:**

```bash
# 1. Check log level
echo $LOG_LEVEL  # Should be INFO or lower

# 2. Check log file permissions
ls -la logs/mcps.log

# 3. Check log configuration
LOG_FORMAT=text LOG_LEVEL=DEBUG docker-compose restart mcps-api
```

### Sentry Not Receiving Errors

**Problem:** Errors not appearing in Sentry

**Solutions:**

```bash
# 1. Check Sentry is enabled
echo $SENTRY_ENABLED  # Should be "true"
echo $SENTRY_DSN  # Should be set

# 2. Test Sentry manually
python -c "import sentry_sdk; sentry_sdk.init('$SENTRY_DSN'); sentry_sdk.capture_message('test')"

# 3. Check sample rate
echo $SENTRY_TRACES_SAMPLE_RATE  # 0.1 = 10% of events
```

## Best Practices

### 1. Log Levels

```{admonition} Good Practice
:class: tip

- **DEBUG:** Detailed diagnostic information (development only)
- **INFO:** General informational messages (default)
- **WARNING:** Warning messages for potentially harmful situations
- **ERROR:** Error messages for serious problems
- **CRITICAL:** Critical errors requiring immediate attention
```

### 2. Metric Naming

```{admonition} Good Practice
:class: tip

- Use `_total` suffix for counters
- Use `_seconds` suffix for durations
- Use `_bytes` suffix for sizes
- Include relevant labels (but not too many)
- Use snake_case for names
```

### 3. Error Handling

```{admonition} Good Practice
:class: tip

- Always log exceptions with `logger.exception()`
- Include context in error messages
- Use appropriate log levels
- Don't log sensitive data
- Add request IDs for correlation
```

### 4. Performance

```{admonition} Good Practice
:class: tip

- Use structured logging (JSON) in production
- Set appropriate log rotation and retention
- Monitor metric cardinality (avoid high-cardinality labels)
- Use sampling for high-volume traces
- Archive old logs to cold storage
```

## See Also

- [Production Deployment](production-deployment.md) - Deploy monitoring stack
- [Caching Guide](caching.md) - Cache metrics and monitoring
- [API Health Endpoints](../api/health-endpoints.md) - Detailed health check documentation
- [Architecture](../architecture.md) - System architecture overview
