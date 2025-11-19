# MCPS Makefile - Unified Command Center
# This Makefile provides a single interface for all development workflows

.PHONY: help install install-python install-web dev dev-api dev-web build lint lint-python lint-web test db-migrate db-reset db-upgrade clean export-data

# Default target: show help
help:
	@echo "MCPS - Model Context Protocol System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies (Python + Web)"
	@echo "  make dev            - Run development servers (API + Web in parallel)"
	@echo "  make build          - Build production assets"
	@echo "  make lint           - Run all linters (Python + Web)"
	@echo "  make test           - Run all tests"
	@echo "  make db-migrate     - Generate and apply database migration"
	@echo "  make db-reset       - Reset database (delete + recreate)"
	@echo "  make db-upgrade     - Apply pending migrations"
	@echo "  make export-data    - Export database to Parquet/JSONL"
	@echo "  make clean          - Clean build artifacts and caches"
	@echo ""

# Installation
install: install-python install-web
	@echo "✓ All dependencies installed"

install-python:
	@echo "Installing Python dependencies..."
	uv sync
	@echo "✓ Python dependencies installed"

install-web:
	@echo "Installing Web dependencies..."
	cd apps/web && pnpm install
	@echo "✓ Web dependencies installed"

# Development
dev:
	@echo "Starting development servers..."
	@$(MAKE) -j 2 dev-api dev-web

dev-api:
	@echo "Starting FastAPI server on :8000..."
	uv run uvicorn apps.api.main:app --reload --port 8000

dev-web:
	@echo "Starting Next.js development server on :3000..."
	cd apps/web && pnpm dev

# Build
build: build-web
	@echo "✓ Build complete"

build-web:
	@echo "Building Next.js production assets..."
	cd apps/web && pnpm build

# Linting
lint: lint-python lint-web
	@echo "✓ All linters passed"

lint-python:
	@echo "Running Ruff on Python code..."
	uv run ruff check packages/ apps/api/ --fix
	uv run ruff format packages/ apps/api/

lint-web:
	@echo "Running ESLint on Web code..."
	cd apps/web && pnpm lint

# Testing
test: test-python
	@echo "✓ All tests passed"

test-python:
	@echo "Running pytest..."
	uv run pytest tests/ -v --cov=packages

# Database operations
db-migrate:
	@echo "Generating database migration..."
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"
	@echo "Applying migration..."
	uv run alembic upgrade head
	@echo "✓ Migration complete"

db-reset:
	@echo "Resetting database..."
	rm -f data/*.db data/*.db-wal data/*.db-shm data/*.db-journal
	@echo "Running migrations..."
	uv run alembic upgrade head
	@echo "✓ Database reset complete"

db-upgrade:
	@echo "Applying database migrations..."
	uv run alembic upgrade head
	@echo "✓ Migrations applied"

# Data export
export-data:
	@echo "Exporting database to analytical formats..."
	mkdir -p data/exports
	uv run python -m packages.harvester.cli export --format parquet --destination ./data/exports
	@echo "✓ Data exported to data/exports/"

# Harvesting (ETL operations)
ingest-all:
	@echo "Running universal harvester..."
	uv run python -m packages.harvester.cli ingest --strategy auto --target all

ingest-github:
	@echo "Running GitHub harvester..."
	uv run python -m packages.harvester.cli ingest --strategy github

ingest-npm:
	@echo "Running NPM harvester..."
	uv run python -m packages.harvester.cli ingest --strategy npm

ingest-docker:
	@echo "Running Docker harvester..."
	uv run python -m packages.harvester.cli ingest --strategy docker

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf data/*.db data/*.db-wal data/*.db-shm data/*.db-journal
	rm -rf apps/web/.next apps/web/out
	rm -rf apps/web/node_modules/.cache
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf packages/**/__pycache__ apps/**/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup complete"

# Type checking
typecheck:
	@echo "Running mypy..."
	uv run mypy packages/ apps/api/ --strict

# Quick start for new developers
quickstart: install db-upgrade
	@echo ""
	@echo "✓ MCPS is ready!"
	@echo ""
	@echo "To start developing:"
	@echo "  make dev       - Start development servers"
	@echo "  make lint      - Run linters before committing"
	@echo "  make test      - Run test suite"
	@echo ""
