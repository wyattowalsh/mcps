# MCPS Makefile - Unified Command Center
# This Makefile provides a single interface for all development workflows

.PHONY: help install install-python install-web dev dev-api dev-web dev-all build lint lint-python lint-web test \
	db-migrate db-reset db-upgrade db-seed db-backup db-restore db-psql db-health \
	docker-up docker-down docker-restart docker-logs docker-clean docker-build \
	redis-cli redis-flush cache-clear \
	metrics health logs \
	social-harvest social-reddit social-twitter social-youtube \
	clean clean-all export-data quickstart

# Default target: show help
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         MCPS - Model Context Protocol System v3.2.0            ║"
	@echo "║              Production-Ready with PostgreSQL + Redis          ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  make install         - Install all dependencies (Python + Web)"
	@echo "  make quickstart      - Quick setup for new developers"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev             - Run API + Web dev servers in parallel"
	@echo "  make dev-all         - Run all services (PostgreSQL + Redis + API + Web)"
	@echo "  make dev-api         - Run FastAPI server only"
	@echo "  make dev-web         - Run Next.js server only"
	@echo ""
	@echo "🐳 Docker Services:"
	@echo "  make docker-up       - Start PostgreSQL + Redis containers"
	@echo "  make docker-down     - Stop all Docker containers"
	@echo "  make docker-restart  - Restart all Docker containers"
	@echo "  make docker-logs     - View Docker container logs"
	@echo "  make docker-clean    - Stop containers and remove volumes"
	@echo "  make docker-build    - Rebuild Docker images"
	@echo ""
	@echo "🗄️  Database Operations:"
	@echo "  make db-migrate      - Generate and apply migration"
	@echo "  make db-upgrade      - Apply pending migrations"
	@echo "  make db-reset        - Reset database (PostgreSQL)"
	@echo "  make db-seed         - Seed database with sample data"
	@echo "  make db-backup       - Backup PostgreSQL database"
	@echo "  make db-restore      - Restore PostgreSQL database"
	@echo "  make db-psql         - Open PostgreSQL shell"
	@echo "  make db-health       - Check database health"
	@echo ""
	@echo "📊 Social Media Harvesting:"
	@echo "  make social-harvest  - Harvest from all platforms"
	@echo "  make social-reddit   - Harvest Reddit only"
	@echo "  make social-twitter  - Harvest Twitter/X only"
	@echo "  make social-youtube  - Harvest YouTube only"
	@echo ""
	@echo "☁️  Supabase Integration:"
	@echo "  make supabase-status - Check Supabase configuration"
	@echo "  make supabase-setup  - Run Supabase setup script"
	@echo "  make supabase-test   - Test Supabase storage"
	@echo ""
	@echo "🔍 Monitoring & Health:"
	@echo "  make health          - Check all service health"
	@echo "  make metrics         - View Prometheus metrics"
	@echo "  make logs            - Tail application logs"
	@echo ""
	@echo "💾 Caching:"
	@echo "  make redis-cli       - Open Redis CLI"
	@echo "  make redis-flush     - Flush Redis cache"
	@echo "  make cache-clear     - Clear all caches (Redis + in-memory)"
	@echo ""
	@echo "🔨 Build & Test:"
	@echo "  make build           - Build production assets"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e        - Run E2E tests (Playwright)"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make lint            - Run all linters"
	@echo ""
	@echo "📤 Data Export:"
	@echo "  make export-data     - Export database to Parquet/JSONL"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean           - Clean build artifacts and caches"
	@echo "  make clean-all       - Deep clean (including Docker volumes)"
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
	@echo "🚀 Starting development servers (API + Web)..."
	@$(MAKE) -j 2 dev-api dev-web

dev-all:
	@echo "🚀 Starting all services (Docker + API + Web)..."
	@$(MAKE) docker-up
	@sleep 3
	@$(MAKE) dev

dev-api:
	@echo "🔥 Starting FastAPI server on :8000..."
	@echo "   📊 Metrics: http://localhost:8000/metrics"
	@echo "   ❤️  Health: http://localhost:8000/health"
	@echo "   📖 Docs: http://localhost:8000/docs"
	uv run uvicorn apps.api.main:app --reload --port 8000 --log-level info

dev-web:
	@echo "⚡ Starting Next.js development server on :3000..."
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
test: test-python test-web
	@echo "✓ All tests passed"

