# Product Requirements Document (PRD): mcps (Model Context Protocol System)

<table><tbody><tr><td><p><strong><span class="selected">Metadata</span></strong></p></td><td><p><strong><span class="selected">Details</span></strong></p></td></tr><tr><td><p><strong><span class="selected">Project Name</span></strong></p></td><td><p><code><span class="selected">mcps</span></code></p></td></tr><tr><td><p><strong><span class="selected">Version</span></strong></p></td><td><p><span class="selected">3.0.0 (Enhanced Implementation Edition)</span></p></td></tr><tr><td><p><strong><span class="selected">Status</span></strong></p></td><td><p><span class="selected">Production-Ready with Active Enhancement</span></p></td></tr><tr><td><p><strong><span class="selected">Owner</span></strong></p></td><td><p><span class="selected">Wyatt Walsh</span></p></td></tr><tr><td><p><strong><span class="selected">Target Audience</span></strong></p></td><td><p><span class="selected">AI Researchers, LLM Integrators, DevOps Engineers, Data Scientists, Security Auditors</span></p></td></tr><tr><td><p><strong><span class="selected">Design Aesthetic</span></strong></p></td><td><p><span class="selected">Technical, Clean, Data-Dense, Accent Color: </span><code><span class="selected">#6a9fb5</span></code></p></td></tr></tbody></table>

## 1\. Executive Summary

`mcps` is the definitive, centralized intelligence hub designed to aggregate, index, analyze, and visualize the Model Context Protocol (MCP) ecosystem. It serves as the "NPM" or "PyPI" equivalent for the AI Agent era, but with significantly deeper introspection capabilities.

Unlike traditional package managers or GitHub-centric crawlers, `mcps` treats the MCP ecosystem as a **heterogeneous knowledge graph**. It operates on the principle of "Universal Ingestion," recognizing that valuable MCP servers are not confined to public GitHub repositories. They exist as standalone HTTP endpoints in enterprise environments, within private GitLab/Bitbucket instances, inside Docker containers, and as raw compiled artifacts (NPM/PyPI) where source code is often opaque or unlinked.

The system leverages a **SQLite-first** architecture (`sqlite3` + `sqlite-vec`) to ensure zero-latency, local-first analytics. By avoiding heavy SaaS dependencies, it remains portable and reproducible. It persists granular metadata—down to individual prompt arguments, Python dependency trees, semantic release history, and semantic vector embeddings. This entire dataset is orchestrated by a robust, resilient Python ETL (Extract, Transform, Load) engine and presented via a high-performance Next.js 15 Dashboard, bridging the gap between raw protocol data and actionable developer intelligence.

## 2\. Implementation Status

**Current Version:** v3.0.0 - All core features successfully implemented and operational.

### ✅ Completed Phases

| Phase | Component | Status | Implementation Notes |
|-------|-----------|--------|---------------------|
| **Phase 0** | Monorepo Infrastructure | ✅ Complete | UV dependency management, Ruff linting, Alembic migrations |
| **Phase 1** | Data Modeling | ✅ Complete | SQLModel with Pydantic v2, full schema with relationships |
| **Phase 2** | Universal Harvester | ✅ Complete | 5 adapters: GitHub, NPM, PyPI, Docker, HTTP/SSE |
| **Phase 3** | Deep Analysis | ✅ Complete | AST security scanning, dependency extraction, risk scoring |
| **Phase 4** | Data Exports | ✅ Complete | Parquet, JSONL, CSV export formats |
| **Phase 5** | Dashboard | ✅ Complete | Next.js 15 with App Router, SQLite integration |
| **Phase 6** | Deployment | ✅ Complete | Multi-stage Docker, docker-compose with volumes |
| **Phase 7** | E2E Verification | ✅ Complete | Integration tests, CLI validation |
| **Phase 8** | RESTful API | ✅ Complete | FastAPI with auth, rate limiting, CRUD operations |
| **Phase 9** | Background Tasks | ✅ Complete | APScheduler with auto-refresh, health recalculation |
| **Phase 10** | Documentation | ✅ Complete | Sphinx with MyST, autodoc2, Mermaid diagrams |

### 🔧 Operational Features

- **Database Operations**: Full CRUD, bulk updates, refresh, prune stale servers
- **API Endpoints**: 15+ RESTful endpoints with OpenAPI documentation
- **Authentication**: API key-based auth with role-based access control
- **Rate Limiting**: SlowAPI integration (configurable per-endpoint limits)
- **Background Scheduler**: 4 automated tasks (refresh, health scores, risk levels, cleanup)
- **Health Monitoring**: System health checks, task progress tracking
- **Documentation Site**: Comprehensive Sphinx docs with interactive guides

