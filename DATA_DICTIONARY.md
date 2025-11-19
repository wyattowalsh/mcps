# MCPS Data Dictionary

> Comprehensive reference for all database schemas, data formats, and relationships in the Model Context Protocol System.

**Version:** 2.5.0
**Last Updated:** 2025-11-19
**Database:** SQLite 3 with WAL mode + sqlite-vec extension

---

## Table of Contents

- [Overview](#overview)
- [Database Tables](#database-tables)
  - [Core Entities](#core-entities)
  - [Functional Entities](#functional-entities)
  - [Knowledge Graph Entities](#knowledge-graph-entities)
  - [System Entities](#system-entities)
- [Enumerations](#enumerations)
- [Relationships](#relationships)
- [Export Formats](#export-formats)
  - [Parquet Schema](#parquet-schema)
  - [JSONL Format](#jsonl-format)
  - [Vector Binary Format](#vector-binary-format)
- [Example Queries](#example-queries)

---

## Overview

The MCPS database uses SQLite as its primary data store, leveraging the following key features:

- **ACID Compliance:** Full transactional support with WAL (Write-Ahead Logging) mode
- **Vector Search:** sqlite-vec extension for semantic similarity queries
- **JSON Support:** Native JSON columns for flexible schema storage
- **Foreign Keys:** Enforced referential integrity across all relationships
- **Cascading Deletes:** Automatic cleanup of related entities

**Connection String:**
```
sqlite+aiosqlite:///data/mcps.db
```

**Key Settings:**
```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
```

---

## Database Tables

### Core Entities

#### `server`

The canonical representation of an MCP server from any source (GitHub, NPM, PyPI, Docker, HTTP).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `uuid` | TEXT | UNIQUE, NOT NULL, INDEXED | UUID v4 identifier for external references |
| `name` | TEXT | NOT NULL, INDEXED | Server display name |
| `primary_url` | TEXT | UNIQUE, NOT NULL, INDEXED | Canonical identifier (GitHub URL, NPM package, etc.) |
| `host_type` | TEXT | NOT NULL, INDEXED | Source platform (see HostType enum) |
| `description` | TEXT | NULLABLE | Human-readable description |
| `author_name` | TEXT | NULLABLE | Original author/organization name |
| `homepage` | TEXT | NULLABLE | Project homepage URL |
| `license` | TEXT | NULLABLE | SPDX license identifier (e.g., "MIT", "Apache-2.0") |
| `readme_content` | TEXT | NULLABLE | Full README content for RAG workflows |
| `keywords` | JSON | DEFAULT [] | Array of keyword strings |
| `categories` | JSON | DEFAULT [] | Array of category strings (e.g., ["Database", "Filesystem"]) |
| `stars` | INTEGER | DEFAULT 0, INDEXED | GitHub stars or popularity metric |
| `downloads` | INTEGER | DEFAULT 0 | NPM/PyPI download count |
| `forks` | INTEGER | DEFAULT 0 | GitHub fork count |
| `open_issues` | INTEGER | DEFAULT 0 | Count of open issues |
| `risk_level` | TEXT | DEFAULT 'unknown' | Security risk assessment (see RiskLevel enum) |
| `verified_source` | BOOLEAN | DEFAULT FALSE | True for official/audited sources |
| `health_score` | INTEGER | DEFAULT 0 | Calculated 0-100 health metric |
| `last_indexed_at` | TIMESTAMP | NOT NULL | Last successful indexing timestamp |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_server_uuid` on `uuid`
- `idx_server_name` on `name`
- `idx_server_primary_url` on `primary_url`
- `idx_server_host_type` on `host_type`
- `idx_server_stars` on `stars` (for ranking)

**Example Record:**
```json
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
  "last_indexed_at": "2025-11-19T10:30:00Z"
}
```

---

### Functional Entities

#### `tool`

Individual tools exposed by MCP servers. Tools are the primary functional units that AI agents can invoke.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `name` | TEXT | NOT NULL | Tool name (unique within server) |
| `description` | TEXT | NULLABLE | Human-readable tool description |
| `input_schema` | JSON | DEFAULT {} | JSON Schema for tool arguments |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Relationships:**
- `server_id` → `server.id` (CASCADE DELETE)
- `embedding` ← `toolembedding.tool_id` (1:1, CASCADE DELETE)

**Example Record:**
```json
{
  "id": 1,
  "server_id": 1,
  "name": "read_file",
  "description": "Read the contents of a file at the specified path",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "The file path to read"
      }
    },
    "required": ["path"]
  }
}
```

#### `toolembedding`

Vector embeddings for semantic search across tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `tool_id` | INTEGER | FOREIGN KEY → tool.id, UNIQUE, NOT NULL | Parent tool reference |
| `vector` | JSON | NOT NULL | 1536-dimensional embedding (stored as JSON array) |
| `model_name` | TEXT | DEFAULT 'text-embedding-3-small' | OpenAI embedding model used |

**Note:** Vectors are stored as JSON for portability but converted to binary format for sqlite-vec operations.

**Example Record:**
```json
{
  "id": 1,
  "tool_id": 1,
  "vector": [0.0023, -0.0156, 0.0089, ...],  // 1536 dimensions
  "model_name": "text-embedding-3-small"
}
```

#### `resourcetemplate`

Resource templates exposed by MCP servers for structured data access.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `uri_template` | TEXT | NOT NULL | URI template with variables (e.g., "file://{path}") |
| `name` | TEXT | NULLABLE | Resource display name |
| `mime_type` | TEXT | NULLABLE | MIME type of resource content |
| `description` | TEXT | NULLABLE | Human-readable description |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Example Record:**
```json
{
  "id": 1,
  "server_id": 1,
  "uri_template": "postgres://{host}/{database}/schema",
  "name": "Database Schema",
  "mime_type": "application/json",
  "description": "Access database schema information"
}
```

#### `prompt`

Prompt templates exposed by MCP servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `name` | TEXT | NOT NULL | Prompt template name |
| `description` | TEXT | NULLABLE | Human-readable description |
| `arguments` | JSON | DEFAULT [] | Array of argument definitions |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Example Record:**
```json
{
  "id": 1,
  "server_id": 1,
  "name": "code_review",
  "description": "Generate a code review for the specified file",
  "arguments": [
    {
      "name": "file_path",
      "description": "Path to the file to review",
      "required": true
    }
  ]
}
```

---

### Knowledge Graph Entities

#### `dependency`

Tracks library dependencies of MCP servers for weight estimation and security analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `library_name` | TEXT | NOT NULL, INDEXED | Dependency package name |
| `version_constraint` | TEXT | NULLABLE | Version specification (e.g., "^1.0.0", ">=2.0.0") |
| `ecosystem` | TEXT | NOT NULL | Package ecosystem ('npm', 'pypi') |
| `type` | TEXT | NOT NULL | Dependency type (see DependencyType enum) |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_dependency_library_name` on `library_name`

**Example Record:**
```json
{
  "id": 1,
  "server_id": 1,
  "library_name": "axios",
  "version_constraint": "^1.6.0",
  "ecosystem": "npm",
  "type": "runtime"
}
```

#### `release`

Version history and changelog tracking for maintenance velocity analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `version` | TEXT | NOT NULL, INDEXED | Semantic version (e.g., "1.0.4") |
| `changelog` | TEXT | NULLABLE | Release notes or changelog content |
| `published_at` | TIMESTAMP | NOT NULL | Release publication timestamp |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `idx_release_version` on `version`

#### `contributor`

Contributor tracking for bus factor analysis and maintenance distribution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `username` | TEXT | NOT NULL | Platform username/handle |
| `platform` | TEXT | NOT NULL | Platform identifier ('github', 'gitlab') |
| `commits` | INTEGER | DEFAULT 0 | Number of commits (when available) |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

---

### System Entities

#### `processinglog`

Checkpoint system for resilient ingestion with retry logic.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `url` | TEXT | UNIQUE, NOT NULL, INDEXED | URL being processed |
| `status` | TEXT | NOT NULL, INDEXED | Processing status (see below) |
| `attempts` | INTEGER | DEFAULT 0 | Number of processing attempts |
| `last_attempt_at` | TIMESTAMP | NULLABLE | Timestamp of last attempt |
| `error_message` | TEXT | NULLABLE | Error message from last failure |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Status Values:**
- `pending` - Queued for processing
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed after retries
- `skipped` - Intentionally skipped

---

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

### DependencyType

Type of dependency relationship.

| Value | Description |
|-------|-------------|
| `runtime` | Required for execution |
| `dev` | Development/testing only |
| `peer` | Peer dependency (NPM) |

### Capability

MCP server capability types.

| Value | Description |
|-------|-------------|
| `tools` | Exposes executable tools |
| `resources` | Provides data resources |
| `prompts` | Offers prompt templates |

---

## Relationships

### Entity Relationship Diagram (Text)

```
┌─────────────┐
│   Server    │ (Core Entity)
└──────┬──────┘
       │
       ├──────┬──────────┬──────────┬──────────┬──────────┐
       │      │          │          │          │          │
       ▼      ▼          ▼          ▼          ▼          ▼
    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
    │ Tool │ │Resource│Prompt│ │Depend│ │Release│Contrib│
    └───┬──┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
        │
        ▼
    ┌──────────┐
    │ToolEmbed │
    └──────────┘
```

### Relationship Details

| Parent | Child | Type | Cascade | Description |
|--------|-------|------|---------|-------------|
| `server` | `tool` | 1:N | DELETE | Server can have multiple tools |
| `server` | `resourcetemplate` | 1:N | DELETE | Server can expose multiple resources |
| `server` | `prompt` | 1:N | DELETE | Server can provide multiple prompts |
| `server` | `dependency` | 1:N | DELETE | Server has multiple dependencies |
| `server` | `release` | 1:N | NO CASCADE | Server has version history |
| `server` | `contributor` | 1:N | NO CASCADE | Server has multiple contributors |
| `tool` | `toolembedding` | 1:1 | DELETE | Each tool has one embedding |

---

## Export Formats

### Parquet Schema

#### servers.parquet

Flattened view of all servers with analytics columns.

```python
schema = pa.schema([
    ("id", pa.int64()),
    ("uuid", pa.string()),
    ("name", pa.string()),
    ("primary_url", pa.string()),
    ("host_type", pa.string()),
    ("description", pa.string()),
    ("author_name", pa.string()),
    ("homepage", pa.string()),
    ("license", pa.string()),
    # Metrics
    ("stars", pa.int32()),
    ("downloads", pa.int32()),
    ("forks", pa.int32()),
    ("open_issues", pa.int32()),
    # Analysis
    ("risk_level", pa.string()),
    ("health_score", pa.int32()),
    ("verified_source", pa.bool_()),
    # Timestamps
    ("created_at", pa.timestamp("ms")),
    ("updated_at", pa.timestamp("ms")),
    ("last_indexed_at", pa.timestamp("ms")),
])
```

**Compression:** Snappy
**Use Cases:** Analytical queries, data science workflows, ML feature engineering

#### dependencies.parquet

Edge list for dependency graph analysis.

```python
schema = pa.schema([
    ("server_id", pa.int64()),
    ("server_name", pa.string()),
    ("library_name", pa.string()),
    ("version_constraint", pa.string()),
    ("ecosystem", pa.string()),
    ("type", pa.string()),
])
```

**Use Cases:** Network analysis (Gephi, NetworkX), dependency tracking

---

### JSONL Format

#### tools.jsonl

LLM training format for fine-tuning on tool schema generation.

```jsonl
{"messages": [{"role": "user", "content": "Create a tool for reading file contents. The tool should be named 'read_file'."}, {"role": "assistant", "content": "{\"type\": \"object\", \"properties\": {\"path\": {\"type\": \"string\", \"description\": \"The file path to read\"}}, \"required\": [\"path\"]}"}]}
{"messages": [{"role": "user", "content": "Create a tool for executing SQL queries from postgresql-server. The tool should be named 'execute_query'."}, {"role": "assistant", "content": "{\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"SQL query to execute\"}, \"database\": {\"type\": \"string\", \"description\": \"Database name\"}}, \"required\": [\"query\"]}"}]}
```

**Format:** One JSON object per line
**Use Cases:** OpenAI fine-tuning API, LLM training datasets

---

### Vector Binary Format

#### vectors.bin

Raw binary dump of embeddings (float32 format).

**Structure:**
- Each vector: 1536 floats × 4 bytes = 6144 bytes
- Total size: 6144 × number_of_vectors bytes

**Binary Format:** IEEE 754 single-precision (float32), little-endian

#### vectors.json

Metadata file with tool ID mappings.

```json
{
  "vector_count": 150,
  "dimensions": 1536,
  "model_name": "text-embedding-3-small",
  "exported_at": "2025-11-19T10:30:00.000Z",
  "mappings": [
    {
      "index": 0,
      "tool_id": 1,
      "tool_name": "read_file"
    },
    {
      "index": 1,
      "tool_id": 2,
      "tool_name": "write_file"
    }
  ]
}
```

**Use Cases:** Loading into numpy/torch, FAISS indexing, Annoy similarity search

---

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

### Find servers with dangerous dependencies

```sql
SELECT DISTINCT
    s.name,
    s.primary_url,
    s.risk_level,
    COUNT(d.id) as dangerous_dep_count
FROM server s
JOIN dependency d ON s.id = d.server_id
WHERE d.library_name IN ('subprocess', 'child_process', 'eval', 'exec')
GROUP BY s.id
ORDER BY dangerous_dep_count DESC;
```

### Calculate dependency network (shared dependencies)

```sql
SELECT
    s1.name as server1,
    s2.name as server2,
    d1.library_name as shared_dependency,
    COUNT(*) as shared_count
FROM dependency d1
JOIN dependency d2 ON d1.library_name = d2.library_name
    AND d1.ecosystem = d2.ecosystem
    AND d1.server_id < d2.server_id
JOIN server s1 ON d1.server_id = s1.id
JOIN server s2 ON d2.server_id = s2.id
GROUP BY s1.id, s2.id, d1.library_name
ORDER BY shared_count DESC;
```

### Get health score distribution

```sql
SELECT
    CASE
        WHEN health_score >= 80 THEN 'Excellent (80-100)'
        WHEN health_score >= 60 THEN 'Good (60-79)'
        WHEN health_score >= 40 THEN 'Fair (40-59)'
        ELSE 'Poor (0-39)'
    END as health_category,
    COUNT(*) as server_count,
    ROUND(AVG(stars), 2) as avg_stars
FROM server
GROUP BY health_category
ORDER BY MIN(health_score) DESC;
```

### Find servers with recent releases

```sql
SELECT
    s.name,
    s.primary_url,
    r.version,
    r.published_at,
    julianday('now') - julianday(r.published_at) as days_since_release
FROM server s
JOIN release r ON s.id = r.server_id
WHERE julianday('now') - julianday(r.published_at) < 30
ORDER BY r.published_at DESC;
```

### Bus factor analysis (contributor concentration)

```sql
SELECT
    s.name,
    s.primary_url,
    COUNT(c.id) as contributor_count,
    MAX(c.commits) as top_contributor_commits,
    SUM(c.commits) as total_commits,
    ROUND(100.0 * MAX(c.commits) / SUM(c.commits), 2) as top_contributor_percentage
FROM server s
JOIN contributor c ON s.id = c.server_id
GROUP BY s.id
HAVING contributor_count > 1
ORDER BY top_contributor_percentage DESC;
```

### Full-text search across servers (using FTS5)

```sql
-- Note: Requires FTS5 virtual table setup
CREATE VIRTUAL TABLE server_fts USING fts5(
    name,
    description,
    readme_content,
    content=server
);

SELECT
    s.name,
    s.description,
    snippet(server_fts, 1, '<mark>', '</mark>', '...', 32) as excerpt
FROM server_fts
JOIN server s ON server_fts.rowid = s.id
WHERE server_fts MATCH 'database OR sql OR postgres'
ORDER BY rank;
```

---

## Data Integrity Constraints

### Foreign Key Constraints

All foreign key relationships are enforced with `PRAGMA foreign_keys = ON`. Violations will raise integrity errors.

### Unique Constraints

- `server.uuid` - Prevents duplicate UUID assignments
- `server.primary_url` - Ensures canonical URL uniqueness
- `toolembedding.tool_id` - One embedding per tool
- `processinglog.url` - Prevents duplicate processing entries

### Check Constraints

- `health_score` - Must be between 0 and 100
- `stars`, `downloads`, `forks`, `open_issues` - Must be non-negative
- Timestamps - Must be valid ISO 8601 format

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.5.0 | 2025-11-19 | Initial comprehensive data dictionary |

---

**For implementation details, see:**
- `/home/user/mcps/packages/harvester/models/models.py` - SQLModel definitions
- `/home/user/mcps/packages/harvester/core/models.py` - Base classes and enums
- `/home/user/mcps/packages/harvester/exporters/exporter.py` - Export format implementations
