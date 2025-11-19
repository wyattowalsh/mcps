#!/usr/bin/env python3
"""
Batch convert remaining RST files to MyST markdown format.
This script handles the conversion of all subdirectory RST files.
"""

from pathlib import Path
import re

# Define conversions for all remaining files
CONVERSIONS = {
    "data-dictionary.md": """---
title: Data Dictionary
description: Comprehensive reference for all database schemas and data formats
version: 2.5.0
last_updated: 2025-11-19
---

# Data Dictionary

Comprehensive reference for all database schemas, data formats, and relationships in the Model Context Protocol System.

**Database:** SQLite 3 with WAL mode + sqlite-vec extension

## Overview

The MCPS database uses SQLite as its primary data store, leveraging the following key features:

- **ACID Compliance:** Full transactional support with WAL (Write-Ahead Logging) mode
- **Vector Search:** sqlite-vec extension for semantic similarity queries
- **JSON Support:** Native JSON columns for flexible schema storage
- **Foreign Keys:** Enforced referential integrity across all relationships
- **Cascading Deletes:** Automatic cleanup of related entities

**Connection String:**

```text
sqlite+aiosqlite:///data/mcps.db
```

**Key Settings:**

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
```

## Database Tables

### Core Entities

#### server

The canonical representation of an MCP server from any source.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `uuid` | TEXT | UNIQUE, NOT NULL, INDEXED | UUID v4 identifier |
| `name` | TEXT | NOT NULL, INDEXED | Server display name |
| `primary_url` | TEXT | UNIQUE, NOT NULL, INDEXED | Canonical identifier |
| `host_type` | TEXT | NOT NULL, INDEXED | Source platform (see HostType enum) |
| `description` | TEXT | NULLABLE | Human-readable description |
| `stars` | INTEGER | DEFAULT 0, INDEXED | GitHub stars or popularity metric |
| `health_score` | INTEGER | DEFAULT 0 | Calculated 0-100 health metric |
| `risk_level` | TEXT | DEFAULT 'unknown' | Security risk assessment |
| `last_indexed_at` | TIMESTAMP | NOT NULL | Last successful indexing |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**

- `idx_server_uuid` on `uuid`
- `idx_server_name` on `name`
- `idx_server_primary_url` on `primary_url`
- `idx_server_host_type` on `host_type`
- `idx_server_stars` on `stars` (for ranking)

### Functional Entities

#### tool

Individual tools exposed by MCP servers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `server_id` | INTEGER | FOREIGN KEY → server.id, NOT NULL | Parent server reference |
| `name` | TEXT | NOT NULL | Tool name (unique within server) |
| `description` | TEXT | NULLABLE | Human-readable tool description |
| `input_schema` | JSON | DEFAULT {} | JSON Schema for tool arguments |
| `created_at` | TIMESTAMP | NOT NULL | Record creation timestamp |

#### toolembedding

Vector embeddings for semantic search across tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Internal database ID |
| `tool_id` | INTEGER | FOREIGN KEY → tool.id, UNIQUE, NOT NULL | Parent tool reference |
| `vector` | JSON | NOT NULL | 1536-dimensional embedding (stored as JSON array) |
| `model_name` | TEXT | DEFAULT 'text-embedding-3-small' | OpenAI embedding model used |

```{note}
Vectors are stored as JSON for portability but converted to binary format for sqlite-vec operations.
```

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

## See Also

- [Architecture](architecture.md) - System architecture and design
- [API Reference](api/harvester.md) - Harvester API reference
""",

    "contributing.md": """---
title: Contributing to MCPS
description: Guidelines for contributing to the Model Context Protocol System
---

# Contributing to MCPS

Thank you for your interest in contributing to the Model Context Protocol System! This guide will help you get started with development, testing, and submitting contributions.

**Project:** Model Context Protocol System (MCPS)

**Repository:** https://github.com/wyattowalsh/mcps

**License:** MIT

## Getting Started

### Prerequisites

:::::{grid} 2
:gutter: 3

::::{grid-item-card} Required
- **Python 3.12+** - Check with `python --version`
- **uv** - Fast Python package installer
- **Git** - Version control
- **SQLite 3.35+** - Should be included with Python
::::

::::{grid-item-card} Optional
- **GitHub CLI (gh)** - For managing PRs
- **make** - For using Makefile commands
- **Node.js 20+** - If working on the web dashboard
::::

:::::

### Development Environment Setup

```bash
# Clone the repository
git clone https://github.com/wyattowalsh/mcps.git
cd mcps

# Install all dependencies including dev tools
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your credentials

# Initialize the database
make db-migrate

# Verify installation
uv run pytest
```

## Development Workflow

### Creating a Branch

Always create a new branch for your work:

```bash
# Feature branch
git checkout -b feature/add-gitlab-adapter

# Bug fix branch
git checkout -b fix/github-rate-limit

# Documentation branch
git checkout -b docs/update-contributing-guide
```

**Branch naming conventions:**

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific test file
uv run pytest tests/test_github_harvester.py

# Run with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with Ruff
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Auto-fix linting issues (when possible)
uv run ruff check --fix .

# Type checking with MyPy
uv run mypy packages/

# All checks via Makefile
make lint
```

## Adding New Features

### Adding a New Registry Adapter

Follow the **Polymorphic Strategy Pattern** to add support for new package registries or hosting platforms.

Example: Adding a GitLab Adapter

```python
# packages/harvester/adapters/gitlab.py

from typing import Any, Dict
from sqlmodel.ext.asyncio.session import AsyncSession
from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models.models import Server

class GitLabHarvester(BaseHarvester):
    """GitLab-specific harvester using REST API."""

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch repository data from GitLab API."""
        # Implementation here
        pass

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse GitLab response into Server model."""
        # Implementation here
        pass
```

All adapters must implement:

- `fetch(url: str) -> Dict[str, Any]` - Retrieve raw data from source
- `parse(data: Dict[str, Any]) -> Server` - Transform data into Server model
- `store(server: Server, session: AsyncSession) -> None` - Persist to database

## Code Style Guidelines

### Python Style (Ruff + MyPy)

We use **Ruff** for linting and formatting, and **MyPy** for type checking.

**Key Rules:**

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} Use pathlib
```python
# Good
from pathlib import Path
file_path = Path("data/mcps.db")

# Bad
import os
file_path = os.path.join("data", "mcps.db")
```
:::

:::{grid-item-card} Use type hints
```python
# Good
def fetch_server(url: str) -> Server:
    ...

# Bad
def fetch_server(url):
    ...
```
:::

:::{grid-item-card} Prefer async/await
```python
# Good
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```
:::

::::

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Modules | snake_case | `github_harvester.py` |
| Classes | PascalCase | `GitHubHarvester` |
| Functions | snake_case | `parse_github_url()` |
| Constants | UPPER_SNAKE | `GRAPHQL_QUERY` |
| Private | _leading_underscore | `_parse_json()` |

### Documentation Standards

Use Google-style docstrings for all public functions and classes:

```python
def calculate_health_score(
    stars: int,
    forks: int,
    has_readme: bool,
) -> int:
    \"\"\"Calculate health score from 0-100 based on various metrics.

    Args:
        stars: Number of GitHub stars
        forks: Number of forks
        has_readme: Whether README exists

    Returns:
        Health score from 0-100

    Raises:
        ValueError: If stars or forks are negative

    Example:
        >>> calculate_health_score(100, 20, True)
        85
    \"\"\"
```

## Testing Guidelines

### Unit Tests

Write unit tests for all new functions and classes.

```python
import pytest
from unittest.mock import AsyncMock
from packages.harvester.adapters.github import GitHubHarvester

@pytest.fixture
def mock_session():
    \"\"\"Create mock database session.\"\"\"
    return AsyncMock()

@pytest.mark.asyncio
async def test_github_harvester_parse(mock_session, mock_github_response):
    \"\"\"Test parsing GitHub API response.\"\"\"
    harvester = GitHubHarvester(mock_session)
    server = await harvester.parse(mock_github_response)

    assert server.name == "test-server"
    assert server.stars == 100
```

### Test Coverage

Aim for **80%+ code coverage** for new code:

```bash
# Generate coverage report
uv run pytest --cov=packages --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Coverage Requirements:**

- Core logic (adapters, parsers): 90%+
- Utilities: 80%+
- CLI commands: 60%+

## Submitting Changes

### Pull Request Process

1. Ensure all checks pass:

```bash
# Run full test suite
uv run pytest

# Check code quality
make lint

# Verify types
uv run mypy packages/
```

2. Update documentation:
   - Add docstrings to new functions
   - Update README.md if adding features
   - Update docs/ if changing architecture

3. Create pull request:

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR using GitHub CLI
gh pr create --title "Add GitLab adapter" --body "Implements GitLab harvesting support"
```

### Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

**Example:**

```bash
feat(adapters): add GitLab harvester with GraphQL support

Implements full GitLab repository harvesting including:
- GraphQL query optimization
- Dependency parsing
- Contributor extraction

Closes #123
```

### Code Review Process

1. **Automated checks run on PR creation:**
   - Ruff linting
   - MyPy type checking
   - Pytest test suite
   - Coverage report

2. **Merging:**
   - Requires 1 approval
   - All checks must pass
   - Squash and merge preferred

## License

By contributing to MCPS, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to MCPS!**

For questions about contributing, open a GitHub Discussion or reach out to the maintainers.
""",
}

# Write the files
source_dir = Path("/home/user/mcps/docs/source")

for filename, content in CONVERSIONS.items():
    filepath = source_dir / filename
    filepath.write_text(content)
    print(f"Created: {filepath}")

print(f"\nConverted {len(CONVERSIONS)} files successfully!")