### 📊 Current Capabilities

- **Multi-Source Ingestion**: GitHub, NPM, PyPI, Docker Hub, HTTP endpoints
- **Deep Metadata**: Tools, resources, prompts, dependencies, contributors, releases
- **Security Analysis**: AST-based risk detection, dangerous pattern identification
- **Health Scoring**: Algorithmic quality assessment (0-100 scale)
- **Search**: Full-text search across servers and tools
- **Export Formats**: Parquet (analytics), JSONL (LLM training), CSV (networks)

## 3\. Problem Statement

The rapid adoption of LLMs has created a fragmented ecosystem of tools that `mcps` aims to unify. The specific pain points include:

- **Severe Source Agnosticism & Discovery Fragmentation:**
    
    - Current discovery tools are overly reliant on GitHub APIs. They fail to index valid, high-quality MCP servers that are hosted on private instances, enterprise GitLab servers, or published solely as Docker containers and NPM/PyPI packages without linked source repositories.
        
    - _Consequence:_ Researchers miss out on critical tools simply because they aren't trending on GitHub.
        
- **Data Inaccessibility & Analytical Friction:**
    
    - There is no mechanism to download a "snapshot" of the entire MCP protocol landscape for offline analysis or fine-tuning. Data scientists cannot easily answer questions like "What is the most common argument name across all 'database' tools?"
        
    - _Consequence:_ The ecosystem cannot learn from itself; standardization happens by accident rather than analysis.
        
- **Agentic Hallucination Risk:**
    
    - AI Agents attempting to build or utilize tools often "guess" at implementation details (arguments, return types) because they lack a strict, validated schema registry.
        
    - _Consequence:_ Agents fail during runtime, causing crashes and poor user experience.
        
- **Blind Usage & Security Opacity:**
    
    - Users currently install MCP servers as "black boxes," unaware of the underlying weight (e.g., heavy dependencies like `torch` or `pandas` for simple tasks) or security risks (e.g., undeclared network access, shell execution capabilities).
        
    - _Consequence:_ Security breaches and bloated container sizes in production environments.
        
- **Semantic Opacity:**
    
    - Keyword search is insufficient for function discovery. A user searching for "spreadsheet" might miss a superior tool labeled "CSV Processor" or "Tabular Data Handler."
        
    - _Consequence:_ Tool duplication and low discoverability for novel solutions.
        

## 3\. System Architecture

### 3.1 The Monorepo Structure

The directory structure is strictly defined to aid Agent context window management and enforce separation of concerns between the ingestion logic and the presentation layer.

```
mcps/
├── apps/
│   ├── web/                  # Next.js 15 (React 19 RC) + Tailwind 4 (Oxide)
│   │   ├── components/       # Reusable Shadcn UI + Visx Charts
│   │   └── app/              # App Router pages
│   └── api/                  # FastAPI service (Write-Access & Admin)
├── packages/
│   └── harvester/            # The Core Python Logic (ETL Engine)
│       ├── adapters/         # Source-specific logic (GitHub, GitLab, HTTP, NPM, Docker)
│       ├── core/             # Abstract Base Classes & Interfaces
│       ├── analysis/         # AST Parsing, Security Scanning, Tree-Sitter
│       ├── models/           # SQLModel definitions (Single Source of Truth)
│       └── utils/            # Rate limiters, Tenacity retries, Hashing
├── data/                     # Persistent State
│   ├── mcps.db               # The SQLite Database (WAL Mode)
│   └── exports/              # Daily flatfile dumps (Parquet/JSONL)
├── tests/                    # Pytest (Backend) and Playwright (E2E)
├── Makefile                  # Unified command center for dev workflows
└── pyproject.toml            # Python dependency management (Poetry/UV)
```

### 3.2 Technical Stack Justification

#### **Backend & Data Engineering (Python 3.12+)**

- **Core Database:** **SQLite** (WAL mode enabled, `PRAGMA foreign_keys = ON`).

    - _Why:_ Provides ACID compliance in a single file. Easy to replicate, backup to S3, or commit to Git LFS. Zero network latency for complex joins.

- **Vector Engine:** **sqlite-vec**.

    - _Why:_ Eliminates the need for a separate vector DB (Pinecone/Weaviate), keeping the stack "lite" and self-contained.

- **ORM:** **SQLModel** (Pydantic v2 + SQLAlchemy 2.0).

    - _Why:_ Combines Pydantic's validation (crucial for messy scraped data) with SQLAlchemy's relational power.

- **API Framework:** **FastAPI** with async SQLAlchemy sessions.

    - _Why:_ High-performance async API with automatic OpenAPI documentation and type validation.

