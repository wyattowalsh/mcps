# MCPS Master Implementation Protocol (v2.5.0)

| 
Metadata

 | 

Details

 |
| --- | --- |
| 

**Project**

 | 

`mcps` (Model Context Protocol System)

 |
| 

**Architecture**

 | 

Monorepo / SQLite-First / Semantic Knowledge Graph

 |
| 

**Owner**

 | 

Wyatt Walsh

 |
| 

**Target State**

 | 

High-Fidelity Knowledge Graph of the MCP Ecosystem

 |
| 

**Status**

 | 

**Active**

 |

## Phase 0: The Monorepo Bedrock (Infrastructure)

_Objective: Establish a deterministic, reproducible development environment._

### 0.1 Repository & Polyglot Config

- \[ \] **Root Configuration:**
    
    - Initialize `pyproject.toml` (workspace root) to manage Python inclusions/exclusions.
        
    - Create `.gitignore` explicitly ignoring `data/*.db`, `data/*.db-wal`, `**/__pycache__`, `.next/`, `node_modules/`.
        
    - **Crucial:** Add `.gitattributes` to enforce `*.db binary` to prevent Git from attempting to diff SQLite files.
        
- \[ \] **Agentic Context Rules (`.cursorrules` / `.windsurfrules`):**
    
    - Create rule: "When editing `packages/harvester`, NEVER import from `apps/web`."
        
    - Create rule: "Always use `uv run` for python commands."
        
    - Create rule: "Prefer `pathlib` over `os.path`."
        

### 0.2 Python Subsystem (`packages/harvester`, `apps/api`)

- \[ \] **Dependency Locking (Strict):**
    
    - `uv add sqlmodel==0.0.16` (Ensure Pydantic v2 compatibility).
        
    - `uv add pydantic-settings` (For `.env` management).
        
    - `uv add tenacity loguru httpx typer` (Core utils).
        
    - `uv add sqlite-vec` (Ensure the pre-compiled binary wheel is selected).
        
    - `uv add alembic` (Database migrations).
        
    - **Dev Deps:** `uv add --dev pytest pytest-asyncio ruff mypy types-pyyaml`.
        
- \[ \] **Linting & Formatting:**
    
    - Configure `ruff.toml`: Enable rules `E` (Error), `F` (Pyflakes), `I` (Isort), `B` (Bugbear).
        
    - Set line length to 100.
        

### 0.3 Frontend Subsystem (`apps/web`)

- \[ \] **Next.js 15 Initialization:**
    
    - Initialize with `--typescript`, `--eslint`, `--tailwind`.
        
    - **Tailwind 4 Upgrade:** Install `tailwindcss@next` and `@tailwindcss/postcss`.
        
    - Configure `css` variables for `#6a9fb5` (Primary Accent) in `app/globals.css`.
        
- \[ \] **UI Libraries:**
    
    - Install `lucide-react`, `clsx`, `tailwind-merge`.
        
    - Install `better-sqlite3` (Native binding for direct DB reads).
        
    - Install `d3-force`, `d3-selection`, `d3-scale` (Visualization).
        
    - Install `@visx/network` (High-level graph components).
        

### 0.4 Orchestration (`Makefile`)

- \[ \] **Implement Unified Commands:**
    
    - `make install`: Runs `uv sync` and `pnpm install`.
        
    - `make db-reset`: Deletes `data/*.db` and runs `alembic upgrade head`.
        
    - `make dev`: Uses `concurrently` or background processes to run FastAPI (`:8000`) and Next.js (`:3000`).
        
    - `make lint`: Runs `ruff check .` and `next lint`.
        

## Phase 1: The Ontological Core (Data Modeling)

_Objective: Define the strict schema that governs the Knowledge Graph._

### 1.1 Abstract Base Classes (`packages/harvester/core/models.py`)

- \[ \] **BaseEntity:**
    
    - UUID field (`default_factory=uuid4`).
        
    - `created_at` / `updated_at` with `sa_column_kwargs={"server_default": func.now()}`.
        
- \[ \] **Enums:**
    
    - `HostType`: GITHUB, NPM, PYPI, DOCKER, HTTP.
        
    - `RiskLevel`: SAFE, MODERATE, HIGH, CRITICAL.
        
    - `Capability`: RESOURCES, PROMPTS, TOOLS, LOGGING.
        

### 1.2 The Relational Graph (`packages/harvester/models.py`)

- \[ \] **Server Model:**
    
    - Fields: `name`, `primary_url`, `stars`, `health_score`.
        
    - **JSON Columns:** `keywords`, `categories` defined as `sa_column=Column(JSON)`.
        
