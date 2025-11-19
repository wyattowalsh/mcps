---
title: Installation
description: Complete guide to installing and setting up MCPS
---

# Installation

This guide will help you install and set up MCPS on your system.

## Prerequisites

Before installing MCPS, ensure you have the following:

### Required

::::{grid} 2
:gutter: 3

:::{grid-item-card} Python 3.12+
Check with `python --version`
:::

:::{grid-item-card} uv
Fast Python package installer ([Installation guide](https://github.com/astral-sh/uv))
:::

:::{grid-item-card} Git
For cloning the repository
:::

:::{grid-item-card} SQLite 3.35+
Usually included with Python
:::

::::

### Optional

- **GitHub CLI (gh)** - For managing pull requests
- **make** - For using Makefile commands
- **Node.js 20+** - If working on the web dashboard

## Installing uv

The fastest way to install uv:

::::{tab-set}

:::{tab-item} macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
:::

:::{tab-item} Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```
:::

:::{tab-item} pip
```bash
pip install uv
```
:::

::::

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/wyattowalsh/mcps.git
cd mcps
```

### 2. Install Dependencies

::::{tab-set}

:::{tab-item} Using uv (Recommended)
```bash
# Install all dependencies
uv sync

# Or use the Makefile
make install
```

This will:
- Create a virtual environment in `.venv/`
- Install all Python dependencies
- Set up development tools (ruff, mypy, pytest)
:::

:::{tab-item} Manual Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt  # If you have this file
```
:::

::::

### 3. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit the `.env` file and add your configuration:

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

```{note}
Without a GitHub token, the API is limited to 60 requests/hour. With a token: 5,000 requests/hour.
```

#### Getting a GitHub Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `public_repo` (read public repositories)
   - `read:packages` (read package metadata)
4. Copy the token and add it to your `.env` file

### 4. Initialize the Database

Run database migrations to create the schema:

```bash
# Using Makefile
make db-migrate

# Or manually
uv run alembic upgrade head
```

This will create the SQLite database at `data/mcps.db` with all necessary tables.

### 5. Verify Installation

Run the test suite to ensure everything is working:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=packages --cov-report=html

# Check code formatting
uv run ruff check .
```

```{tip}
If all tests pass, your installation is successful!
```

## Installing Documentation Dependencies

To build the documentation locally:

```bash
# Install docs dependencies
uv sync --group docs

# Build documentation
cd docs
make html

# Open in browser
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows
```

## Troubleshooting

### GITHUB_TOKEN not found

**Problem:** Getting errors about missing GitHub token

**Solution:**

```bash
# Add token to .env file
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env
```

### Database locked errors

**Problem:** Getting "database is locked" errors

**Solution:**

```bash
# Ensure WAL mode is enabled
sqlite3 data/mcps.db "PRAGMA journal_mode=WAL;"
```

### Import errors

**Problem:** Getting import errors when running commands

**Solution:**

```bash
# Reinstall dependencies
uv sync --reinstall

# Or clear cache
rm -rf .venv
uv sync
```

### Tests failing

**Problem:** Tests are failing after installation

**Solution:**

```bash
# Reset test database
rm -f data/test.db
uv run alembic upgrade head

# Run tests again
uv run pytest
```

### Python version mismatch

**Problem:** Getting Python version errors

**Solution:**

```bash
# Check Python version
python --version

# Should be 3.12 or higher
# If not, install Python 3.12+

# Use pyenv for version management
pyenv install 3.12
pyenv local 3.12
```

## Next Steps

Now that you have MCPS installed, check out:

- [Quick Start](quick-start.md) - Get started with basic usage
- [CLI Usage](user-guide/cli-usage.md) - Learn CLI commands
- [Contributing](contributing.md) - Contribute to the project

```{seealso}
**Having issues?** Check our [GitHub Issues](https://github.com/wyattowalsh/mcps/issues) or [Discussions](https://github.com/wyattowalsh/mcps/discussions)
```
