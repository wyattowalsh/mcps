---
title: MCPS - Model Context Protocol System
description: The definitive intelligence hub for the MCP ecosystem
version: 2.5.0
status: Active Development
---

# MCPS - Model Context Protocol System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Version:** 2.5.0 | **Status:** Active Development

---

## Overview

The definitive intelligence hub for the MCP ecosystem. Aggregates, indexes, analyzes, and visualizes Model Context Protocol servers from any source.

MCPS is the "NPM for the AI Agent era" - a comprehensive knowledge graph that treats the Model Context Protocol ecosystem as a heterogeneous, multi-source network. Unlike traditional package registries or GitHub-centric crawlers, MCPS performs **Universal Ingestion** from:

:::::{grid} 2
:gutter: 3

::::{grid-item-card} Available Sources
:class-header: bg-light

- {bdg-success}`✓` **GitHub repositories** (via GraphQL API)
- {bdg-success}`✓` **NPM packages** (via registry API + tarball inspection)
- {bdg-success}`✓` **PyPI packages** (via JSON API + wheel/sdist analysis)

::::

::::{grid-item-card} Coming Soon
:class-header: bg-light

- {bdg-warning}`⏳` **Docker containers** (via registry v2 + manifest inspection)
- {bdg-warning}`⏳` **HTTP/SSE endpoints** (via MCP introspection protocol)
- {bdg-warning}`⏳` **GitLab repositories** (future)

::::
:::::

## Key Features

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} {octicon}`search` Deep Metadata Extraction
:class-header: bg-primary text-white

Parses `mcp.json`, `package.json`, `pyproject.toml` to extract tools, resources, prompts, and dependencies
:::

:::{grid-item-card} {octicon}`shield-check` Security Analysis
:class-header: bg-success text-white

AST-based scanning for dangerous patterns (eval, subprocess, filesystem access)
:::

:::{grid-item-card} {octicon}`graph` Health Scoring
:class-header: bg-info text-white

Algorithmic calculation based on stars, activity, tests, and documentation
:::

:::{grid-item-card} {octicon}`brain` Semantic Search
:class-header: bg-warning

Vector embeddings (OpenAI text-embedding-3-small) for RAG workflows
:::

:::{grid-item-card} {octicon}`workflow` Dependency Graphs
:class-header: bg-danger text-white

Full dependency tree extraction for network analysis
:::

:::{grid-item-card} {octicon}`database` PostgreSQL-Powered
:class-header: bg-dark text-white

Production-ready database with connection pooling and pgvector
:::

::::

## Quick Start

### Installation

**Prerequisites:**

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)

```bash
# Clone the repository
git clone https://github.com/wyattowalsh/mcps.git
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

::::{tab-set}

:::{tab-item} GitHub
```bash
# Ingest a GitHub repository
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/modelcontextprotocol/servers
```
:::

:::{tab-item} NPM
```bash
# Ingest an NPM package
uv run python -m packages.harvester.cli ingest \
  --strategy npm \
  --target @modelcontextprotocol/server-filesystem
```
:::

:::{tab-item} PyPI
```bash
# Ingest a PyPI package
uv run python -m packages.harvester.cli ingest \
  --strategy pypi \
  --target mcp-server-git
```
:::

::::

### Exporting Data

```{tab-set}
```{tab-item} Parquet
Export to Parquet format (for data analysis):

```bash
uv run python -m packages.harvester.cli export \
  --format parquet \
  --destination ./data/exports
```
```

```{tab-item} JSONL
Export to JSONL format (for LLM fine-tuning):

```bash
uv run python -m packages.harvester.cli export \
  --format jsonl \
  --destination ./data/exports
```
```
```

### Checking Status

```bash
# View harvesting statistics
uv run python -m packages.harvester.cli status
```

## Architecture Overview

```{mermaid}
flowchart TB
    subgraph Sources["Data Sources"]
        GH[GitHub<br/>GraphQL API]
        NPM[NPM<br/>Registry]
        PYPI[PyPI<br/>JSON API]
        DOCKER[Docker<br/>Registry v2]
        SOCIAL[Social Media<br/>Reddit/Twitter/YouTube]
    end

    subgraph Harvester["Harvester Engine"]
        ADAPTER[Polymorphic<br/>Adapters]
    end

    subgraph Analysis["Analysis Pipeline"]
        AST[AST Security<br/>Analyzer]
        EMB[Embedding<br/>Generator]
        BUS[Bus Factor<br/>Calculator]
    end

    subgraph Cache["Caching Layer"]
        REDIS[(Redis<br/>Cache)]
    end

    subgraph Storage["Data Layer"]
        DB[(PostgreSQL<br/>+ pgvector)]
    end

    subgraph Export["Export Formats"]
        PARQUET[Parquet<br/>Files]
        JSONL[JSONL<br/>Training Data]
        VEC[Vector<br/>Binary]
    end

    subgraph Monitoring["Observability"]
        METRICS[Prometheus<br/>Metrics]
        LOGS[Structured<br/>Logging]
        SENTRY[Error<br/>Tracking]
    end

    GH --> ADAPTER
    NPM --> ADAPTER
    PYPI --> ADAPTER
    DOCKER --> ADAPTER
    SOCIAL --> ADAPTER

    ADAPTER --> REDIS
    REDIS --> AST
    REDIS --> EMB
    REDIS --> BUS

    AST --> DB
    EMB --> DB
    BUS --> DB

    DB --> PARQUET
    DB --> JSONL
    DB --> VEC

    DB --> METRICS
    ADAPTER --> LOGS
    DB --> SENTRY

    style Sources fill:#e1f5ff
    style Harvester fill:#fff3cd
    style Analysis fill:#d4edda
    style Cache fill:#ffe4b5
    style Storage fill:#f8d7da
    style Export fill:#e2e3e5
    style Monitoring fill:#e8f5e9
