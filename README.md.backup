# MCPS - Model Context Protocol System

> The definitive intelligence hub for the MCP ecosystem. Aggregates, indexes, analyzes, and visualizes Model Context Protocol servers from any source.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Version:** 2.5.0 | **Status:** Active Development

---

## Overview

MCPS is the "NPM for the AI Agent era" - a comprehensive knowledge graph that treats the Model Context Protocol ecosystem as a heterogeneous, multi-source network. Unlike traditional package registries or GitHub-centric crawlers, MCPS performs **Universal Ingestion** from:

- ✅ **GitHub repositories** (via GraphQL API)
- ✅ **NPM packages** (via registry API + tarball inspection)
- ✅ **PyPI packages** (via JSON API + wheel/sdist analysis)
- 🚧 **Docker containers** (via registry v2 + manifest inspection)
- 🚧 **HTTP/SSE endpoints** (via MCP introspection protocol)
- 🚧 **GitLab repositories** (future)

### Key Features

- **🔍 Deep Metadata Extraction:** Parses `mcp.json`, `package.json`, `pyproject.toml` to extract tools, resources, prompts, and dependencies
- **🛡️ Security Analysis:** AST-based scanning for dangerous patterns (eval, subprocess, filesystem access)
- **📊 Health Scoring:** Algorithmic calculation based on stars, activity, tests, and documentation
- **🧠 Semantic Search:** Vector embeddings (OpenAI text-embedding-3-small) for RAG workflows
- **📈 Dependency Graphs:** Full dependency tree extraction for network analysis
- **💾 SQLite-First:** Zero-latency, local-first analytics with WAL mode
- **📦 Data Lake Exports:** Parquet, JSONL, and binary vector formats for data science

---

## Quick Start

### Installation

**Prerequisites:**
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)

```bash
# Clone the repository
git clone https://github.com/your-org/mcps.git
cd mcps

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN

# Initialize database
uv run alembic upgrade head
```

### Basic Usage

#### Harvesting MCP Servers

```bash
# Ingest a GitHub repository
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/modelcontextprotocol/servers

# Ingest an NPM package
uv run python -m packages.harvester.cli ingest \
  --strategy npm \
  --target @modelcontextprotocol/server-filesystem

# Ingest a PyPI package
uv run python -m packages.harvester.cli ingest \
  --strategy pypi \
  --target mcp-server-git
```

#### Exporting Data

```bash
# Export to Parquet format (for data analysis)
uv run python -m packages.harvester.cli export \
  --format parquet \
  --destination ./data/exports

# Export to JSONL format (for LLM fine-tuning)
uv run python -m packages.harvester.cli export \
  --format jsonl \
  --destination ./data/exports
```

#### Checking Status

```bash
# View harvesting statistics
uv run python -m packages.harvester.cli status
```

---

## Architecture Overview

MCPS follows a **monorepo structure** with strict separation between data ingestion (Python) and presentation (Next.js):

```
┌─────────────────────────────────────────────────────────┐
│                    MCPS Architecture                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  GitHub    │  │    NPM     │  │   PyPI     │        │
│  │  GraphQL   │  │  Registry  │  │   JSON API │  ...   │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │
│         │               │               │               │
│         └───────────────┴───────────────┘               │
│                         │                               │
│                    ┌────▼────┐                          │
│                    │Harvester│ (Polymorphic Strategy)   │
│                    │ Adapters│                          │
│                    └────┬────┘                          │
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         │               │               │               │
│    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐          │
│    │  AST    │    │Embedding│    │  Bus    │          │
│    │Analyzer │    │Generator│    │ Factor  │          │
│    └────┬────┘    └────┬────┘    └────┬────┘          │
│         │               │               │               │
│         └───────────────┴───────────────┘               │
│                         │                               │
│                    ┌────▼────┐                          │
│                    │ SQLite  │ (+sqlite-vec)            │
│                    │Database │                          │
│                    └────┬────┘                          │
│                         │                               │
│         ┌───────────────┼───────────────┐               │
│         │               │               │               │
│    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐          │
│    │ Parquet │    │  JSONL  │    │ Vector  │          │
│    │ Exports │    │ Exports │    │ Binary  │          │
│    └─────────┘    └─────────┘    └─────────┘          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Core Components:**
- **Harvester Engine:** Resilient ETL with retry logic (tenacity)
- **Adapter Layer:** Source-specific ingestion strategies
- **Analysis Pipeline:** Security scanning, embeddings, metrics
- **SQLite Database:** ACID-compliant storage with vector search
- **Export Engine:** Analytical format conversion

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Development Workflow

### Using Make Commands

```bash
# Install all dependencies
make install

# Run database migrations
make db-migrate

# Reset database (WARNING: deletes all data)
make db-reset

# Run linting checks
make lint

# Run tests
make test

# Start development servers (API + Web)
make dev
```

### Manual Commands

```bash
# Activate virtual environment (uv creates this automatically)
source .venv/bin/activate

