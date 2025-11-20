---
title: Data Dictionary
description: Comprehensive reference for all database schemas and data formats
version: 2.5.0
last_updated: 2025-11-19
---

# Data Dictionary

Comprehensive reference for all database schemas, data formats, and relationships in the Model Context Protocol System.

**Database:** SQLite 3 with WAL mode + sqlite-vec extension

## Overview

The MCPS database uses SQLite as its primary data store, leveraging the following key features:

- **ACID Compliance:** Full transactional support with WAL (Write-Ahead Logging) mode
- **Vector Search:** sqlite-vec extension for semantic similarity queries
- **JSON Support:** Native JSON columns for flexible schema storage
- **Foreign Keys:** Enforced referential integrity across all relationships
- **Cascading Deletes:** Automatic cleanup of related entities

**Connection String:**

```text
sqlite+aiosqlite:///data/mcps.db
```

**Key Settings:**

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
```

## Database Tables

### Core Entities

#### server

The canonical representation of an MCP server from any source.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `uuid` | TEXT | UNIQUE, NOT NULL, INDEXED | UUID v4 identifier |
| `name` | TEXT | NOT NULL, INDEXED | Server display name |
| `primary_url` | TEXT | UNIQUE, NOT NULL, INDEXED | Canonical identifier |
| `host_type` | TEXT | NOT NULL, INDEXED | Source platform (see HostType enum) |
| `description` | TEXT | NULLABLE | Human-readable description |
| `stars` | INTEGER | DEFAULT 0, INDEXED | GitHub stars or popularity metric |
| `health_score` | INTEGER | DEFAULT 0 | Calculated 0-100 health metric |
| `risk_level` | TEXT | DEFAULT 'unknown' | Security risk assessment |
| `last_indexed_at` | TIMESTAMP | NOT NULL | Last successful indexing |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**

- `idx_server_uuid` on `uuid`
- `idx_server_name` on `name`
- `idx_server_primary_url` on `primary_url`
- `idx_server_host_type` on `host_type`
- `idx_server_stars` on `stars` (for ranking)

### Functional Entities

#### tool

Individual tools exposed by MCP servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `name` | TEXT | NOT NULL | Tool name (unique within server) |
| `description` | TEXT | NULLABLE | Human-readable tool description |
| `input_schema` | JSON | DEFAULT {} | JSON Schema for tool arguments |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |

#### toolembedding

Vector embeddings for semantic search across tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `tool_id` | INTEGER | FOREIGN KEY → tool.id, UNIQUE, NOT NULL | Parent tool reference |
| `vector` | JSON | NOT NULL | 1536-dimensional embedding (stored as JSON array) |
| `model_name` | TEXT | DEFAULT 'text-embedding-3-small' | OpenAI embedding model used |

```{note}
Vectors are stored as JSON for portability but converted to binary format for sqlite-vec operations.
```

## Enumerations

### HostType

Source platform for MCP servers.

| Value | Description |
|-------|-------------|
| `github` | GitHub repository |
| `gitlab` | GitLab repository |
| `npm` | NPM package registry |
| `pypi` | Python Package Index (PyPI) |
| `docker` | Docker container registry |
| `http` | Direct HTTP/SSE endpoint |

### RiskLevel

Security risk assessment levels.

| Value | Description | Criteria |
|-------|-------------|----------|
| `safe` | Verified and sandboxed | Official repos with no dangerous operations |
| `moderate` | Network or read-only FS | Uses network/filesystem but verified |
| `high` | Unverified with dangerous ops | Shell execution, write access, subprocess |
| `critical` | Malicious patterns detected | `eval()`, `exec()`, known CVEs |
| `unknown` | Not yet analyzed | Pending security analysis |

## Example Queries

### Find all servers by ecosystem

```sql
SELECT name, primary_url, stars, health_score
FROM server
WHERE host_type = 'github'
  AND verified_source = TRUE
ORDER BY stars DESC
LIMIT 10;
```

### Get tools with embeddings for semantic search

```sql
SELECT
    t.id,
    t.name,
    t.description,
    s.name as server_name,
    te.model_name
FROM tool t
JOIN server s ON t.server_id = s.id
LEFT JOIN toolembedding te ON t.id = te.tool_id
WHERE te.id IS NOT NULL;
```

## See Also

- [Architecture](architecture.md) - System architecture and design
- [API Reference](api/harvester.md) - Harvester API reference