- **Authentication & Security:** **SlowAPI** (rate limiting), custom API key authentication.

    - _Why:_ Protects endpoints from abuse while maintaining simplicity for internal/enterprise use.

- **Task Scheduler:** **APScheduler** (AsyncIO backend).

    - _Why:_ Reliable cron-like scheduling for background maintenance tasks without external dependencies.

- **Resilience:** **Tenacity**.

    - _Why:_ Network scraping is inherently flaky. Exponential backoff prevents API bans and ensures eventual consistency.

- **Package Inspection:** `build`, `pkginfo`, `tarfile`, `docker-py`.

    - _Why:_ We must inspect artifacts _statically_ without executing them to prevent Arbitrary Code Execution (ACE) during ingestion.

- **Static Analysis:** `ast` (Python), `tree-sitter` (TypeScript).

    - _Why:_ Regex is insufficient for understanding code logic. ASTs allow us to map import graphs accurately.

- **Logging:** **Loguru** for structured, colorized logging.

    - _Why:_ Developer-friendly logging with automatic context and minimal configuration.

#### **Frontend (TypeScript)**

- **Framework:** **Next.js 15** (App Router).

    - _Why:_ Server Components allow direct database access (via `better-sqlite3`) for read-heavy dashboard views, bypassing API serialization overhead.

- **Visualization:** **D3.js** (Force Simulation) + **Visx**.

    - _Why:_ D3 provides the low-level physics needed for the dependency graph, while Visx handles standard accessible charts.

#### **Documentation System**

- **Documentation Generator:** **Sphinx** with MyST-Parser.

    - _Why:_ Industry-standard Python documentation with Markdown support via MyST.

- **API Documentation:** **autodoc2** for automatic API reference generation.

    - _Why:_ Keeps API docs in sync with code without manual maintenance.

- **Diagrams:** **Mermaid** support via `sphinxcontrib-mermaid`.

    - _Why:_ Inline diagrams-as-code for architecture visualization.

- **Theme:** **Furo** theme for modern, mobile-friendly docs.

    - _Why:_ Clean, accessible design optimized for technical documentation.
        

## 4\. Core Features & Ingestion Mechanics

### 4.1 The Universal Harvester (ETL Pipeline)

The harvester utilizes a **Polymorphic Strategy Pattern** to normalize data from disparate sources into a unified `Server` entity.

#### **Strategy A: GitHub Strategy (High Fidelity)**

- **Trigger:** A valid `github.com/owner/repo` URL.
    
- **Process:**
    
    1. **Metadata Fetch:** Uses GraphQL to efficiently fetch `mcp.json`, `README.md`, `pyproject.toml`, and `package.json` in a single request.
        
    2. **Deep Scan:** Clones the repository to a temporary, sandboxed volume.
        
    3. **Static Analysis:** Runs AST parsing to detect exposed tools even if `mcp.json` is missing.
        
    4. **Social Graph:** Aggregates Stargazers, Contributors, and "Used By" statistics.
        

#### **Strategy B: Registry/Artifact Strategy (Medium Fidelity)**

- **Trigger:** An NPM package (`@modelcontextprotocol/server-filesystem`) or PyPI package name.
    
- **Process:**
    
    1. **Registry Query:** Hits the NPM/PyPI JSON API for version history and author emails.
        
    2. **Artifact Analysis:** Downloads the `.tgz` or `.whl` file to memory.
        
    3. **Extraction:** Unzips the archive to read `package.json` or `metadata` files directly.
        
    4. **Heuristic Linking:** Attempts to fuzzy-match the package to a GitHub repo if the `repository` field is missing.
        

#### **Strategy C: Docker Strategy (Container Inspection)**

- **Trigger:** A Docker Hub Image (`org/mcp-server:latest`).
    
- **Process:**
    
    1. **Manifest Pull:** Fetches the image manifest and config blobs without pulling layers.
        
    2. **Layer Inspection:** Scans `ENTRYPOINT`, `CMD`, and `ENV` variables to infer the transport protocol (Stdio vs SSE).
        
    3. **Label Parsing:** Looks for `org.opencontainers.image.source` to link back to source control.
        

#### **Strategy D: Generic HTTP Strategy (Low Fidelity)**

- **Trigger:** A direct URL (`https://mcp.my-company.com/sse`).
    
- **Process:**
    
    1. **Probing:** Sends `OPTIONS` and `GET` requests to detect MCP-specific headers.
        
    2. **Handshake:** Briefly connects via Server-Sent Events (SSE) to perform the MCP initialization handshake.
        
    3. **Introspection:** Requests `tools/list`, `resources/list`, and `prompts/list` capabilities, then immediately disconnects.
        