# Run tests with coverage
uv run pytest --cov=packages --cov-report=html

# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Type checking
uv run mypy packages/
```

---

## Project Structure

```
mcps/
├── packages/harvester/          # Core Python logic
│   ├── adapters/               # Source-specific harvesters
│   │   ├── github.py          # GitHub GraphQL adapter
│   │   ├── npm.py             # NPM registry adapter
│   │   ├── pypi.py            # PyPI JSON API adapter
│   │   ├── docker.py          # Docker registry adapter
│   │   └── http.py            # Generic HTTP/SSE adapter
│   ├── analysis/              # Analysis modules
│   │   ├── ast_analyzer.py   # Security pattern detection
│   │   ├── embeddings.py     # Vector embedding generation
│   │   └── bus_factor.py     # Contributor analysis
│   ├── core/                  # Base classes
│   │   ├── models.py         # Enums and base entities
│   │   └── base_harvester.py # Abstract harvester class
│   ├── exporters/             # Data export formats
│   │   └── exporter.py       # Parquet, JSONL, Vector
│   ├── models/                # Database models
│   │   └── models.py         # SQLModel definitions
│   ├── utils/                 # Utility modules
│   │   ├── http_client.py    # HTTP client with retries
│   │   └── checkpointing.py  # Processing state
│   ├── cli.py                 # Typer CLI interface
│   ├── database.py            # DB connection management
│   └── settings.py            # Pydantic settings
├── apps/
│   ├── api/                   # FastAPI service (future)
│   └── web/                   # Next.js dashboard (future)
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── data/                      # Data storage (gitignored)
│   ├── mcps.db               # SQLite database
│   └── exports/              # Exported data files
├── Makefile                   # Dev workflow automation
├── pyproject.toml            # Python dependencies
├── ruff.toml                 # Ruff configuration
└── alembic.ini               # Alembic configuration
```

---

## CLI Reference

### `ingest` - Harvest MCP Servers

```bash
uv run python -m packages.harvester.cli ingest [OPTIONS]
```

**Options:**
- `--strategy, -s` - Harvesting strategy: `auto|github|npm|pypi|docker|http` (default: `auto`)
- `--target, -t` - Target URL or `all` to process all sources (required)
- `--log-level, -l` - Logging level: `DEBUG|INFO|WARNING|ERROR|CRITICAL` (default: `INFO`)

**Examples:**
```bash
# GitHub repository
uv run python -m packages.harvester.cli ingest \
  -s github \
  -t https://github.com/modelcontextprotocol/servers

# NPM package
uv run python -m packages.harvester.cli ingest \
  -s npm \
  -t @modelcontextprotocol/server-filesystem

# PyPI package
uv run python -m packages.harvester.cli ingest \
  -s pypi \
  -t mcp-server-git

# Auto-detect source type
uv run python -m packages.harvester.cli ingest \
  -s auto \
  -t https://github.com/anthropics/anthropic-sdk-python
```

### `export` - Export Data to Analytical Formats

```bash
uv run python -m packages.harvester.cli export [OPTIONS]
```

**Options:**
- `--format, -f` - Export format: `parquet|jsonl` (default: `parquet`)
- `--destination, -d` - Destination directory (default: `./data/exports`)
- `--log-level, -l` - Logging level (default: `INFO`)

**Examples:**
```bash
# Export to Parquet
uv run python -m packages.harvester.cli export \
  -f parquet \
  -d ./data/exports

# Export to JSONL for LLM training
uv run python -m packages.harvester.cli export \
  -f jsonl \
  -d ./data/fine-tuning
```

**Output Files:**
- **Parquet:** `servers.parquet`, `dependencies.parquet`
- **JSONL:** `tools.jsonl`, `vectors.json`, `vectors.bin`

### `status` - View Harvesting Statistics

```bash
uv run python -m packages.harvester.cli status [OPTIONS]
```

**Options:**
- `--log-level, -l` - Logging level (default: `INFO`)

**Output:**
```
=== MCPS Harvester Status ===

Total Servers Indexed: 42

Processing Queue:
  Pending: 5
  Processing: 1
  Completed: 38
  Failed: 2
  Skipped: 0
```

---

## Database Schema

MCPS uses SQLite with the following core tables:

- **`server`** - Core server entity (name, URL, host type, metrics, risk level)
- **`tool`** - Individual tools with JSON schemas
- **`toolembedding`** - Vector embeddings for semantic search
- **`resourcetemplate`** - Resource URI templates
- **`prompt`** - Prompt templates with arguments
- **`dependency`** - Library dependencies (runtime/dev)
- **`release`** - Version history and changelogs
- **`contributor`** - Contributor information for bus factor
- **`processinglog`** - Checkpoint system for retries

For complete schema documentation, see [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# GitHub API (required for GitHub harvesting)
GITHUB_TOKEN=ghp_your_personal_access_token_here

# Environment
ENVIRONMENT=development

# Database
DATABASE_PATH=data/mcps.db
DATABASE_ECHO=false

# Logging
LOG_LEVEL=INFO
```