test-python:
	@echo "🧪 Running Python tests..."
	uv run pytest tests/ -v --cov=packages

test-web:
	@echo "🧪 Running Web tests..."
	cd apps/web && pnpm test

test-unit:
	@echo "🧪 Running unit tests..."
	uv run pytest tests/unit/ -v
	cd apps/web && pnpm test:unit

test-integration:
	@echo "🧪 Running integration tests..."
	uv run pytest tests/integration/ -v
	cd apps/web && pnpm test:integration

test-e2e:
	@echo "🧪 Running E2E tests..."
	cd apps/web && pnpm test:e2e

test-coverage:
	@echo "📊 Running tests with coverage..."
	uv run pytest tests/ -v --cov=packages --cov-report=html --cov-report=term
	cd apps/web && pnpm test:coverage
	@echo "✓ Coverage report generated:"
	@echo "   Python: htmlcov/index.html"
	@echo "   Web: apps/web/coverage/index.html"

# Docker Services
docker-up:
	@echo "🐳 Starting Docker services (PostgreSQL + Redis)..."
	docker-compose up -d postgres redis
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	@echo "✓ Services started"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis: localhost:6379"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✓ Services stopped"

docker-restart:
	@$(MAKE) docker-down
	@$(MAKE) docker-up

docker-logs:
	@echo "📋 Viewing Docker logs (Ctrl+C to exit)..."
	docker-compose logs -f postgres redis

docker-clean:
	@echo "🧹 Cleaning Docker containers and volumes..."
	@read -p "This will delete ALL data. Continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v; \
		echo "✓ Cleanup complete"; \
	else \
		echo "Cancelled"; \
	fi

docker-build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✓ Build complete"

# Database operations (PostgreSQL)
db-migrate:
	@echo "📝 Generating database migration..."
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"
	@echo "⬆️  Applying migration..."
	uv run alembic upgrade head
	@echo "✓ Migration complete"

db-reset:
	@echo "⚠️  Resetting PostgreSQL database..."
	@read -p "This will delete ALL data. Continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose exec postgres psql -U mcps -d postgres -c "DROP DATABASE IF EXISTS mcps;" || true; \
		docker-compose exec postgres psql -U mcps -d postgres -c "CREATE DATABASE mcps;"; \
		uv run alembic upgrade head; \
		echo "✓ Database reset complete"; \
	else \
		echo "Cancelled"; \
	fi

db-upgrade:
	@echo "⬆️  Applying database migrations..."
	uv run alembic upgrade head
	@echo "✓ Migrations applied"

db-seed:
	@echo "🌱 Seeding database with sample data..."
	uv run python -m packages.harvester.cli ingest --strategy auto --target all
	@echo "✓ Database seeded"

db-backup:
	@echo "💾 Backing up PostgreSQL database..."
	@mkdir -p data/backups
	@BACKUP_FILE="data/backups/mcps_$$(date +%Y%m%d_%H%M%S).sql"; \
	docker-compose exec -T postgres pg_dump -U mcps mcps > "$$BACKUP_FILE"; \
	echo "✓ Backup saved to $$BACKUP_FILE"

db-restore:
	@echo "📥 Restoring PostgreSQL database..."
	@read -p "Backup file path: " backup; \
	if [ -f "$$backup" ]; then \
		docker-compose exec -T postgres psql -U mcps -d mcps < "$$backup"; \
		echo "✓ Database restored"; \
	else \
		echo "Error: Backup file not found"; \
		exit 1; \
	fi

db-psql:
	@echo "🐘 Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U mcps -d mcps

db-health:
	@echo "❤️  Checking database health..."
	@curl -s http://localhost:8000/health/db | python -m json.tool || echo "API not running"

# Supabase Integration
supabase-status:
	@echo "☁️  Checking Supabase configuration..."
	uv run python -m packages.harvester.cli supabase-status

supabase-setup:
	@echo "⚙️  Running Supabase setup script..."
	@echo "Please run scripts/supabase-setup.sql in your Supabase SQL Editor"
	@echo "Dashboard: https://app.supabase.com"

supabase-test:
	@echo "🧪 Testing Supabase storage operations..."
	uv run python -m packages.harvester.cli supabase-test-storage