### 4.2 Deep Content Extraction & Vectorization

The system goes beyond surface-level metadata to understand the _intent_ and _construction_ of every server.

- **Dependency Mapping:**
    
    - Parses `pyproject.toml`, `requirements.txt`, and `package.json` to build a directed graph of `Server -> Library`.
        
    - _Use Case:_ Identify "heavy" servers that import massive ML libraries for simple text tasks.
        
- **Security Heuristics (AST Analysis):**
    
    - Scans the Abstract Syntax Tree for dangerous import patterns (`subprocess`, `os.system`, `eval`, `exec`, `child_process.exec`).
        
    - Flags servers with `RiskLevel.HIGH` if these patterns are found in unverified community code.
        
- **Semantic Embeddings:**
    
    - Generates 1536-dimensional embeddings (OpenAI `text-embedding-3-small`) for every `Tool.description`, `Resource.description`, and `Prompt.description`.
        
    - Stores these directly in the `ToolEmbedding` table for fast RAG (Retrieval-Augmented Generation).
        

### 4.3 The Data Export Engine ("The Lake")

To support the data science persona, the system runs a nightly job to flatten the SQLite graph into analytical formats.

- **`servers.parquet`**: Analytical columns (`star_velocity`, `health_score`, `risk_level`, `bus_factor`).
    
- **`tools.jsonl`**: JSONL formatted specifically for LLM fine-tuning (`{"input": schema, "output": description}`).
    
- **`dependencies.csv`**: Edge list suitable for Gephi or NetworkX analysis.
    
- **`vectors.bin`**: Raw binary dump of embeddings for loading into FAISS or Annoy indices.
    

## 5\. Data Schema (SQLModel + Pydantic v2)

_Note: Models use `ConfigDict` for strict Pydantic v2 validation. The schema includes specific support for Contributors and Maintenance tracking._

```
# packages/harvester/models.py
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from pydantic import ConfigDict
from sqlalchemy import Text

# --- Enums & Constants ---
class HostType(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    NPM = "npm"
    PYPI = "pypi"
    DOCKER = "docker"
    HTTP = "http"

class RiskLevel(str, Enum):
    SAFE = "safe"          # Verified, sandboxed, or pure logic
    MODERATE = "moderate"  # Uses network or read-only FS
    HIGH = "high"          # Uses shell, write-FS, or unrestricted subprocess
    CRITICAL = "critical"  # Malicious patterns or known CVEs
    UNKNOWN = "unknown"

class DependencyType(str, Enum):
    RUNTIME = "runtime"
    DEV = "dev"
    PEER = "peer"

# --- Base Model ---
class BaseEntity(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# --- Core Entity: Server ---
class Server(BaseEntity, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)
    
    name: str = Field(index=True)
    primary_url: str = Field(unique=True, index=True) # The Canonical Identifier
    host_type: HostType = Field(index=True)
    
    # Descriptive Metadata
    description: Optional[str] = Field(sa_column=Column(Text))
    author_name: Optional[str]
    homepage: Optional[str]
    license: Optional[str]
    readme_content: Optional[str] = Field(sa_column=Column(Text)) # Full README for RAG
    
    # Taxonomy
    keywords: List[str] = Field(default=[], sa_column=Column(JSON))
    categories: List[str] = Field(default=[], sa_column=Column(JSON)) # e.g. "Database", "Filesystem"
    
    # Community Metrics
    stars: int = Field(default=0, index=True)
    downloads: int = Field(default=0)
    forks: int = Field(default=0)
    open_issues: int = Field(default=0)
    
    # Analysis & Trust
    risk_level: RiskLevel = Field(default=RiskLevel.UNKNOWN)
    verified_source: bool = Field(default=False) # Official or Manually Audited
    health_score: int = Field(default=0) # Calculated 0-100 based on maintenance & testing
    last_indexed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tools: List["Tool"] = Relationship(back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"})
    resources: List["ResourceTemplate"] = Relationship(back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"})
    prompts: List["Prompt"] = Relationship(back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"})
    dependencies: List["Dependency"] = Relationship(back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"})
    releases: List["Release"] = Relationship(back_populates="server")
    contributors: List["Contributor"] = Relationship(back_populates="server")

# --- Functional Entities ---

class Tool(BaseEntity, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    name: str
    description: Optional[str] = Field(sa_column=Column(Text))
    
    # Exact JSON Schema of arguments (crucial for Agent validation)
    input_schema: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    server: Server = Relationship(back_populates="tools")
    embedding: Optional["ToolEmbedding"] = Relationship(back_populates="tool", sa_relationship_kwargs={"cascade": "all, delete"})

class ToolEmbedding(SQLModel, table=True):
    """
    Stores vector embeddings for semantic search.
    While sqlite-vec stores these in virtual tables, we map them here for ORM access.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    tool_id: int = Field(foreign_key="tool.id", unique=True)
    
    # 1536 dims for openai-small. 
    # Stored as JSON list for portability, converted to binary blob for sqlite-vec ops.
    vector: List[float] = Field(sa_column=Column(JSON)) 
    model_name: str = Field(default="text-embedding-3-small")
    
    tool: Tool = Relationship(back_populates="embedding")

class ResourceTemplate(BaseEntity, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    uri_template: str # e.g. "postgres://{host}/{db}/schema"
    name: Optional[str]
    mime_type: Optional[str]
    description: Optional[str]
    
    server: Server = Relationship(back_populates="resources")

class Prompt(BaseEntity, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    name: str
    description: Optional[str]
    arguments: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    
    server: Server = Relationship(back_populates="prompts")

# --- Knowledge Graph & People Entities ---

class Dependency(BaseEntity, table=True):
    """Tracks what libraries the MCP server uses"""
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    library_name: str = Field(index=True)
    version_constraint: Optional[str]
    ecosystem: str # 'pypi', 'npm'
    type: DependencyType = Field(default=DependencyType.RUNTIME)
    
    server: Server = Relationship(back_populates="dependencies")

class Release(BaseEntity, table=True):
    """Tracks version history and changelogs"""
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    version: str = Field(index=True) # e.g. "1.0.4"
    changelog: Optional[str] = Field(sa_column=Column(Text))
    published_at: datetime
    
    server: Server = Relationship(back_populates="releases")

class Contributor(BaseEntity, table=True):
    """Tracks the human element for 'Bus Factor' analysis"""
    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")
    
    username: str
    platform: str # "github", "gitlab"
    commits: int = 0
    
    server: Server = Relationship(back_populates="contributors")
```

