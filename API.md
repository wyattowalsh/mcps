# MCPS API Documentation

> REST API documentation for the Model Context Protocol System.

**Version:** 2.5.0 (Future Implementation)
**Base URL:** `http://localhost:8000/api/v1`
**Status:** 📅 Planned for Phase 5

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Servers](#servers)
  - [Tools](#tools)
  - [Search](#search)
  - [Analytics](#analytics)
  - [Admin](#admin)
- [Error Handling](#error-handling)
- [Response Formats](#response-formats)
- [Pagination](#pagination)
- [Filtering and Sorting](#filtering-and-sorting)
- [WebSocket Endpoints](#websocket-endpoints)

---

## Overview

The MCPS API provides programmatic access to the MCP ecosystem knowledge graph. It is built with FastAPI and follows REST principles with JSON responses.

**Features:**
- Read-only public access (no auth required)
- Write access requires API key
- Real-time updates via WebSocket
- GraphQL endpoint for complex queries (future)
- OpenAPI/Swagger documentation at `/docs`

**Technology Stack:**
- **Framework:** FastAPI 0.115.0+
- **Server:** Uvicorn with `--workers 4`
- **Database:** Direct SQLite access (read replicas)
- **Caching:** Redis for hot queries
- **Rate Limiting:** FastAPI-Limiter

---

## Authentication

### Public Endpoints (No Auth Required)

Most read endpoints are public:
- `GET /servers`
- `GET /tools`
- `GET /search`
- `GET /analytics/*`

### Protected Endpoints (API Key Required)

Write operations require an API key:
- `POST /servers/ingest`
- `PUT /servers/{id}`
- `DELETE /servers/{id}`

**Header Format:**
```http
Authorization: Bearer <your-api-key>
```

**Example:**
```bash
curl -H "Authorization: Bearer mcps_abc123xyz789" \
  http://localhost:8000/api/v1/servers/ingest
```

### Obtaining an API Key

1. Register at `/api/v1/auth/register`
2. Verify email
3. Request API key at `/api/v1/auth/keys/create`
4. Store key securely (shown only once)

---

## Rate Limiting

**Default Limits:**
- **Public:** 100 requests per minute
- **Authenticated:** 1000 requests per minute
- **Admin:** Unlimited

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1638360000
```

**Error Response (429):**
```json
{
  "detail": "Rate limit exceeded. Retry after 60 seconds.",
  "retry_after": 60
}
```

---

## Endpoints

### Servers

#### List All Servers

```http
GET /api/v1/servers
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `limit` | integer | 20 | Items per page (max 100) |
| `host_type` | string | - | Filter by host type: `github`, `npm`, `pypi`, etc. |
| `verified` | boolean | - | Filter verified sources |
| `risk_level` | string | - | Filter by risk: `safe`, `moderate`, `high`, `critical` |
| `min_stars` | integer | - | Minimum star count |
| `min_health` | integer | - | Minimum health score (0-100) |
| `sort` | string | `stars` | Sort by: `stars`, `health_score`, `created_at`, `name` |
| `order` | string | `desc` | Sort order: `asc`, `desc` |

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/servers?host_type=github&min_stars=100&limit=10"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "name": "servers",
      "primary_url": "https://github.com/modelcontextprotocol/servers",
      "host_type": "github",
      "description": "Official MCP servers collection",
      "author_name": "Anthropic",
      "homepage": "https://modelcontextprotocol.io",
      "license": "MIT",
      "keywords": ["mcp", "tools", "filesystem"],
      "categories": ["Official", "Multi-Server"],
      "stars": 1250,
      "downloads": 0,
      "forks": 85,
      "open_issues": 12,
      "risk_level": "safe",
      "verified_source": true,
      "health_score": 95,
      "last_indexed_at": "2025-11-19T10:30:00Z",
      "created_at": "2025-11-01T08:00:00Z",
      "updated_at": "2025-11-19T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 42,
    "pages": 5
  }
}
```

#### Get Server by ID

```http
GET /api/v1/servers/{id}
```

**Path Parameters:**
- `id` - Server ID or UUID

**Query Parameters:**
- `include` - Comma-separated relationships: `tools`, `resources`, `prompts`, `dependencies`, `releases`, `contributors`

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/servers/1?include=tools,dependencies"
```

**Example Response:**
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "name": "servers",
  "primary_url": "https://github.com/modelcontextprotocol/servers",
  "host_type": "github",
  "description": "Official MCP servers collection",
  "stars": 1250,
  "health_score": 95,
  "risk_level": "safe",
  "tools": [
    {
      "id": 1,
      "name": "read_file",
      "description": "Read file contents",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "File path"
          }
        },
        "required": ["path"]
      }
    }
  ],
  "dependencies": [
    {
      "id": 1,
      "library_name": "axios",
      "version_constraint": "^1.6.0",
      "ecosystem": "npm",
      "type": "runtime"
    }
  ]
}
```

#### Ingest Server (Protected)

```http
POST /api/v1/servers/ingest
```

**Request Body:**
```json
{
  "url": "https://github.com/modelcontextprotocol/servers",
  "strategy": "auto",
  "priority": "normal"
}
```

**Response:**
```json
{
  "status": "queued",
  "job_id": "job_abc123",
  "estimated_completion": "2025-11-19T10:35:00Z"
}
```

---

### Tools

#### List All Tools

```http
GET /api/v1/tools
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page |
| `server_id` | integer | - | Filter by server |
| `name` | string | - | Filter by name (partial match) |

**Example Response:**
```json
{
  "data": [
    {
      "id": 1,
      "server_id": 1,
      "server_name": "servers",
      "name": "read_file",
      "description": "Read file contents",
      "input_schema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string"
          }
        },
        "required": ["path"]
      },
      "has_embedding": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

#### Get Tool by ID

```http
GET /api/v1/tools/{id}
```

**Example Response:**
```json
{
  "id": 1,
  "server_id": 1,
  "server": {
    "id": 1,
    "name": "servers",
    "primary_url": "https://github.com/modelcontextprotocol/servers"
  },
  "name": "read_file",
  "description": "Read file contents at specified path",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "The file path to read"
      }
    },
    "required": ["path"]
  },
  "embedding": {
    "model_name": "text-embedding-3-small",
    "dimensions": 1536
  }
}
```

---

### Search

#### Full-Text Search

```http
GET /api/v1/search
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | **required** | Search query |
| `type` | string | `all` | Search type: `all`, `servers`, `tools`, `resources` |
| `limit` | integer | 20 | Max results |

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/search?q=database&type=servers&limit=10"
```

**Example Response:**
```json
{
  "query": "database",
  "results": [
    {
      "type": "server",
      "id": 5,
      "name": "postgresql-server",
      "description": "MCP server for PostgreSQL database access",
      "score": 0.95,
      "highlight": "MCP server for <mark>database</mark> access via PostgreSQL"
    },
    {
      "type": "tool",
      "id": 23,
      "server_name": "postgresql-server",
      "name": "execute_query",
      "description": "Execute SQL query on database",
      "score": 0.88,
      "highlight": "Execute SQL query on <mark>database</mark>"
    }
  ],
  "total": 15
}
```

#### Semantic Search (Vector Similarity)

```http
POST /api/v1/search/semantic
```

**Request Body:**
```json
{
  "query": "I need a tool to read CSV files and insert them into SQL",
  "limit": 10,
  "threshold": 0.7
}
```

**Response:**
```json
{
  "query": "I need a tool to read CSV files and insert them into SQL",
  "results": [
    {
      "tool_id": 42,
      "tool_name": "csv_to_database",
      "server_name": "data-tools",
      "description": "Parse CSV file and insert rows into database table",
      "similarity": 0.92,
      "server_url": "https://github.com/user/data-tools"
    },
    {
      "tool_id": 18,
      "tool_name": "import_csv",
      "server_name": "postgres-server",
      "description": "Import CSV data into PostgreSQL",
      "similarity": 0.87,
      "server_url": "https://github.com/user/postgres-server"
    }
  ],
  "total": 8
}
```

---

### Analytics

#### Server Statistics

```http
GET /api/v1/analytics/stats
```

**Example Response:**
```json
{
  "total_servers": 1250,
  "total_tools": 8420,
  "total_resources": 1230,
  "total_prompts": 450,
  "servers_by_host_type": {
    "github": 850,
    "npm": 280,
    "pypi": 95,
    "docker": 25
  },
  "servers_by_risk_level": {
    "safe": 420,
    "moderate": 680,
    "high": 125,
    "critical": 5,
    "unknown": 20
  },
  "verified_servers": 95,
  "last_updated": "2025-11-19T10:30:00Z"
}
```

#### Health Score Distribution

```http
GET /api/v1/analytics/health-distribution
```

**Example Response:**
```json
{
  "distribution": [
    {
      "category": "Excellent (80-100)",
      "count": 320,
      "percentage": 25.6,
      "avg_stars": 450
    },
    {
      "category": "Good (60-79)",
      "count": 580,
      "percentage": 46.4,
      "avg_stars": 125
    },
    {
      "category": "Fair (40-59)",
      "count": 280,
      "percentage": 22.4,
      "avg_stars": 35
    },
    {
      "category": "Poor (0-39)",
      "count": 70,
      "percentage": 5.6,
      "avg_stars": 8
    }
  ]
}
```

#### Dependency Graph

```http
GET /api/v1/analytics/dependency-graph
```

**Query Parameters:**
- `library` - Filter by specific library name
- `ecosystem` - Filter by ecosystem: `npm`, `pypi`

**Example Response:**
```json
{
  "nodes": [
    {
      "id": "server_1",
      "name": "postgres-server",
      "type": "server",
      "stars": 150
    },
    {
      "id": "lib_axios",
      "name": "axios",
      "type": "library",
      "ecosystem": "npm"
    }
  ],
  "edges": [
    {
      "source": "server_1",
      "target": "lib_axios",
      "type": "runtime"
    }
  ]
}
```

#### Trending Servers

```http
GET /api/v1/analytics/trending
```

**Query Parameters:**
- `period` - Time period: `day`, `week`, `month` (default: `week`)
- `limit` - Max results (default: 10)

**Example Response:**
```json
{
  "period": "week",
  "servers": [
    {
      "id": 42,
      "name": "ai-assistant",
      "primary_url": "https://github.com/user/ai-assistant",
      "stars": 850,
      "star_growth": 120,
      "growth_percentage": 16.4
    }
  ]
}
```

---

### Admin (Protected)

#### Trigger Re-indexing

```http
POST /api/v1/admin/reindex/{id}
```

**Path Parameters:**
- `id` - Server ID to re-index

**Response:**
```json
{
  "status": "queued",
  "server_id": 42,
  "job_id": "job_xyz789"
}
```

#### Export Database

```http
POST /api/v1/admin/export
```

**Request Body:**
```json
{
  "format": "parquet",
  "destination": "s3://mcps-exports/2025-11-19/"
}
```

**Response:**
```json
{
  "status": "started",
  "job_id": "export_abc123",
  "estimated_size": "250MB",
  "estimated_duration": "60s"
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Server with ID 9999 not found",
    "details": {
      "server_id": 9999
    }
  }
}
```

### HTTP Status Codes

| Status | Code | Description |
|--------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Maintenance mode |

### Error Codes

| Code | Description |
|------|-------------|
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `INTERNAL_ERROR` | Server error |
| `DATABASE_ERROR` | Database operation failed |

---

## Response Formats

### Pagination

All list endpoints support pagination:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

### Timestamps

All timestamps are in ISO 8601 format with UTC timezone:

```json
{
  "created_at": "2025-11-19T10:30:00Z",
  "updated_at": "2025-11-19T10:30:00Z"
}
```

### Enums

Enums are returned as lowercase strings:

```json
{
  "host_type": "github",
  "risk_level": "safe",
  "dependency_type": "runtime"
}
```

---

## Pagination

### Query Parameters

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `page` | integer | 1 | - |
| `limit` | integer | 20 | 100 |
| `offset` | integer | 0 | - |

**Note:** Use either `page` or `offset`, not both.

### Link Headers (Future)

```http
Link: <http://localhost:8000/api/v1/servers?page=2>; rel="next",
      <http://localhost:8000/api/v1/servers?page=8>; rel="last"