```

**Core Components:**

- **Harvester Engine:** Resilient ETL with retry logic (tenacity)
- **Adapter Layer:** Source-specific ingestion strategies
- **Analysis Pipeline:** Security scanning, embeddings, metrics
- **Caching Layer:** Redis-backed caching for performance
- **PostgreSQL Database:** Production-grade storage with vector search
- **Export Engine:** Analytical format conversion
- **Monitoring Stack:** Prometheus metrics, structured logging, error tracking

For detailed architecture documentation, see [Architecture](architecture.md).

## Documentation

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
quick-start
quick-start-postgresql
```

```{toctree}
:maxdepth: 2
:caption: User Guide

user-guide/index
user-guide/cli-usage
user-guide/dashboard
user-guide/data-exports
```

```{toctree}
:maxdepth: 2
:caption: Guides

guides/index
guides/harvesting
guides/analysis
guides/deployment
guides/production-deployment
guides/caching
guides/monitoring
guides/postgresql-migration
guides/postgresql-migration-plan
guides/postgresql-migration-summary
```

```{toctree}
:maxdepth: 2
:caption: Architecture & Design

architecture
data-dictionary
```

```{toctree}
:maxdepth: 2
:caption: Developer Guide

developer-guide/index
contributing
developer-guide/adding-adapters
developer-guide/testing
developer-guide/frontend-development
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
api/harvester
api/adapters
api/analysis
api/exporters
api/health-endpoints
```

```{toctree}
:maxdepth: 1
:caption: Additional Resources

changelog
tools/index
```

## Roadmap

::::{dropdown} Phase 1: Foundation {bdg-success}`✓ Complete`
:open:

- ✅ SQLite database with SQLModel
- ✅ Alembic migrations
- ✅ Base harvester abstract class
- ✅ GitHub adapter with GraphQL
- ✅ CLI interface with Typer

::::

::::{dropdown} Phase 2: Harvesting {bdg-warning}`⏳ In Progress`

- ✅ NPM adapter
- ✅ PyPI adapter
- ⏳ Docker adapter
- ⏳ HTTP/SSE adapter
- ⏳ Checkpoint system with retries

::::

::::{dropdown} Phase 3: Analysis {bdg-warning}`⏳ In Progress`

- ✅ AST-based security scanning
- ⏳ OpenAI embedding generation
- ⏳ Bus factor calculation
- ⏳ Health score algorithm refinement

::::

::::{dropdown} Phase 4: Data Engineering {bdg-success}`✓ Complete`

- ✅ Parquet export with PyArrow
- ✅ JSONL export for training
- ✅ Binary vector export

::::

::::{dropdown} Phase 5: Dashboard {bdg-info}`📅 Planned`

- ⏳ Next.js 15 setup
- ⏳ Direct SQLite access (better-sqlite3)
- ⏳ Force-directed dependency graph (D3.js)
- ⏳ Semantic search UI
- ⏳ Activity heatmap

::::

::::{dropdown} Phase 6: Deployment {bdg-info}`📅 Planned`

- ⏳ Docker multi-stage build
- ⏳ GitHub Actions CI/CD
- ⏳ Automated nightly ingestion
- ✅ Documentation site

::::

## License

This project is licensed under the **MIT License**.

## Acknowledgments

- **Anthropic** - For creating the Model Context Protocol
- **SQLModel** - For elegant ORM with Pydantic integration
- **Ruff** - For blazing-fast Python linting
- **uv** - For fast, reliable Python packaging

## Contact

- **Issues:** [GitHub Issues](https://github.com/wyattowalsh/mcps/issues)
- **Discussions:** [GitHub Discussions](https://github.com/wyattowalsh/mcps/discussions)
- **Maintainer:** Wyatt Walsh

---

**Built with ❤️ for the AI Agent ecosystem**

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