- \[ \] **Deep Metadata Models:**
    
    - `Contributor`: Fields `username`, `commits`, `platform` (For Bus Factor calc).
        
    - `Release`: Fields `version`, `changelog`, `published_at`.
        
    - `Dependency`: Fields `library_name`, `version_constraint`, `ecosystem`.
        
- \[ \] **Functional Models:**
    
    - `Tool`, `ResourceTemplate`, `Prompt`.
        
    - **Constraint:** `input_schema` must be `JSON` type.
        

### 1.3 The Vector Layer

- \[ \] **ToolEmbedding Model:**
    
    - `tool_id` (Foreign Key).
        
    - `vector`: Define as a custom column type or `JSON` (if waiting on `sqlite-vec` ORM support).
        
    - `model_name`: Default "text-embedding-3-small".
        

### 1.4 Database Operations

- \[ \] **Alembic Setup:**
    
    - Configure `alembic.ini` to point to `data/mcps.db`.
        
    - Generate Initial Migration: `uv run alembic revision --autogenerate -m "genesis"`.
        
    - Apply Migration: `uv run alembic upgrade head`.
        

## Phase 2: The Universal Harvester (ETL Engine)

_Objective: Build the resilient, polymorphic ingestion pipeline._

### 2.1 The Core Engine (`packages/harvester/engine.py`)

- \[ \] **Session Management:**
    
    - Create a global `httpx.AsyncClient` with `limit=10` connections.
        
    - Apply `tenacity` retry decorator: `stop=stop_after_attempt(5)`, `wait=wait_exponential(multiplier=1, min=2, max=30)`.
        
- \[ \] **Checkpoint System:**
    
    - Create a `ProcessingLog` table to track `(url, status, attempts)` to allow resuming interrupted scrapes.
        

### 2.2 Strategy A: GitHub Intelligence

- \[ \] **GraphQL Query Optimization:**
    
    - Write a single query to fetch:
        
        1. `object(expression: "HEAD:mcp.json") { text }`
            
        2. `object(expression: "HEAD:package.json") { text }`
            
        3. `object(expression: "HEAD:pyproject.toml") { text }`
            
        4. `stargazers { totalCount }`
            
        5. `mentionableUsers(first: 10) { nodes { login } }` (Contributors).
            
- \[ \] **Pagination Logic:** Handle `hasNextPage` for repositories with >100 tools (rare, but possible).
    

### 2.3 Strategy B: The Artifact Inspector (NPM/PyPI)

- \[ \] **Virtual Filesystem (In-Memory):**
    
    - Use `tarfile.open(fileobj=BytesIO(content))` to inspect `.tgz` without disk I/O.
        
    - **Security Check:** Check for "Zip Bombs" (uncompressed size > 500MB) before extraction.
        
- \[ \] **Manifest Parsing:**
    
    - Logic to extract `mcp` config from `package.json` -> `mcpServers` key.
        

### 2.4 Strategy C: Docker Forensics

- \[ \] **Registry API Client:**
    
    - Implement token authentication (`Bearer realm="..."`).
        
    - Fetch Manifest V2 Schema 2.
        
- \[ \] **Config Blob Parser:**
    
    - Parse the `config.digest` blob to find `Env` variables.
        
    - Heuristic: If `Env` contains `MCP_PORT` or `STDIO`, flag as valid server.
        

## Phase 3: Deep Analysis & Knowledge Enrichment

_Objective: Turn raw data into "Intelligence"._

### 3.1 Static Analysis (AST)

- \[ \] **Python Visitor (`ast.NodeVisitor`):**
    
    - `visit_Call`: Check if func name is `eval`, `exec`, `subprocess.run`.
        
    - `visit_Import`: Check if importing `socket`, `requests`, `os`.
        
- \[ \] **TypeScript Visitor (Regex/Tree-sitter):**
    
    - Regex fallback: `/(child_process|exec|spawn|bun:ffi)/`.
        
- \[ \] **Risk Scoring Algorithm:**
    
    - Base Score: 100.
        
    - `RiskLevel.CRITICAL`: If `eval` detected.
        
    - `RiskLevel.HIGH`: If `network` + `filesystem` detected + `verified=False`.
        

### 3.2 Semantic Indexing

- \[ \] **Embedding Pipeline:**
    
    - Implement `EmbeddingService` class.
        
    - Batch processing: Group descriptions into batches of 50 for OpenAI API efficiency.
        
    - **Optimization:** Hash the description text. If hash exists in DB, skip embedding (saves $$$).
        

### 3.3 Bus Factor Calculation

- \[ \] **Algorithm:**
    
    - Fetch last 100 commits.
        
    - Calculate % of code contributed by top author.
        
    - If Top Author > 80% of commits -> `BusFactor.LOW` (High Risk).
        
    - If Top 3 Authors evenly distributed -> `BusFactor.HIGH` (Safe).
        

