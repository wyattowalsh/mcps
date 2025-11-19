---
title: Quick Start
description: Get started with MCPS by walking through common tasks
---

# Quick Start

This guide will help you get started with MCPS by walking through common tasks.

```{tip}
For PostgreSQL-specific quick start, see [Quick Start PostgreSQL](quick-start-postgresql.md)
```

## Your First Harvest

Let's start by harvesting an MCP server from GitHub.

### 1. Ingest a GitHub Repository

The official MCP servers repository is a good starting point:

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/modelcontextprotocol/servers
```

You should see output like:

```text
2025-11-19 10:30:00 | INFO | Harvesting GitHub repository: modelcontextprotocol/servers
2025-11-19 10:30:02 | INFO | Found 12 tools, 5 resources, 2 prompts
2025-11-19 10:30:03 | INFO | Security analysis: SAFE (no dangerous patterns detected)
2025-11-19 10:30:03 | INFO | Health score: 95/100
2025-11-19 10:30:04 | SUCCESS | Server indexed successfully
```

### 2. View Harvesting Statistics

Check what's been indexed:

```bash
uv run python -m packages.harvester.cli status
```

Output:

```text
=== MCPS Harvester Status ===

Total Servers Indexed: 1

Processing Queue:
  Pending: 0
  Processing: 0
  Completed: 1
  Failed: 0
  Skipped: 0

Recent Servers:
  1. servers (github) - Health: 95/100 - Stars: 1250
```

## Harvesting from Different Sources

::::{tab-set}

:::{tab-item} NPM Packages
Harvest an NPM package that provides MCP servers:

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy npm \
  --target @modelcontextprotocol/server-filesystem
```
:::

:::{tab-item} PyPI Packages
Harvest a Python package:

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy pypi \
  --target mcp-server-git
```
:::

:::{tab-item} Auto-Detection
Let MCPS automatically detect the source type:

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy auto \
  --target https://github.com/anthropics/anthropic-sdk-python
```
:::

::::

## Exporting Data

Once you've harvested some servers, export the data for analysis.

### Export to Parquet

Parquet format is optimized for analytical queries:

```bash
uv run python -m packages.harvester.cli export \
  --format parquet \
  --destination ./data/exports
```

This creates:

- `servers.parquet` - Server metadata with analytics columns
- `dependencies.parquet` - Dependency edge list for graph analysis

#### Using the Parquet exports with pandas

```python
import pandas as pd

# Load servers
servers = pd.read_parquet('data/exports/servers.parquet')

# Filter by risk level
high_risk = servers[servers['risk_level'] == 'high']

# Top servers by health score
top_servers = servers.nlargest(10, 'health_score')

print(top_servers[['name', 'stars', 'health_score', 'risk_level']])
```

### Export to JSONL

JSONL format is formatted for LLM fine-tuning:

```bash
uv run python -m packages.harvester.cli export \
  --format jsonl \
  --destination ./data/exports
```

This creates:

- `tools.jsonl` - Tool definitions in training format
- `vectors.json` - Vector metadata
- `vectors.bin` - Binary embedding dump

#### Using the JSONL exports

```python
import json

# Load training data
with open('data/exports/tools.jsonl', 'r') as f:
    for line in f:
        example = json.loads(line)
        # Each example has 'messages' array for fine-tuning
        print(example['messages'])
```

## Working with the Database

### Query the Database

#### Using PostgreSQL (Recommended)

```bash
# Using psql CLI
psql "postgresql://mcps:mcps_password@localhost:5432/mcps"
```

```sql
-- List all servers
SELECT name, stars, health_score, risk_level FROM server ORDER BY stars DESC LIMIT 10;

-- List all tools for a server
SELECT t.name, t.description
FROM tool t
JOIN server s ON t.server_id = s.id
WHERE s.name = 'servers';

-- Count servers by host type
SELECT host_type, COUNT(*) as count FROM server GROUP BY host_type;
```

#### Using SQLite (Development)

If using SQLite instead:

```bash
# Using sqlite3 CLI
sqlite3 data/mcps.db
```

### Using Python with SQLModel

```python
from sqlmodel import Session, select
from packages.harvester.database import get_engine
from packages.harvester.models.models import Server, Tool

# Create database session
engine = get_engine()
session = Session(engine)

# Query all servers
statement = select(Server).where(Server.stars > 100)
servers = session.exec(statement).all()

for server in servers:
    print(f"{server.name}: {server.stars} stars, Health: {server.health_score}")

# Query tools for a specific server
server = session.exec(select(Server).where(Server.name == "servers")).first()
if server:
    print(f"\nTools for {server.name}:")
    for tool in server.tools:
        print(f"  - {tool.name}: {tool.description}")
```

## Common Workflows

### Workflow 1: Discovery

Discover and index all official MCP servers:

```bash
# Index the main servers repository
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/modelcontextprotocol/servers

# Check status
uv run python -m packages.harvester.cli status

# Export for analysis
uv run python -m packages.harvester.cli export \
  --format parquet \
  --destination ./data/exports
```

### Workflow 2: Security Audit

Find servers with high-risk patterns:

```bash
# Harvest multiple servers
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/user/suspicious-server

# Query database for high-risk servers
sqlite3 data/mcps.db "SELECT name, risk_level, stars FROM server WHERE risk_level IN ('high', 'critical');"
```

### Workflow 3: Dependency Analysis

Analyze dependency networks:

```python
import pandas as pd
import networkx as nx

# Load dependencies
deps = pd.read_parquet('data/exports/dependencies.parquet')

# Create graph
G = nx.from_pandas_edgelist(
    deps,
    source='server_name',
    target='library_name',
    edge_attr='type'
)

# Find most popular libraries
popular_libs = sorted(
    [(node, G.degree(node)) for node in G.nodes()],
    key=lambda x: x[1],
    reverse=True
)[:10]

print("Most popular dependencies:")
for lib, count in popular_libs:
    print(f"  {lib}: used by {count} servers")
```

## Development Commands

If you're developing MCPS, use these commands:

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=packages --cov-report=html

# Specific test file
uv run pytest tests/test_github_harvester.py

# Verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Type checking
uv run mypy packages/
```

### Database Management

```bash
# Create migration
uv run alembic revision --autogenerate -m "Add new field"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Reset database (WARNING: deletes all data)
make db-reset
```

### Using Make Commands

```bash
# Install dependencies
make install

# Run database migrations
make db-migrate

# Reset database
make db-reset

# Run linting
make lint

# Run tests
make test

# Start development servers (API + Web)
make dev
```

### Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/cache

# Stop services
docker-compose down

# Reset everything
docker-compose down -v
docker-compose up -d
```

## Next Steps

Now that you're familiar with the basics:

:::::{grid} 2
:gutter: 3

::::{grid-item-card} {octicon}`terminal` CLI Usage
:link: user-guide/cli-usage
:link-type: doc

Detailed CLI reference
::::

::::{grid-item-card} {octicon}`download` Data Exports
:link: user-guide/data-exports
:link-type: doc

Advanced export options
::::

::::{grid-item-card} {octicon}`workflow` Architecture
:link: architecture
:link-type: doc

Understand the system design
::::

::::{grid-item-card} {octicon}`heart` Contributing
:link: contributing
:link-type: doc

Contribute to the project
::::

:::::