# Social Media Harvesting
social-harvest:
	@echo "📱 Harvesting from all social media platforms..."
	uv run python -m packages.harvester.cli harvest-social --platform all
	@echo "✓ Social harvest complete"

social-reddit:
	@echo "🔴 Harvesting Reddit..."
	uv run python -m packages.harvester.cli harvest-social --platform reddit
	@echo "✓ Reddit harvest complete"

social-twitter:
	@echo "🐦 Harvesting Twitter/X..."
	uv run python -m packages.harvester.cli harvest-social --platform twitter
	@echo "✓ Twitter harvest complete"

social-youtube:
	@echo "📹 Harvesting YouTube..."
	uv run python -m packages.harvester.cli harvest-social --platform youtube
	@echo "✓ YouTube harvest complete"

# Monitoring & Health
health:
	@echo "❤️  Checking service health..."
	@echo "\n🔍 API Health:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "  ❌ API not running"
	@echo "\n🗄️  Database Health:"
	@curl -s http://localhost:8000/health/db | python -m json.tool || echo "  ❌ Database check failed"
	@echo "\n💾 Cache Health:"
	@curl -s http://localhost:8000/health/cache | python -m json.tool || echo "  ❌ Cache check failed"
	@echo "\n✅ Readiness:"
	@curl -s http://localhost:8000/readiness | python -m json.tool || echo "  ❌ Not ready"

metrics:
	@echo "📊 Prometheus Metrics:"
	@curl -s http://localhost:8000/metrics || echo "API not running"

logs:
	@echo "📋 Tailing application logs (Ctrl+C to exit)..."
	@tail -f logs/*.log 2>/dev/null || echo "No log files found. Start the API to generate logs."

# Redis / Caching
redis-cli:
	@echo "💾 Opening Redis CLI..."
	docker-compose exec redis redis-cli

redis-flush:
	@echo "🧹 Flushing Redis cache..."
	@read -p "This will clear ALL cached data. Continue? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose exec redis redis-cli FLUSHALL; \
		echo "✓ Redis cache cleared"; \
	else \
		echo "Cancelled"; \
	fi

cache-clear:
	@$(MAKE) redis-flush
	@echo "✓ All caches cleared"

# Data export
export-data:
	@echo "📤 Exporting database to analytical formats..."
	mkdir -p data/exports
	uv run python -m packages.harvester.cli export --format parquet --destination ./data/exports
	@echo "✓ Data exported to data/exports/"

# Cleanup
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf apps/web/.next apps/web/out
	rm -rf apps/web/node_modules/.cache
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf packages/**/__pycache__ apps/**/__pycache__
	rm -rf htmlcov/ apps/web/coverage/
	rm -rf .coverage apps/web/.nyc_output/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleanup complete"

clean-all: clean docker-clean
	@echo "🧹 Deep cleaning everything..."
	rm -rf .venv/
	rm -rf apps/web/node_modules/
	rm -rf data/
	@echo "✓ Deep cleanup complete"

# Type checking
typecheck:
	@echo "🔍 Running type checks..."
	uv run mypy packages/ apps/api/ --strict
	cd apps/web && pnpm typecheck
	@echo "✓ Type checking passed"

# Production deployment
deploy:
	@echo "🚀 Deploying to production..."
	@echo "   Building web..."
	@$(MAKE) build
	@echo "   Running migrations..."
	@$(MAKE) db-upgrade
	@echo "   Clearing caches..."
	@$(MAKE) cache-clear
	@echo "✓ Deployment complete"

# Quick start for new developers
quickstart: install docker-up db-upgrade
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                     ✓ MCPS is ready!                           ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 To start developing:"
	@echo "  make dev          - Start development servers"
	@echo "  make dev-all      - Start all services (Docker + API + Web)"
	@echo ""
	@echo "📊 Useful commands:"
	@echo "  make health       - Check service health"
	@echo "  make metrics      - View Prometheus metrics"
	@echo "  make logs         - View application logs"
	@echo ""
	@echo "🔨 Before committing:"
	@echo "  make lint         - Run linters"
	@echo "  make test         - Run test suite"
	@echo "  make typecheck    - Run type checks"
	@echo ""
	@echo "🐘 Database:"
	@echo "  PostgreSQL: localhost:5432 (user: mcps, db: mcps)"
	@echo "  Redis: localhost:6379"
	@echo ""
	@echo "🌐 Services:"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Web: http://localhost:3000"
	@echo ""