### GitHub Token Setup

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `public_repo` (read public repositories)
   - `read:packages` (read package metadata)
4. Copy token and add to `.env`

**Note:** Without a token, GitHub API is limited to 60 requests/hour. With a token: 5,000 requests/hour.

---

## Data Exports

### Parquet Format

Optimized for analytical queries and data science workflows.

**Files:**
- `servers.parquet` - Server metadata with analytics columns
- `dependencies.parquet` - Dependency edge list for graph analysis

**Usage with pandas:**
```python
import pandas as pd

# Load servers
servers = pd.read_parquet('data/exports/servers.parquet')

# Filter by risk level
high_risk = servers[servers['risk_level'] == 'high']

# Top servers by health score
top_servers = servers.nlargest(10, 'health_score')
```

### JSONL Format

Formatted for LLM fine-tuning and training workflows.

**Files:**
- `tools.jsonl` - Tool definitions in training format
- `vectors.json` - Vector metadata
- `vectors.bin` - Binary embedding dump

**Usage:**
```python
import json

# Load training data
with open('data/exports/tools.jsonl', 'r') as f:
    for line in f:
        example = json.loads(line)
        # Each example has 'messages' array for fine-tuning
```

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=packages --cov-report=html

# Run specific test file
uv run pytest tests/test_github_harvester.py

# Run with verbose output
uv run pytest -v

# Run in parallel
uv run pytest -n auto
```

### Writing Tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for testing guidelines and examples.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development environment setup
- Code style guidelines (Ruff, MyPy)
- How to add new registry adapters
- Testing requirements
- Pull request process

**Quick Links:**
- [Bug Reports](https://github.com/your-org/mcps/issues/new?template=bug_report.md)
- [Feature Requests](https://github.com/your-org/mcps/issues/new?template=feature_request.md)
- [GitHub Discussions](https://github.com/your-org/mcps/discussions)

---

## Documentation

- **[PRD.md](PRD.md)** - Product Requirements Document
- **[TASKS.md](TASKS.md)** - Master Implementation Protocol
- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** - Database schema reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[API.md](API.md)** - FastAPI endpoints (future)

---

## Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] SQLite database with SQLModel
- [x] Alembic migrations
- [x] Base harvester abstract class
- [x] GitHub adapter with GraphQL
- [x] CLI interface with Typer

### Phase 2: Harvesting (🚧 In Progress)
- [x] NPM adapter
- [x] PyPI adapter
- [ ] Docker adapter
- [ ] HTTP/SSE adapter
- [ ] Checkpoint system with retries

### Phase 3: Analysis (🚧 In Progress)
- [x] AST-based security scanning
- [ ] OpenAI embedding generation
- [ ] Bus factor calculation
- [ ] Health score algorithm refinement

### Phase 4: Data Engineering (✅ Complete)
- [x] Parquet export with PyArrow
- [x] JSONL export for training
- [x] Binary vector export

### Phase 5: Dashboard (📅 Planned)
- [ ] Next.js 15 setup
- [ ] Direct SQLite access (better-sqlite3)
- [ ] Force-directed dependency graph (D3.js)
- [ ] Semantic search UI
- [ ] Activity heatmap

### Phase 6: Deployment (📅 Planned)
- [ ] Docker multi-stage build
- [ ] GitHub Actions CI/CD
- [ ] Automated nightly ingestion
- [ ] Documentation site

---

## Performance

**Benchmark Results (Local SQLite):**
- Server ingestion (GitHub): ~2-5 seconds per repository
- Query latency (indexed): <10ms for most queries
- Export speed (Parquet): ~1000 servers/second
- Vector search (1536-dim): ~50ms for 10,000 vectors

**Optimization Tips:**
- Enable WAL mode: `PRAGMA journal_mode = WAL;`
- Use indexes on foreign keys
- Batch inserts with transactions
- Pre-load relationships with `selectinload()`

---

## Troubleshooting

### Common Issues

**Problem:** `GITHUB_TOKEN` not found
```bash
# Solution: Add token to .env file
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

**Problem:** Database locked errors
```bash
# Solution: Ensure WAL mode is enabled
sqlite3 data/mcps.db "PRAGMA journal_mode=WAL;"
```

**Problem:** Import errors
```bash
# Solution: Reinstall dependencies
uv sync --reinstall
```

**Problem:** Tests failing
```bash
# Solution: Reset test database
rm -f data/test.db
uv run alembic upgrade head
```

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Anthropic** - For creating the Model Context Protocol
- **SQLModel** - For elegant ORM with Pydantic integration
- **Ruff** - For blazing-fast Python linting
- **uv** - For fast, reliable Python packaging

---

## Contact

- **Issues:** [GitHub Issues](https://github.com/your-org/mcps/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/mcps/discussions)
- **Maintainer:** Wyatt Walsh

---

**Built with ❤️ for the AI Agent ecosystem**