```

---

## Filtering and Sorting

### Filter Operators

Use query parameter syntax:

```bash
# Exact match
?host_type=github

# Greater than
?min_stars=100

# Less than
?max_issues=10

# Multiple values (OR)
?risk_level=safe,moderate

# Range
?health_score_min=60&health_score_max=90
```

### Sorting

```bash
# Sort by field (ascending)
?sort=stars

# Sort descending
?sort=stars&order=desc

# Multi-field sort
?sort=health_score,stars&order=desc,desc
```

---

## WebSocket Endpoints

### Real-Time Updates

```
ws://localhost:8000/api/v1/ws/updates
```

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/updates');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Update:', update);
};
```

**Message Types:**

```json
{
  "type": "server.created",
  "data": {
    "id": 123,
    "name": "new-server",
    "primary_url": "https://github.com/user/new-server"
  },
  "timestamp": "2025-11-19T10:30:00Z"
}
```

```json
{
  "type": "server.updated",
  "data": {
    "id": 42,
    "changes": {
      "stars": 150,
      "health_score": 85
    }
  },
  "timestamp": "2025-11-19T10:30:00Z"
}
```

---

## OpenAPI / Swagger

Interactive API documentation available at:

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

**OpenAPI JSON:**
```
http://localhost:8000/openapi.json
```

