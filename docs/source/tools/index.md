---
title: Tools Overview
description: Reference for all MCPS CLI tools and utilities
---

# Tools Overview

Reference documentation for all MCPS command-line tools and utilities.

## CLI Commands

### harvester.cli

Main CLI interface for MCPS operations.

```bash
uv run python -m packages.harvester.cli --help
```

**Available Commands:**

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ingest
Harvest MCP servers from various sources

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target URL
```
:::

:::{grid-item-card} export
Export data in various formats

```bash
uv run python -m packages.harvester.cli export \
  --format parquet \
  --destination ./exports
```
:::

:::{grid-item-card} status
View harvesting statistics

```bash
uv run python -m packages.harvester.cli status
```
:::

:::{grid-item-card} analyze
Analyze security and health

```bash
uv run python -m packages.harvester.cli analyze \
  --server-id 123
```
:::

::::

## Makefile Commands

```bash
make install     # Install dependencies
make db-migrate  # Run database migrations
make db-reset    # Reset database (WARNING: deletes data)
make lint        # Run code quality checks
make test        # Run test suite
make dev         # Start development servers
```

## Utility Scripts

### Database Management

```bash
# Check database size
sqlite3 data/mcps.db "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"

# Vacuum database
sqlite3 data/mcps.db "VACUUM;"

# Enable WAL mode
sqlite3 data/mcps.db "PRAGMA journal_mode=WAL;"
```

### Data Export Scripts

```python
# scripts/export_to_csv.py
from packages.harvester.database import get_engine
from sqlmodel import Session, select
from packages.harvester.models.models import Server
import pandas as pd

engine = get_engine()
with Session(engine) as session:
    servers = session.exec(select(Server)).all()
    df = pd.DataFrame([s.model_dump() for s in servers])
    df.to_csv('servers.csv', index=False)
```

## Development Tools

### Testing

```bash
pytest tests/                              # All tests
pytest tests/test_github_harvester.py      # Specific file
pytest --cov=packages --cov-report=html    # With coverage
pytest -v --tb=short                       # Verbose with short traceback
```

### Linting

```bash
ruff check .                               # Check all files
ruff check --fix .                         # Auto-fix issues
ruff format .                              # Format code
mypy packages/                             # Type checking
```

## See Also

- [CLI Usage](../user-guide/cli-usage.md)
- [Quick Start](../quick-start.md)
- [Contributing](../contributing.md)
