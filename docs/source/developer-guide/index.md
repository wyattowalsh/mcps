---
title: Developer Guide
description: Comprehensive development guide for MCPS contributors
---

# Developer Guide

Welcome to the MCPS developer guide. This guide covers everything you need to know to contribute to MCPS.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+ (for frontend development)
- PostgreSQL 16+ (or Docker)
- Redis 7+ (or Docker)
- Git

### Development Setup

```bash
# Clone repository
git clone https://github.com/wyattowalsh/mcps.git
cd mcps

# Install dependencies
uv sync

# Set up environment
cp .env.example .env

# Start database services
docker-compose up -d postgres redis

# Run migrations
uv run alembic upgrade head

# Start API in development mode
uvicorn apps.api.main:app --reload

# Start frontend (in another terminal)
cd apps/web
pnpm dev
```

## Development Guides

### Backend Development

- **[Adding Adapters](adding-adapters.md)** - Create new data source adapters
- **[Testing Guide](testing.md)** - Write and run tests
- **Database Migrations** - Create and apply schema changes

### Frontend Development

- **[Frontend Development](frontend-development.md)** - Next.js development guide
- **Component Library** - shadcn/ui components
- **Testing** - Vitest and Playwright

### Architecture & Design

- **[Architecture](../architecture.md)** - System architecture overview
- **[Data Dictionary](../data-dictionary.md)** - Database schema reference
- **[API Documentation](../api/index.md)** - API reference

### Operations

- **[PostgreSQL Migration](../guides/postgresql-migration.md)** - Database migration guide
- **[Caching](../guides/caching.md)** - Redis caching implementation
- **[Monitoring](../guides/monitoring.md)** - Observability and metrics
- **[Production Deployment](../guides/production-deployment.md)** - Deploy to production

## Development Workflow

### 1. Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .

# Type checking
uv run mypy packages/
```

### 2. Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific test file
uv run pytest tests/test_github_harvester.py

# Run frontend tests
cd apps/web
pnpm test
pnpm test:e2e
```

### 3. Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Review generated migration
cat alembic/versions/[timestamp]_description.py

# Apply migration
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### 4. Running Services

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run individually
uvicorn apps.api.main:app --reload  # API
cd apps/web && pnpm dev             # Web UI
```

## Code Style Guidelines

### Python

- Follow PEP 8 with 100-character line length
- Use type hints for all functions
- Use async/await for I/O operations
- Write docstrings for public APIs

### TypeScript

- Use functional components with hooks
- Prefer named exports over default exports
- Use TypeScript strict mode
- Write JSDoc for complex functions

## Project Structure

```
mcps/
├── apps/
│   ├── api/              # FastAPI application
│   └── web/              # Next.js frontend
├── packages/
│   └── harvester/        # Core harvester package
│       ├── adapters/     # Data source adapters
│       ├── analysis/     # Analysis pipeline
│       ├── cache.py      # Redis caching
│       ├── database.py   # Database layer
│       ├── logging.py    # Structured logging
│       └── metrics.py    # Prometheus metrics
├── docs/                 # Documentation (Sphinx)
├── tests/                # Test files
├── alembic/              # Database migrations
└── docker-compose.yml    # Development services
```

## Common Tasks

### Adding a New Adapter

See [Adding Adapters](adding-adapters.md) for detailed instructions.

### Updating Dependencies

```bash
# Update Python dependencies
uv sync --upgrade

# Update frontend dependencies
cd apps/web
pnpm update
```

### Building Documentation

```bash
cd docs
make html
open build/html/index.html
```

## Debugging

### API Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DB_ECHO=true

# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn apps.api.main:app
```

### Database Debugging

```bash
# Check connection
psql "postgresql://mcps:mcps_password@localhost:5432/mcps"

# View migrations
uv run alembic history

# Check current version
uv run alembic current
```

### Cache Debugging

```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# View all keys
KEYS *

# Get key value
GET key_name

# Clear all cache
FLUSHDB
```

## Contributing

See [Contributing Guide](../contributing.md) for:
- Code review process
- Pull request guidelines
- Commit message conventions
- Release process

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Reinstall dependencies
rm -rf .venv
uv sync
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres
docker-compose logs postgres
```

**Frontend build errors:**
```bash
# Clear Next.js cache
cd apps/web
rm -rf .next
pnpm build
```

## See Also

- [Installation](../installation.md) - Setup guide
- [Quick Start](../quick-start.md) - Get started quickly
- [Contributing](../contributing.md) - Contribution guidelines
- [API Reference](../api/index.md) - API documentation