## 6\. Operational Workflow & DevEx

The `Makefile` acts as the central nervous system for the project, abstracting away complex Python/Node commands.

```
# Makefile
.PHONY: all ingest-universal ingest-docker serve db-migrate clean

setup:
	uv pip install -r requirements.txt
	cd apps/web && pnpm install

db-migrate:
	# Generate and apply Alembic migrations
	# Uses --autogenerate to detect SQLModel changes
	uv run alembic revision --autogenerate -m "update_schema"
	uv run alembic upgrade head

ingest-universal:
	# Runs the ETL pipeline with all strategies enabled
	# --target="all" implies scraping sources, parsing artifacts, and vetting
	uv run python -m packages.harvester.cli ingest --strategy=auto --target="all"

ingest-docker:
	# Specific target for Docker Hub scraping
	uv run python -m packages.harvester.cli ingest --strategy=docker --target="mcp-server"

export-data:
	# Flattens the DB to Parquet/JSONL for data science
	uv run python -m packages.harvester.cli export --format=parquet --destination=./data/exports

serve:
	# Starts API (FastAPI) and Web (Next.js) in parallel
	# Uses 'make -j 2' to run concurrent processes
	make -j 2 run-api run-web

run-api:
	uv run uvicorn apps.api.main:app --reload --port 8000

run-web:
	cd apps/web && pnpm dev --port 3000

clean:
	rm -rf data/*.db
	rm -rf apps/web/.next
```

## 7\. Functional Requirements (Detailed)

### 7.1 Database Update Operations

The system provides comprehensive CRUD operations and maintenance capabilities:

#### **Create, Read, Update, Delete (CRUD)**

- **Create:** Not directly exposed (servers are ingested via harvester)
- **Read:** Full querying with filters (host_type, risk_level, verified status)
- **Update:** Single server updates, bulk updates with filter conditions
- **Delete:** Admin-only soft/hard delete with cascade to related entities

#### **Refresh Operations**

- **Single Refresh:** Re-harvest a specific server by URL to update metadata
- **Auto-Refresh:** Background task refreshes servers every 7 days automatically
- **Batch Refresh:** Bulk refresh servers matching filter criteria

#### **Bulk Update Operations**

- **Filter-Based:** Update multiple servers matching complex filter conditions
- **Field Updates:** Modify stars, health_score, risk_level, categories, etc.
- **Validation:** Pydantic validation ensures data integrity during bulk operations

#### **Maintenance Operations**