## Phase 4: Data Engineering (The Lake)

_Objective: Reproducibility and Data Science enablement._

### 4.1 Parquet Exports

- \[ \] **Schema Definition:**
    
    - Use `pyarrow` schema for strict typing (e.g., `stars: int32`, `created_at: timestamp[ms]`).
        
- \[ \] **Flatfile Generation:**
    
    - `servers.parquet`: Join `Server` + `RiskLevel` + `BusFactor`.
        
    - `dependencies.parquet`: Exploded view of `Server` -> `Dependency`.
        

### 4.2 JSONL datasets

- \[ \] **LLM Fine-Tuning Set:**
    
    - Iterate all `Tool` records.
        
    - Format: `{"messages": [{"role": "user", "content": "Create a tool for..."}, {"role": "assistant", "content": <input_schema>}]}`.
        
    - Validation: Ensure JSON schema is valid before writing line.
        

## Phase 5: The Dashboard (Interface)

_Objective: High-performance visualization._

### 5.1 Data Access Layer

- \[ \] **Direct SQLite Access:**
    
    - Create `apps/web/lib/db.ts`.
        
    - Initialize `new Database(path, { readonly: true, fileMustExist: true })`.
        
    - **Performance:** Enable `db.pragma('journal_mode = WAL')`.
        

### 5.2 Visualizations

- \[ \] **Force-Directed Graph (`<EcosystemGraph />`):**
    
    - Nodes: Servers. Edges: Shared Dependencies.
        
    - D3 Logic: `d3.forceSimulation` with `forceManyBody` (repulsion) and `forceLink` (attraction).
        
    - **Zoom/Pan:** Implement `d3-zoom`.
        
- \[ \] **Activity Heatmap:**
    
    - Calendar view of `last_indexed_at` timestamps.
        

### 5.3 Search Experience

- \[ \] **Hybrid Search Implementation:**
    
    - Input: User types query.
        
    - Path A (Exact): Query SQLite FTS5 virtual table.
        
    - Path B (Semantic): Call API -> Embedding -> `sqlite-vec` KNN search.
        
    - Merge & Rank: Weighted average of Text Rank and Vector Similarity.
        

## Phase 6: Deployment & Ops

_Objective: Production readiness._

### 6.1 Containerization

- \[ \] **Dockerfile:**
    
    - Multi-stage build.
        
    - Stage 1: `python-builder` (Install UV, generate requirements).
        
    - Stage 2: `node-builder` (Next.js build).
        
    - Stage 3: `runner` (Alpine/Slim + SQLite libs).
        
- \[ \] **Volume Management:**
    
    - Ensure `/app/data` is a mounted volume for persistence.
        

### 6.2 CI/CD (GitHub Actions)

- \[ \] **Ingest Pipeline:**
    
    - Schedule: `cron: "0 0 * * *"` (Midnight).
        
    - Step: Checkout -> Install Python -> `make ingest-universal` -> Commit `mcps.db` (or upload artifact).
        

### 6.3 Documentation

- \[ \] **`DATA_DICTIONARY.md`:** Explicitly document the Parquet schema for data scientists.
    
- \[ \] **`CONTRIBUTING.md`:** Guide on adding new Registry Adapters.
    

## Phase 7: E2E Verification & System Handoff

_Objective: Validation of the entire "Ghost Server" to "Dashboard" pipeline._

### 7.1 The "Ghost Server" Test

- \[ \] **Input:** Execute `uv run mcps ingest --target npm --package @modelcontextprotocol/server-filesystem`.
    
- \[ \] **Verification:**
    
    - Check `ProcessingLog`: Status should be `COMPLETED`.
        
    - Check `Server` table: `host_type` should be `NPM`.
        
    - Check `RiskLevel`: Should be `SAFE` (official package) or `HIGH` (if unverified).
        
    - Check `Tool` table: Should contain `read_file` and `write_file`.
        

### 7.2 The "Knowledge Graph" Integrity Check

- \[ \] **Dependency Linkage:**
    
    - Run a query to find Servers that share a dependency on `langchain`.
        
    - Verify that `d3` force graph API returns edges between these servers.
        
- \[ \] **Vector Quality:**
    
    - Run CLI command `mcps search "read csv"`.
        
    - Verify that `@modelcontextprotocol/server-filesystem` appears in top 5 results even if "csv" is not in the name.
        

### 7.3 Dashboard Usability

- \[ \] **Performance Benchmark:**
    
    - Load Dashboard with 10,000 mock servers.
        
    - Time to Interactive (TTI) must be < 1.5s.
        
- \[ \] **Search Latency:**
    
    - Full-text search + Vector Rerank must complete in < 200ms on local hardware.