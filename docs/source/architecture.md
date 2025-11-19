---
title: MCPS System Architecture
description: Detailed architecture documentation for the Model Context Protocol System
version: 2.5.0
last_updated: 2025-11-19
---

# MCPS System Architecture

Detailed architecture documentation for the Model Context Protocol System - a knowledge graph for the MCP ecosystem.

## High-Level Architecture

MCPS follows a **layered architecture** with clear separation of concerns:

```{mermaid}
graph TB
    subgraph Presentation["Presentation Layer"]
        CLI[CLI - Typer]
        API[FastAPI REST API]
        WEB[Next.js UI]
    end

    subgraph Business["Business Logic Layer"]
        HARV[Harvester Engine<br/>Orchestration, Retry, Checkpointing]

        subgraph Adapters["Adapter Layer"]
            GHA[GitHub Adapter]
            NPMA[NPM Adapter]
            PYPIA[PyPI Adapter]
            DOCKER[Docker Adapter]
        end

        subgraph Analysis["Analysis Pipeline"]
            AST[AST Security Analyzer]
            EMB[Embedding Generator]
            BUS[Bus Factor Calculator]
        end
    end

    subgraph Data["Data Layer"]
        DB[(SQLite + sqlite-vec)]

        subgraph Exports["Export Formats"]
            PARQ[Parquet Files]
            JSONL[JSONL Training Data]
            VEC[Vector Binary]
        end
    end

    CLI --> HARV
    API --> HARV
    WEB --> API

    HARV --> GHA
    HARV --> NPMA
    HARV --> PYPIA
    HARV --> DOCKER

    GHA --> AST
    NPMA --> AST
    PYPIA --> AST

    AST --> DB
    EMB --> DB
    BUS --> DB

    DB --> PARQ
    DB --> JSONL
    DB --> VEC
```

### Architecture Principles

1. **Separation of Concerns:** Clear boundaries between presentation, business logic, and data layers
2. **Polymorphic Adapters:** Source-specific logic isolated in adapter classes
3. **Resilient by Design:** Retry logic, checkpointing, and graceful degradation
4. **SQLite-First:** Local-first data storage for zero-latency analytics
5. **Exportable by Default:** All data available in analytical formats

## System Components

### 1. Harvester Engine

::::{grid} 1
:gutter: 3

:::{grid-item-card} Location
`/home/user/mcps/packages/harvester/`
:::

::::

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

```{admonition} Authentication
:class: note
Requires `GITHUB_TOKEN` environment variable. Falls back to unauthenticated (60 req/hour limit). Authenticated: 5,000 req/hour.
```

#### 2.2 NPM & PyPI Adapters

See [API Reference](api/adapters.md) for detailed documentation.

### 3. Analysis Pipeline

```{mermaid}
flowchart LR
    CODE[Source Code] --> AST[AST Analyzer]
    DESC[Descriptions] --> EMB[Embedding Generator]
    REPO[Repository Data] --> BUS[Bus Factor Calculator]

    AST --> RISK[Risk Level]
    EMB --> VEC[Vector Embeddings]
    BUS --> SCORE[Health Score]

    RISK --> DB[(Database)]
    VEC --> DB
    SCORE --> DB
```

**Location:** `/home/user/mcps/packages/harvester/analysis/`

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
| **API Framework** | FastAPI 0.115.0+ | REST API (future) |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Ruff** | Linting and formatting (100-char line length) |
| **MyPy** | Static type checking |
| **pytest** | Unit and integration testing |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Code coverage reporting |
| **uv** | Fast Python package management |

## Design Decisions

### Why SQLite Instead of PostgreSQL?

```{dropdown} Decision Rationale
:open:

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
```

### Why Async/Await Throughout?

```{dropdown} Implementation Details

**Decision:** Use `async/await` for all I/O operations

**Rationale:**

- HTTP requests are inherently async
- Allows concurrent adapter execution
- Efficient connection pooling with httpx
- Scales to thousands of concurrent requests

**Implementation:**

\`\`\`python
async with httpx.AsyncClient(limits=httpx.Limits(max_connections=10)) as client:
    tasks = [adapter.harvest(url) for url in urls]
    results = await asyncio.gather(*tasks)
\`\`\`
```

### Why GraphQL for GitHub?

**Comparison:**

:::::{grid} 1 1 2 2
:gutter: 3

::::{grid-item-card} REST Approach
:class-header: bg-danger text-white

1. GET `/repos/:owner/:repo` (metadata)
2. GET `/repos/:owner/:repo/contents/mcp.json`
3. GET `/repos/:owner/:repo/contents/package.json`
4. GET `/repos/:owner/:repo/contributors`
5. GET `/repos/:owner/:repo/releases`

**= 5 API calls**
::::

::::{grid-item-card} GraphQL Approach
:class-header: bg-success text-white

1. POST `/graphql` (all data in one request)

**= 1 API call**

{bdg-success}`80% reduction in API calls`
::::

:::::

## Performance Optimizations

### Database Optimizations

```sql
-- Indexes on Foreign Keys
CREATE INDEX idx_tool_server_id ON tool(server_id);
CREATE INDEX idx_dependency_server_id ON dependency(server_id);

-- WAL Mode for Concurrent Reads
PRAGMA journal_mode=WAL;
```

### HTTP Client Optimizations

```python
# Connection Pooling
client = httpx.AsyncClient(limits=httpx.Limits(
    max_connections=10,
    max_keepalive_connections=5
))

# Exponential Backoff
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30)
)
async def fetch_with_retry(url):
    ...
```

## Security Architecture

### Input Validation

**Strategy:** Never trust external data

**Implementation:**

- Pydantic validation on all inputs
- SQLModel validation before database writes
- Regex validation for URLs and package names

### Code Execution Prevention

**Strategy:** Static analysis only, never import/execute

```{danger}
**NEVER DO THIS:**
\`\`\`python
import importlib
module = importlib.import_module(downloaded_package)
\`\`\`

**ALWAYS DO THIS:**
\`\`\`python
code = Path(downloaded_package).read_text()
tree = ast.parse(code)
analyzer = PythonASTAnalyzer()
analyzer.visit(tree)
\`\`\`
```

## See Also

- [Data Dictionary](data-dictionary.md) - Database schema reference
- [Contributing](contributing.md) - Development guidelines
- [API Documentation](api/index.md) - API reference