- **Prune Stale Servers:** Remove servers inactive for N days (default: 180)
- **Health Score Recalculation:** Daily automated recalculation for all servers
- **Risk Level Updates:** Daily automated security re-assessment
- **Statistics Generation:** Real-time stats on server counts, distributions, etc.

### 7.2 RESTful API Features

#### **Authentication & Authorization**

- **API Key Authentication:** Header-based (`X-API-Key`) authentication
- **Role-Based Access:** Different access levels (development, admin)
- **Endpoint Protection:** All endpoints require valid API key
- **Admin-Only Operations:** Delete, bulk update, prune require admin role

#### **Rate Limiting**

- **Per-Endpoint Limits:** Configurable limits (e.g., 60/min for reads, 30/min for writes)
- **IP-Based Tracking:** Limits enforced per remote address
- **Graceful Degradation:** Returns 429 with retry-after header when exceeded

#### **OpenAPI Documentation**

- **Auto-Generated Docs:** FastAPI generates interactive Swagger UI at `/docs`
- **ReDoc Interface:** Alternative documentation at `/redoc`
- **Type Safety:** Request/response models with Pydantic validation

#### **API Endpoints**

| Endpoint | Method | Rate Limit | Auth | Description |
|----------|--------|------------|------|-------------|
| `/health` | GET | 100/min | None | Health check |
| `/servers` | GET | 60/min | API Key | List servers with pagination |
| `/servers/{id}` | GET | 60/min | API Key | Get server details |
| `/servers/{id}` | PUT | 30/min | API Key | Update server |
| `/servers/{id}` | DELETE | 20/min | Admin | Delete server |
| `/servers/refresh` | POST | 10/min | API Key | Refresh server data |
| `/tools` | GET | 60/min | API Key | List tools |
| `/search` | GET | 30/min | API Key | Full-text search |
| `/admin/update-health-scores` | POST | 5/min | Admin | Recalculate all health scores |
| `/admin/update-risk-levels` | POST | 5/min | Admin | Recalculate all risk levels |
| `/admin/prune-stale` | POST | 5/min | Admin | Remove stale servers |
| `/admin/bulk-update` | POST | 5/min | Admin | Bulk update servers |
| `/admin/stats` | GET | 10/min | Admin | Database statistics |

### 7.3 Background Task Scheduler

#### **Scheduled Tasks**

| Task | Schedule | Purpose |
|------|----------|---------|
| Auto-refresh servers | Every 7 days | Re-harvest servers not updated recently |
| Health score recalculation | Daily at 2 AM | Update quality metrics |
| Risk level recalculation | Daily at 2:30 AM | Update security assessment |
| Stale server cleanup | Weekly (Sunday 3 AM) | Remove inactive servers |

#### **Task Management**

- **Progress Tracking:** Real-time progress updates for long-running tasks
- **Error Handling:** Graceful failure with error logging
- **Manual Trigger:** Admin can trigger any task on-demand via CLI
- **Status Monitoring:** View task history, success/failure rates

### 7.4 Health Monitoring

#### **System Health**

- **Database Connectivity:** Check SQLite connection and WAL mode
- **API Availability:** Health endpoint returns service status
- **Background Tasks:** Monitor scheduler status and job queue

#### **Metrics Tracking**

- **Server Counts:** Total servers by host_type, risk_level
- **Tool/Resource Counts:** Distribution of capabilities
- **Dependency Analysis:** Most common dependencies, version distributions
- **Quality Metrics:** Average health scores, risk level breakdowns

### 7.5 Handling "Ghost" Servers (Non-GitHub)

- **Scenario:** A user inputs `@smithery/filesystem` (an NPM package) or a direct link to a `.whl` file that has no corresponding public GitHub repository (a "Ghost" server).
    
- **System Behavior:**
    
    1. **Detection:** The system attempts to resolve the URL to GitHub. If it returns a 404, it switches to `RegistryStrategy`.
        
    2. **Acquisition:** It downloads the latest tarball/wheel from the registry.
        
    3. **Extraction:** It inflates the artifact in memory.
        
    4. **Parsing:** It reads `package.json` for tool definitions. If unavailable, it scans the source JS/Python files for `new McpServer()` or `@mcp.tool` decorators.
        
    5. **Indexing:** The server is indexed with `host_type="npm"` and `primary_url="npm://@smithery/filesystem"`.
        
    6. **Visualization:** On the dashboard, this node appears with a distinct "Package Only" icon, alerting users that source history is unavailable.
        

### 7.2 Semantic Search & RAG (Retrieval Augmented Generation)

- **Query:** "I need a tool that can parse CSV files and insert them into a SQL database."
    
