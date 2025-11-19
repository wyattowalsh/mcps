# MCPS System Architecture

> Detailed architecture documentation for the Model Context Protocol System - a knowledge graph for the MCP ecosystem.

**Version:** 2.5.0
**Last Updated:** 2025-11-19

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Scalability Considerations](#scalability-considerations)
- [Security Architecture](#security-architecture)

---

## High-Level Architecture

MCPS follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   CLI (Typer)│  │ FastAPI REST │  │  Next.js UI  │          │
│  │   Interface  │  │     API      │  │  (Future)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼──────────────────┐
│         │         BUSINESS LOGIC LAYER        │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │              Harvester Engine                     │           │
│  │  (Orchestration, Retry Logic, Checkpointing)     │           │
│  └──────────┬───────────────────────────────────────┘           │
│             │                                                    │
│             ├──────────────┬──────────────┬──────────────┐      │
│             │              │              │              │      │
│      ┌──────▼──────┐┌──────▼──────┐┌──────▼──────┐┌────▼─────┐│
│      │   GitHub    ││    NPM      ││    PyPI     ││  Docker  ││
│      │   Adapter   ││  Adapter    ││  Adapter    ││  Adapter ││
│      └──────┬──────┘└──────┬──────┘└──────┬──────┘└────┬─────┘│
│             └──────────────┴──────────────┴──────────────┘      │
│                             │                                    │
│             ┌───────────────┼───────────────┐                   │
│             │               │               │                   │
│      ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐          │
│      │    AST      │ │  Embedding  │ │ Bus Factor  │          │
│      │  Security   │ │  Generator  │ │  Calculator │          │
│      │  Analyzer   │ │             │ │             │          │
│      └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌──────────────────────────────────────────────────┐          │
│  │              SQLite Database (WAL Mode)          │          │
│  │         + sqlite-vec Extension (Vectors)         │          │
│  └──────────┬───────────────────────────────────────┘          │
│             │                                                    │
│      ┌──────▼──────┐   ┌──────────┐   ┌──────────┐            │
│      │  Parquet    │   │  JSONL   │   │  Vector  │            │
│      │  Exports    │   │  Exports │   │  Binary  │            │
│      └─────────────┘   └──────────┘   └──────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Separation of Concerns:** Clear boundaries between presentation, business logic, and data layers
2. **Polymorphic Adapters:** Source-specific logic isolated in adapter classes
3. **Resilient by Design:** Retry logic, checkpointing, and graceful degradation
4. **SQLite-First:** Local-first data storage for zero-latency analytics
5. **Exportable by Default:** All data available in analytical formats

---

## System Components

### 1. Harvester Engine

**Location:** `/home/user/mcps/packages/harvester/`

**Responsibilities:**
- Orchestrate ETL workflows
- Manage retry logic with exponential backoff
- Coordinate adapter execution
- Handle checkpointing and recovery

**Key Classes:**
- `BaseHarvester` - Abstract base class for all adapters
- `HTTPClient` - Shared HTTP client with tenacity retry logic
- `CheckpointManager` - Processing state management

**Technology:**
- **Tenacity:** Exponential backoff retry (5 attempts, 2-30s wait)
- **httpx:** Async HTTP client with connection pooling (10 connections)
- **Loguru:** Structured logging with rotation

---

### 2. Adapter Layer

**Location:** `/home/user/mcps/packages/harvester/adapters/`

Each adapter implements the **Strategy Pattern** with three core methods:

```python
class BaseHarvester(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch raw data from source."""
        pass

    @abstractmethod
    async def parse(self, data: Dict[str, Any]) -> Server:
        """Transform raw data into Server model."""
        pass

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server to database (common implementation)."""
        pass
```

#### 2.1 GitHub Adapter

**File:** `adapters/github.py`

**Strategy:**
- Single GraphQL query fetches all required data
- Avoids multiple REST API calls
- Parses `mcp.json`, `package.json`, `pyproject.toml` in-memory

**GraphQL Query Structure:**
```graphql
query GetRepoData($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    # Metadata
    name, description, stargazerCount, forkCount
    # Files (as blobs)
    mcpJson: object(expression: "HEAD:mcp.json") { text }
    packageJson: object(expression: "HEAD:package.json") { text }
    pyprojectToml: object(expression: "HEAD:pyproject.toml") { text }
    readme: object(expression: "HEAD:README.md") { text }
    # Social data
    mentionableUsers(first: 10) { nodes { login } }
    releases(first: 5) { nodes { tagName, publishedAt } }
  }
}
```

**Authentication:**
- Requires `GITHUB_TOKEN` environment variable
- Falls back to unauthenticated (60 req/hour limit)
- Authenticated: 5,000 req/hour

**Error Handling:**
- GraphQL errors returned as structured JSON
- 404s raise `HarvesterError`
- Rate limits trigger exponential backoff

#### 2.2 NPM Adapter

**File:** `adapters/npm.py`

**Strategy:**
- Fetch package metadata from registry API
- Download `.tgz` tarball to memory (no disk I/O)
- Extract `package.json` and scan for `mcpServers` config

**API Endpoints:**
```
Registry API: https://registry.npmjs.org/{package-name}
Tarball URL: https://registry.npmjs.org/{package}/-/{package}-{version}.tgz
```

**Security:**
- Checks for "zip bombs" (uncompressed > 500MB)
- Uses `tarfile` in-memory extraction
- Never executes package code (static analysis only)

#### 2.3 PyPI Adapter

**File:** `adapters/pypi.py`

**Strategy:**
- Fetch package JSON from PyPI API
- Download `.whl` or `.tar.gz` to memory
- Extract metadata and scan for MCP configuration

**API Endpoint:**
```
https://pypi.org/pypi/{package}/json
```

**Challenges:**
- PyPI doesn't have a standardized MCP config location
- Must scan common files: `pyproject.toml`, `setup.py`, `__init__.py`
- Heuristic detection of `@mcp.tool` decorators

#### 2.4 Docker Adapter (Future)

**File:** `adapters/docker.py`

**Strategy:**
- Fetch manifest v2 schema 2 from Docker registry
- Parse config blob for environment variables
- Detect MCP-specific env vars (`MCP_PORT`, `STDIO`)

**Challenges:**
- Requires token authentication flow
- Must handle multi-arch images
- Layer inspection without full pull

#### 2.5 HTTP Adapter (Future)

**File:** `adapters/http.py`

**Strategy:**
- Direct MCP introspection via SSE/HTTP
- Send `initialize` request
- Call `tools/list`, `resources/list`, `prompts/list`
- Immediately disconnect after metadata collection

**Challenges:**
- Protocol version negotiation
- Timeout handling for unresponsive servers
- Authentication (if required)

---

### 3. Analysis Pipeline

**Location:** `/home/user/mcps/packages/harvester/analysis/`

#### 3.1 AST Security Analyzer

**File:** `analysis/ast_analyzer.py`

**Purpose:** Detect dangerous code patterns without executing code

**Methodology:**
- **Python:** Uses `ast.NodeVisitor` to walk syntax trees
- **TypeScript/JavaScript:** Regex-based fallback (future: tree-sitter)

**Detection Categories:**

| Category | Python Patterns | JS/TS Patterns |
|----------|----------------|----------------|
| Code Execution | `eval()`, `exec()`, `compile()` | `eval()` |
| Subprocess | `subprocess.run()`, `os.system()` | `child_process.exec()`, `spawn()` |
| Network | `socket`, `requests`, `httpx` | `fetch()`, `http`, `net` |
| Filesystem | `os`, `shutil`, `pathlib` | `fs.writeFile()`, `fs-extra` |

**Risk Scoring Algorithm:**
```python
def calculate_risk_score(patterns: List[str]) -> RiskLevel:
    if "eval()" in patterns or "exec()" in patterns:
        return RiskLevel.CRITICAL

    has_subprocess = any("subprocess" in p for p in patterns)
    has_network = any("network" in p for p in patterns)

    if has_subprocess and (has_network or has_filesystem):
        return RiskLevel.HIGH
    elif has_subprocess:
        return RiskLevel.HIGH
    elif has_network or has_filesystem:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.SAFE
```

#### 3.2 Embedding Generator (Future)

**File:** `analysis/embeddings.py`

**Purpose:** Generate semantic vectors for similarity search

**Methodology:**
- OpenAI `text-embedding-3-small` model (1536 dimensions)
- Batch processing (50 descriptions per API call)
- Content hashing to avoid re-embedding

**Storage:**
- Vectors stored as JSON arrays in `toolembedding` table
- Converted to binary for sqlite-vec operations
- Exported to `.bin` format for numpy/torch

#### 3.3 Bus Factor Calculator (Future)

**File:** `analysis/bus_factor.py`

**Purpose:** Assess project maintenance risk

**Methodology:**
```python
# Fetch last 100 commits
commits = get_commit_history(repo, limit=100)

# Calculate contribution distribution
top_author_commits = max(commits.values())
total_commits = sum(commits.values())
top_author_percentage = top_author_commits / total_commits

# Classify risk
if top_author_percentage > 0.8:
    bus_factor = "LOW"  # High risk - single maintainer
elif top_author_percentage > 0.5:
    bus_factor = "MEDIUM"
else:
    bus_factor = "HIGH"  # Low risk - distributed team
```

---

### 4. Data Layer

#### 4.1 Database (SQLite + sqlite-vec)

**Connection Management:**
```python
# Async connection with aiosqlite
engine = create_async_engine(
    "sqlite+aiosqlite:///data/mcps.db",
    connect_args={"check_same_thread": False},
)

# Enable WAL mode for concurrent reads
await conn.execute("PRAGMA journal_mode=WAL;")
await conn.execute("PRAGMA foreign_keys=ON;")
```

**ORM:** SQLModel (Pydantic v2 + SQLAlchemy 2.0)

**Migration System:** Alembic
- Auto-generate migrations from model changes
- Version control for schema evolution
- Rollback support

**Vector Extension:**
- `sqlite-vec` extension for KNN search
- Virtual tables for vector storage
- Cosine similarity search

#### 4.2 Export Engine

**Location:** `/home/user/mcps/packages/harvester/exporters/exporter.py`

**Parquet Exporter:**
```python
schema = pa.schema([
    ("id", pa.int64()),
    ("name", pa.string()),
    ("stars", pa.int32()),
    ("health_score", pa.int32()),
    # ... more fields
])

table = pa.Table.from_pylist(data, schema=schema)
pq.write_table(table, output_file, compression="snappy")
```

**JSONL Exporter:**
```python
# LLM fine-tuning format
{
    "messages": [
        {
            "role": "user",
            "content": "Create a tool for reading files"
        },
        {
            "role": "assistant",
            "content": '{"type": "object", "properties": {...}}'
        }
    ]
}
```

**Vector Exporter:**
- Binary dump: float32 little-endian
- Metadata: JSON with tool ID mappings

---

## Data Flow

### Ingestion Flow

```
┌─────────────┐
│ User Input  │ (URL or package name)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ CLI Command Handler │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Adapter Selection   │ (auto-detect or explicit)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ fetch() - Raw Data  │ (HTTP/GraphQL/API call)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ parse() - Transform │ (JSON parsing, validation)
└──────┬──────────────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   AST    │  │Dependency│  │  Health  │  │   Risk   │
│ Analysis │  │ Parsing  │  │  Score   │  │  Level   │
└──────┬───┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │           │             │             │
       └───────────┴─────────────┴─────────────┘
                   │
                   ▼
       ┌─────────────────────┐
       │ store() - Persist   │ (Upsert to SQLite)
       └──────┬──────────────┘
              │
              ▼
       ┌─────────────────────┐
       │   Database Commit   │
       └─────────────────────┘
```

### Export Flow

```
┌─────────────┐
│ CLI Export  │ (format: parquet|jsonl)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Query Database      │ (SELECT with joins)
└──────┬──────────────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Servers  │  │   Tools  │  │ Vectors  │
│  Query   │  │  Query   │  │  Query   │
└──────┬───┘  └────┬─────┘  └────┬─────┘
       │           │             │
       ▼           ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Parquet  │  │  JSONL   │  │  Binary  │
│ Schema   │  │ Format   │  │  Format  │
└──────┬───┘  └────┬─────┘  └────┬─────┘
       │           │             │
       └───────────┴─────────────┘
                   │
                   ▼
       ┌─────────────────────┐
       │   Write to Files    │
       └─────────────────────┘
```

---

## Technology Stack

### Backend (Python 3.12+)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **ORM** | SQLModel 0.0.16 | Pydantic v2 + SQLAlchemy 2.0 integration |
| **Database** | SQLite 3.35+ | ACID-compliant local storage with WAL mode |
| **Vector Search** | sqlite-vec 0.1.0+ | KNN similarity search extension |
| **Migrations** | Alembic 1.17.2+ | Schema version control |
| **HTTP Client** | httpx 0.27.0+ | Async HTTP with connection pooling |
| **Retry Logic** | tenacity 9.0.0+ | Exponential backoff decorators |
| **Logging** | loguru 0.7.3+ | Structured logging with rotation |
| **CLI** | typer 0.15.0+ | Type-safe command-line interface |
| **Settings** | pydantic-settings 2.12.0+ | Environment variable management |
| **Exports** | pyarrow 18.0.0+ | Parquet format support |
| **AST Analysis** | ast (stdlib) + tree-sitter | Python/TypeScript parsing |
| **API Framework** | FastAPI 0.115.0+ | REST API (future) |
| **ASGI Server** | uvicorn 0.32.0+ | Production server (future) |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Ruff** | Linting and formatting (100-char line length) |
| **MyPy** | Static type checking |
| **pytest** | Unit and integration testing |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Code coverage reporting |
| **uv** | Fast Python package management |

### Frontend (Future)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Next.js 15 | React 19 RC with App Router |
| **Styling** | Tailwind CSS 4 (Oxide) | Utility-first CSS |
| **Database Access** | better-sqlite3 | Direct SQLite reads (server components) |
| **Visualization** | D3.js + Visx | Force-directed graphs and charts |
| **UI Components** | Shadcn UI | Accessible, customizable components |
| **Icons** | lucide-react | Icon library |

---

## Design Decisions

### 1. Why SQLite Instead of PostgreSQL?

**Decision:** Use SQLite as the primary database

**Rationale:**
- **Portability:** Single-file database, easy to backup/replicate
- **Zero Configuration:** No server setup or management
- **Local-First:** Zero network latency for analytics
- **Git-Friendly:** Can commit to Git LFS for versioning
- **Sufficient Scale:** Handles millions of records efficiently
- **Vector Support:** sqlite-vec extension for semantic search

**Trade-offs:**
- ❌ No built-in replication
- ❌ Single-writer limitation (mitigated by WAL mode)
- ✅ Perfect for read-heavy analytics workloads

### 2. Why Async/Await Throughout?

**Decision:** Use `async/await` for all I/O operations

**Rationale:**
- HTTP requests are inherently async
- Allows concurrent adapter execution
- Efficient connection pooling with httpx
- Scales to thousands of concurrent requests

**Implementation:**
```python
async with httpx.AsyncClient(limits=httpx.Limits(max_connections=10)) as client:
    tasks = [adapter.harvest(url) for url in urls]
    results = await asyncio.gather(*tasks)
```

### 3. Why GraphQL for GitHub?

**Decision:** Use GraphQL instead of REST API for GitHub

**Rationale:**
- **Efficiency:** Single request fetches all required data
- **Bandwidth:** Only request needed fields
- **Rate Limits:** Saves 3-5 REST calls per repository

**Comparison:**
```
REST Approach:
1. GET /repos/:owner/:repo (metadata)
2. GET /repos/:owner/:repo/contents/mcp.json
3. GET /repos/:owner/:repo/contents/package.json
4. GET /repos/:owner/:repo/contributors
5. GET /repos/:owner/:repo/releases
= 5 API calls

GraphQL Approach:
1. POST /graphql (all data in one request)
= 1 API call
```

### 4. Why Parquet for Exports?

**Decision:** Use Parquet as primary export format

**Rationale:**
- **Columnar Storage:** Optimized for analytical queries
- **Compression:** 10x smaller than CSV
- **Type Safety:** Enforces schema
- **Ecosystem:** Works with pandas, DuckDB, Spark, BigQuery

**Performance:**
```
CSV:      100 MB, 1000 servers, ~5 seconds to load
Parquet:   10 MB, 1000 servers, ~0.5 seconds to load
```

### 5. Why Monorepo Structure?

**Decision:** Single repository for backend, API, and frontend

**Rationale:**
- **Shared Models:** SQLModel definitions used by all components
- **Atomic Changes:** Update schema + API + UI in single PR
- **Simplified CI/CD:** Single build pipeline
- **Context Management:** Easier for AI code assistants

**Structure:**
```
mcps/
├── packages/harvester/  # Backend logic
├── apps/api/            # FastAPI service
└── apps/web/            # Next.js frontend
```

---

## Scalability Considerations

### Current Scale (Phase 1-4)

- **Servers:** 1,000 - 10,000 servers
- **Tools:** 10,000 - 100,000 tools
- **Database Size:** 100 MB - 1 GB
- **Query Latency:** <10ms (indexed queries)
- **Ingestion Speed:** 100-200 servers/hour (GitHub rate limits)

### Future Scale (Phase 5-6)

**Horizontal Scaling:**
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Harvester   │    │  Harvester   │    │  Harvester   │
│   Worker 1   │    │   Worker 2   │    │   Worker 3   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                  ┌────────▼────────┐
                  │   Job Queue     │
                  │   (Redis)       │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │  Central SQLite │
                  │  (Read Replicas)│
                  └─────────────────┘
```

**Optimization Strategies:**
1. **Sharding:** Partition by `host_type`
2. **Caching:** Redis for hot queries
3. **CDN:** Serve Parquet exports via CloudFront
4. **Background Jobs:** Celery for long-running tasks

---

## Security Architecture

### Input Validation

**Strategy:** Never trust external data

**Implementation:**
- Pydantic validation on all inputs
- SQLModel validation before database writes
- Regex validation for URLs and package names

### Code Execution Prevention

**Strategy:** Static analysis only, never import/execute

**Implementation:**
```python
# NEVER DO THIS:
import importlib
module = importlib.import_module(downloaded_package)

# ALWAYS DO THIS:
code = Path(downloaded_package).read_text()
tree = ast.parse(code)
analyzer = PythonASTAnalyzer()
analyzer.visit(tree)
```

### Dependency Scanning

**Strategy:** Detect dangerous libraries before storage

**Implementation:**
```python
DANGEROUS_LIBRARIES = {
    "npm": {"child_process", "shelljs", "execa"},
    "pypi": {"subprocess", "os", "sys"}
}

if any(dep.library_name in DANGEROUS_LIBRARIES[dep.ecosystem]
       for dep in server.dependencies):
    server.risk_level = RiskLevel.HIGH
```

### API Security (Future)

**Strategy:** Rate limiting + authentication + CORS

**Implementation:**
```python
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

app = FastAPI()

@app.get("/api/servers", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def list_servers():
    ...
```

---

## Performance Optimizations

### Database Optimizations

1. **Indexes on Foreign Keys:**
   ```sql
   CREATE INDEX idx_tool_server_id ON tool(server_id);
   CREATE INDEX idx_dependency_server_id ON dependency(server_id);
   ```

2. **WAL Mode for Concurrent Reads:**
   ```sql
   PRAGMA journal_mode=WAL;
   ```

3. **Eager Loading with SQLAlchemy:**
   ```python
   stmt = select(Server).options(
       selectinload(Server.tools),
       selectinload(Server.dependencies)
   )
   ```

### HTTP Client Optimizations

1. **Connection Pooling:**
   ```python
   client = httpx.AsyncClient(limits=httpx.Limits(
       max_connections=10,
       max_keepalive_connections=5
   ))
   ```

2. **Exponential Backoff:**
   ```python
   @retry(
       stop=stop_after_attempt(5),
       wait=wait_exponential(multiplier=1, min=2, max=30)
   )
   async def fetch_with_retry(url):
       ...
   ```

---

## Future Architecture Enhancements

### Phase 7: Real-Time Updates

```
┌──────────────┐
│   Webhook    │ (GitHub, NPM, PyPI)
│   Listeners  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Message Queue│ (Redis Streams)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Worker     │ (Background processing)
│    Pool      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Database   │ (Updated)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  WebSocket   │ (Push updates to clients)
│  Broadcast   │
└──────────────┘
```

---

**For implementation details, see:**
- [DATA_DICTIONARY.md](/home/user/mcps/DATA_DICTIONARY.md) - Database schema
- [CONTRIBUTING.md](/home/user/mcps/CONTRIBUTING.md) - Development guidelines
- [PRD.md](/home/user/mcps/PRD.md) - Product requirements
