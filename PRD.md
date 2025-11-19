# Product Requirements Document (PRD): mcps (Model Context Protocol System)

<table><tbody><tr><td><p><strong><span class="selected">Metadata</span></strong></p></td><td><p><strong><span class="selected">Details</span></strong></p></td></tr><tr><td><p><strong><span class="selected">Project Name</span></strong></p></td><td><p><code><span class="selected">mcps</span></code></p></td></tr><tr><td><p><strong><span class="selected">Version</span></strong></p></td><td><p><span class="selected">2.4.0 (Comprehensive Knowledge Graph Edition)</span></p></td></tr><tr><td><p><strong><span class="selected">Status</span></strong></p></td><td><p><span class="selected">Approved for Agentic Implementation</span></p></td></tr><tr><td><p><strong><span class="selected">Owner</span></strong></p></td><td><p><span class="selected">Wyatt Walsh</span></p></td></tr><tr><td><p><strong><span class="selected">Target Audience</span></strong></p></td><td><p><span class="selected">AI Researchers, LLM Integrators, DevOps Engineers, Data Scientists, Security Auditors</span></p></td></tr><tr><td><p><strong><span class="selected">Design Aesthetic</span></strong></p></td><td><p><span class="selected">Technical, Clean, Data-Dense, Accent Color: </span><code><span class="selected">#6a9fb5</span></code></p></td></tr></tbody></table>

## 1\. Executive Summary

`mcps` is the definitive, centralized intelligence hub designed to aggregate, index, analyze, and visualize the Model Context Protocol (MCP) ecosystem. It serves as the "NPM" or "PyPI" equivalent for the AI Agent era, but with significantly deeper introspection capabilities.

Unlike traditional package managers or GitHub-centric crawlers, `mcps` treats the MCP ecosystem as a **heterogeneous knowledge graph**. It operates on the principle of "Universal Ingestion," recognizing that valuable MCP servers are not confined to public GitHub repositories. They exist as standalone HTTP endpoints in enterprise environments, within private GitLab/Bitbucket instances, inside Docker containers, and as raw compiled artifacts (NPM/PyPI) where source code is often opaque or unlinked.

The system leverages a **SQLite-first** architecture (`sqlite3` + `sqlite-vec`) to ensure zero-latency, local-first analytics. By avoiding heavy SaaS dependencies, it remains portable and reproducible. It persists granular metadata—down to individual prompt arguments, Python dependency trees, semantic release history, and semantic vector embeddings. This entire dataset is orchestrated by a robust, resilient Python ETL (Extract, Transform, Load) engine and presented via a high-performance Next.js 15 Dashboard, bridging the gap between raw protocol data and actionable developer intelligence.

## 2\. Problem Statement

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
        
- **Resilience:** **Tenacity**.
    
    - _Why:_ Network scraping is inherently flaky. Exponential backoff prevents API bans and ensures eventual consistency.
        
- **Package Inspection:** `build`, `pkginfo`, `tarfile`, `docker-py`.
    
    - _Why:_ We must inspect artifacts _statically_ without executing them to prevent Arbitrary Code Execution (ACE) during ingestion.
        
- **Static Analysis:** `ast` (Python), `tree-sitter` (TypeScript).
    
    - _Why:_ Regex is insufficient for understanding code logic. ASTs allow us to map import graphs accurately.
        

#### **Frontend (TypeScript)**

- **Framework:** **Next.js 15** (App Router).
    
    - _Why:_ Server Components allow direct database access (via `better-sqlite3`) for read-heavy dashboard views, bypassing API serialization overhead.
        
- **Visualization:** **D3.js** (Force Simulation) + **Visx**.
    
    - _Why:_ D3 provides the low-level physics needed for the dependency graph, while Visx handles standard accessible charts.
        

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

### 7.1 Handling "Ghost" Servers (Non-GitHub)

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