- **Flow:**
    
    1. **Embedding:** The query is sent to OpenAI to generate a 1536-dim vector.
        
    2. **Vector Search:** A cosine similarity search is executed against the `ToolEmbedding` table using `sqlite-vec`.
        
    3. **Re-Ranking:** Results are re-ranked based on `Server.health_score` and `Server.stars` to prioritize robust tools over experimental ones.
        
    4. **Presentation:** The UI displays the relevant tools, grouped by their parent Server, with a "Confidence Score" badge.
        

### 7.3 Automated Risk Analysis

- **Rule:** The system automatically flags high-risk servers to protect users.
    
- **Logic:**
    
    - IF `Dependency` list contains `os`, `subprocess`, `sys`, or `shutil` (Python) OR `child_process`, `fs` (Node.js)...
        
    - AND `verified_source` is `False`...
        
    - THEN set `RiskLevel` to `RiskLevel.HIGH` and append a warning flag to the `Server` entity.
        
    - **UI Implication:** These servers display a red "Unverified & High Risk" banner on their details page.
        

## 8\. Success Metrics & KPIs

- **Robustness:** < 1% Failure rate on "Ghost" Server indexing (NPM/PyPI fallbacks). The system must gracefully handle malformed `package.json` files.
    
- **Data Depth:** > 90% of indexed servers must have populated `dependencies` and `tools` tables. Empty metadata records are considered failures.
    
- **Completeness:** 100% of servers listed on major aggregators (e.g., `glama.ai`, `smithery.ai`) are indexed within 24 hours of discovery.
    
- **Performance:** The Dashboard must load the "Global Graph" visualization for 5,000+ nodes in under 1.5 seconds using local SQLite reads.
    

## 9\. Agentic Implementation Protocols

_Specific instructions for AI Agents (e.g., Cursor, Windsurf) generating code from this PRD._

### Protocol A: Database & Schema Integrity

- **Constraint:** Use `alembic` for _all_ schema changes. Never use `SQLModel.metadata.create_all()` in production code.
    
- **Instruction:** When generating SQLModel classes, ensure `sa_column=Column(JSON)` is used for all list/dict fields to ensure strict SQLite compatibility. SQLite does not support native array types like Postgres, so JSON serialization is mandatory.
    

### Protocol B: Vector Math & Performance

- **Constraint:** Do not perform vector math (cosine similarity) in pure Python loops if avoidable.
    
- **Instruction:** Check for the presence of `sqlite-vec`. If available, offload the search query to the DB engine. Only fallback to `numpy`/`scipy` in-memory calculation if the extension fails to load.
    

### Protocol C: Static Analysis & Security

- **Constraint:** **NEVER** import a downloaded module to inspect it. Importing runs code.
    
- **Instruction:** Use `ast.parse()` for Python and `tree-sitter` for TypeScript/JavaScript. Walk the syntax tree to find class definitions and decorators. If you see `eval()` or `exec()` in the AST, immediately tag the server as `RiskLevel.CRITICAL`.
    

### Protocol D: Context Window Optimization

- **Constraint:** The codebase is a Monorepo.

- **Instruction:** When asked to work on the backend, only read/index files in `packages/harvester` and `apps/api`. Do not pollute the context window with `apps/web` frontend code unless explicitly integrating an API endpoint.

## 10\. Enhancement Roadmap (Future Phases)

This section outlines potential future enhancements to extend MCPS capabilities beyond the current implementation.

### Phase 11: Real-Time Communication (Q1 2025)

**Objective:** Add WebSocket support for real-time updates to dashboard and external clients.

- **WebSocket Server:** Implement with `fastapi-websocket` or standalone `websockets` server
- **Event Streaming:** Broadcast server updates, ingestion progress, health score changes
- **Client SDK:** TypeScript/Python SDK for subscribing to real-time events
- **Use Cases:**
  - Live dashboard updates during batch ingestion
  - Real-time notifications for security alerts
  - Progress tracking for long-running tasks

**Tech Stack:** `fastapi.WebSocket`, Redis for pub/sub (optional), Server-Sent Events (SSE) fallback

### Phase 12: Advanced Search & Discovery (Q2 2025)

**Objective:** Enhance search capabilities with Elasticsearch and vector search improvements.

- **Elasticsearch Integration:** Full-text search with fuzzy matching, faceting, aggregations
- **Enhanced Vector Search:** Upgrade to `sqlite-vec` 2.0 or evaluate ChromaDB/Qdrant
- **Hybrid Search:** Combine keyword, semantic, and faceted search with re-ranking
- **Search Features:**
  - Autocomplete suggestions
  - Faceted navigation (filter by multiple dimensions)
  - "Similar to this" recommendations
  - Trending searches analytics

