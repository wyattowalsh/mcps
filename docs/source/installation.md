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
- **Docker & Docker Compose** - For containerized deployment
- **PostgreSQL 16+** - For production database (or use Docker)
- **Redis 7+** - For caching (or use Docker)

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

# PostgreSQL Database (Production)
DATABASE_URL=postgresql+asyncpg://mcps:mcps_password@localhost:5432/mcps
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=mcps
POSTGRES_PASSWORD=mcps_password
POSTGRES_DB=mcps

# Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# SQLite (Development - optional)
USE_SQLITE=false
DATABASE_PATH=data/mcps.db
DATABASE_ECHO=false

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

```{note}
Without a GitHub token, the API is limited to 60 requests/hour. With a token: 5,000 requests/hour.
```

```{tip}
For production deployments, use PostgreSQL instead of SQLite. Set `USE_SQLITE=false` and configure PostgreSQL connection settings. See [PostgreSQL Migration Guide](guides/postgresql-migration.md) for details.
```

#### Getting a GitHub Token

1. Go to [GitHub Settings > Developer Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `public_repo` (read public repositories)
   - `read:packages` (read package metadata)
4. Copy the token and add it to your `.env` file

### 4. Initialize the Database

#### Option A: Docker Compose (Recommended)

The easiest way to set up PostgreSQL and Redis:

```bash
# Start database services
docker-compose up -d postgres redis

# Wait for services to be ready
docker-compose ps

# Migrations run automatically on API startup
docker-compose up -d mcps-api
```

#### Option B: Local PostgreSQL

If you have PostgreSQL installed locally:

```bash
# Install PostgreSQL (if not installed)
# macOS
brew install postgresql@16

# Ubuntu/Debian
sudo apt install postgresql-16

# Create database
createdb mcps

# Initialize extensions
psql mcps < scripts/init-postgres.sql

# Set DATABASE_URL in .env
export DATABASE_URL=postgresql+asyncpg://localhost/mcps

# Run migrations
uv run alembic upgrade head
```

#### Option C: SQLite (Development Only)

For local development without PostgreSQL:

```bash
# Set USE_SQLITE=true in .env
export USE_SQLITE=true
export DATABASE_PATH=data/mcps.db

# Run migrations
uv run alembic upgrade head
```

This will create the SQLite database at `data/mcps.db` with all necessary tables.

### 5. Set Up Redis (Optional but Recommended)

Redis is used for caching and performance optimization.

#### Using Docker

```bash
# Start Redis container
docker-compose up -d redis
```

#### Local Installation

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis
sudo systemctl start redis

# Verify Redis is running
redis-cli ping  # Should return PONG
```

### 6. Verify Installation

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

## Docker Compose Installation

The easiest way to get started with all services:

```bash
# 1. Clone repository
git clone https://github.com/wyattowalsh/mcps.git
cd mcps

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Check service health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/cache

# 5. View logs
docker-compose logs -f

# 6. Stop services
docker-compose down
```

This starts:
- PostgreSQL 16 on port 5432
- Redis 7 on port 6379
- MCPS API on port 8000
- MCPS Web UI on port 3000

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

### PostgreSQL Connection Errors

**Problem:** Can't connect to PostgreSQL

**Solutions:**

```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres
# OR
pg_isready -h localhost -U mcps

# 2. Check connection string in .env
echo $DATABASE_URL

# 3. Test connection manually
psql "postgresql://mcps:mcps_password@localhost:5432/mcps"

# 4. Check logs
docker-compose logs postgres
```

### Redis Connection Errors

**Problem:** Cache unavailable errors

**Solutions:**

```bash
# 1. Check Redis is running
docker-compose ps redis
# OR
redis-cli ping

# 2. Disable cache if not needed
export CACHE_ENABLED=false

# 3. Check logs
docker-compose logs redis
```

## Next Steps

Now that you have MCPS installed, check out:

- [Quick Start](quick-start.md) - Get started with basic usage
- [Quick Start PostgreSQL](quick-start-postgresql.md) - PostgreSQL-specific quickstart
- [PostgreSQL Migration](guides/postgresql-migration.md) - Detailed PostgreSQL guide
- [Caching Guide](guides/caching.md) - Redis caching documentation
- [CLI Usage](user-guide/cli-usage.md) - Learn CLI commands
- [Contributing](contributing.md) - Contribute to the project

```{seealso}
**Having issues?** Check our [GitHub Issues](https://github.com/wyattowalsh/mcps/issues) or [Discussions](https://github.com/wyattowalsh/mcps/discussions)
```