---

## Client Libraries

### Python Client (Official)

```python
from mcps_client import MCPSClient

client = MCPSClient(api_key="mcps_abc123")

# List servers
servers = client.servers.list(host_type="github", min_stars=100)

# Get server details
server = client.servers.get(1, include=["tools", "dependencies"])

# Search
results = client.search.semantic("tools for reading CSV files")

# Ingest new server
job = client.servers.ingest("https://github.com/user/repo")
```

### JavaScript Client (Future)

```javascript
import { MCPSClient } from '@mcps/client';

const client = new MCPSClient({ apiKey: 'mcps_abc123' });

// List servers
const servers = await client.servers.list({
  hostType: 'github',
  minStars: 100
});

// Semantic search
const results = await client.search.semantic({
  query: 'tools for reading CSV files',
  limit: 10
});
```

---

## Rate Limit Details

### Algorithms

**Token Bucket Algorithm:**
- Refills at constant rate
- Allows bursts up to bucket size
- Smooth over time

**Implementation:**
```python
from fastapi_limiter.depends import RateLimiter

@app.get("/api/v1/servers", dependencies=[
    Depends(RateLimiter(times=100, seconds=60))
])
async def list_servers():
    ...
```

### Best Practices

1. **Cache responses** when possible
2. **Use pagination** to reduce response sizes
3. **Implement exponential backoff** for retries
4. **Monitor rate limit headers**
5. **Upgrade to authenticated access** for higher limits

---

## Versioning

**Current Version:** v1

**Version Strategy:** URL-based versioning

```
http://localhost:8000/api/v1/...
http://localhost:8000/api/v2/...  (future)
```

**Deprecation Policy:**
- Minimum 6 months notice
- Sunset header on deprecated endpoints
- Migration guide provided

---

## Support

**Issues:**
- GitHub Issues: https://github.com/your-org/mcps/issues

**API Status:**
- Status Page: https://status.mcps.dev (future)

**Contact:**
- Email: api@mcps.dev

---

**For implementation details, see:**
- [ARCHITECTURE.md](/home/user/mcps/ARCHITECTURE.md) - System architecture
- [DATA_DICTIONARY.md](/home/user/mcps/DATA_DICTIONARY.md) - Database schema
- [CONTRIBUTING.md](/home/user/mcps/CONTRIBUTING.md) - Development guidelines