**Tech Stack:** Elasticsearch 8.x, `sentence-transformers` for local embeddings

### Phase 13: Machine Learning & Intelligence (Q2-Q3 2025)

**Objective:** Add ML-powered features for classification, anomaly detection, and recommendations.

- **Auto-Classification:** Train classifier to categorize servers (Database, Filesystem, AI, etc.)
- **Quality Prediction:** ML model to predict health_score from metadata
- **Anomaly Detection:** Identify suspicious servers (malware, abandoned projects)
- **Recommendation Engine:** "Users who used X also used Y"
- **Dependency Vulnerability Scanning:** Integration with OSV/CVE databases

**Tech Stack:** `scikit-learn`, `transformers`, `torch` (optional), OSV API

### Phase 14: Multi-Tenancy & Enterprise Features (Q3 2025)

**Objective:** Support multiple organizations with isolated data and custom policies.

- **Organization Model:** Separate schemas or row-level security
- **Custom Adapters:** Allow organizations to add private GitLab/Bitbucket sources
- **Access Control:** Fine-grained permissions (read/write/admin per organization)
- **Audit Logging:** Track all API calls, data modifications, user actions
- **SSO Integration:** SAML/OAuth2 for enterprise authentication
- **Custom Risk Policies:** Organization-specific risk scoring rules

**Tech Stack:** PostgreSQL (for multi-tenancy), `authlib`, RBAC framework

### Phase 15: Performance & Scale (Q4 2025)

**Objective:** Optimize for 100K+ servers with distributed processing.

- **Redis Caching:** Cache frequently accessed servers, search results
- **Rate Limit with Redis:** Distributed rate limiting across multiple API instances
- **Database Sharding:** Partition servers by host_type or geographic region
- **Async Ingestion:** Distributed task queue (Celery/RQ) for parallel harvesting
- **CDN Integration:** Serve static exports via CloudFront/Cloudflare
- **Prometheus Metrics:** Export metrics for monitoring (request rates, ingestion throughput)
- **Read Replicas:** SQLite read replicas or migrate to PostgreSQL

**Tech Stack:** Redis, Celery/RQ, Prometheus, Grafana, PostgreSQL (migration)

### Phase 16: GraphQL API (Q4 2025)

**Objective:** Provide flexible querying with GraphQL alongside REST API.

- **GraphQL Schema:** Define schema for Server, Tool, Resource, Prompt, Dependency
- **Nested Queries:** Allow fetching servers with tools, dependencies in single query
- **Pagination:** Cursor-based pagination for large result sets
- **Subscriptions:** Real-time updates via GraphQL subscriptions
- **DataLoader:** Batch and cache database queries to avoid N+1 problems

**Tech Stack:** `strawberry-graphql` or `graphene-python`, `aiodataloader`

### Phase 17: Plugin System & Extensibility (2026)

**Objective:** Allow third-party developers to extend MCPS with custom adapters and analyzers.

- **Plugin Architecture:** Define plugin interface for adapters, analyzers, exporters
- **Plugin Registry:** Marketplace for community-contributed plugins
- **Sandboxing:** Run untrusted plugins in containers or restricted environments
- **Plugin API:** Stable API contract with versioning
- **Examples:**
  - Adapter for proprietary package registries
  - Custom security scanners
  - Export formats (Excel, Neo4j, etc.)

**Tech Stack:** `pluggy`, Docker for sandboxing, semantic versioning

### Phase 18: Developer Experience Enhancements (2026)

**Objective:** Improve CLI and developer tools for easier interaction.

- **CLI Auto-Completion:** Bash/Zsh completion scripts for all commands
- **Interactive Mode:** REPL-like interface for exploring data
- **VSCode Extension:** Syntax highlighting, autocomplete for mcp.json
- **GitHub Action:** Pre-built action for CI/CD ingestion workflows
- **Python/TypeScript SDKs:** Idiomatic client libraries for programmatic access
- **CLI Plugins:** Extend CLI with custom commands

**Tech Stack:** `click-completion`, `prompt_toolkit`, VSCode Extension API

### Prioritization Criteria

Features will be prioritized based on:

1. **User Demand:** Feedback from GitHub issues, community surveys
2. **Impact:** Features that unlock new use cases or significantly improve existing ones
3. **Complexity:** Balance between effort required and value delivered
4. **Dependencies:** Technical prerequisites (e.g., PostgreSQL migration enables multi-tenancy)
5. **Maintenance:** Preference for solutions with minimal ongoing maintenance burden

### Community Contributions

The project welcomes community contributions for any roadmap items. High-priority items will be marked as "good first issue" or "help wanted" on GitHub to encourage participation.