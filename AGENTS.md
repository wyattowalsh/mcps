# AGENTS.md - MCPS Project Guide for AI Coding Assistants

## Overview

MCPS (Model Context Protocol System) is the definitive intelligence hub for the MCP ecosystem. It aggregates, indexes, analyzes, and visualizes Model Context Protocol servers from multiple sources including code repositories (GitHub, NPM, PyPI, Docker, HTTP endpoints) and social media platforms (Reddit, Twitter, YouTube).

**Version:** 3.2.0 (Production-Ready with PostgreSQL + Redis)
**Stack:** Python 3.12+ (Backend), Next.js 15 (Frontend), PostgreSQL + Redis
**Architecture:** Monorepo with clear separation between harvesting logic and presentation
**Scope:** Comprehensive MCP ecosystem database covering code, community discussions, tutorials, and social engagement

## High-Level Context

MCPS is designed as a "Universal Ingestion" system that:
- Harvests MCP servers from heterogeneous sources using polymorphic strategy patterns
- **NEW:** Tracks social media discussions (Reddit posts, Twitter/X threads, YouTube tutorials)
- **NEW:** Analyzes sentiment and community engagement around MCP ecosystem
- Performs deep static analysis (AST-based security scanning)
- Calculates health scores and risk levels algorithmically
- Provides semantic search via vector embeddings (sqlite-vec)
- Exports data in multiple formats (Parquet, JSONL, CSV) for data science workflows
- Offers both a RESTful API (FastAPI) and web dashboard (Next.js 15)
- Links social media mentions to specific servers for comprehensive ecosystem intelligence

## Project Structure

```
mcps/
├── packages/harvester/          # Core Python ETL engine (SQLModel + async)
│   ├── adapters/               # Source-specific harvesters
│   │   ├── github.py           # GitHub GraphQL harvester
│   │   ├── npm.py              # NPM registry + tarball inspection
│   │   ├── pypi.py             # PyPI metadata + wheel/sdist inspection
│   │   ├── docker.py           # Docker registry API v2
│   │   ├── http.py             # HTTP/SSE MCP introspection
│   │   ├── reddit.py           # NEW: Reddit post & comment harvester (PRAW)
│   │   ├── twitter.py          # NEW: Twitter/X API v2 harvester (Tweepy)
│   │   └── youtube.py          # NEW: YouTube Data API v3 harvester
│   ├── analysis/               # AST scanning, embeddings, bus factor calculation
│   ├── core/                   # Base classes, abstractions, updater logic
│   ├── models/                 # SQLModel entities
│   │   ├── models.py           # Core: Server, Tool, Dependency, etc.
│   │   └── social.py           # NEW: SocialPost, Video, Article, Discussion, Event, Company
│   ├── exporters/              # Data export formats (Parquet, JSONL, CSV)
│   ├── tasks/                  # Background scheduler tasks (APScheduler)
│   ├── utils/                  # HTTP client, checkpointing, validation
│   ├── cli.py                  # CLI interface (Typer) - includes harvest-social command
│   └── database.py             # Async session management
│
├── apps/
│   ├── api/                    # FastAPI RESTful API with auth & rate limiting
│   │   └── main.py            # All API endpoints, Pydantic models
│   │
│   └── web/                    # Next.js 15 dashboard (App Router)
│       ├── src/app/           # Next.js pages (Server Components)
│       ├── src/components/    # React components
│       └── src/lib/           # Database access (better-sqlite3), utilities
│
├── docs/source/                # Sphinx documentation (MyST markdown)
│   ├── api/                   # Auto-generated API reference (autodoc2)
│   ├── guides/                # User guides
│   ├── developer-guide/       # Developer documentation
│   └── conf.py                # Sphinx configuration
│
├── tests/                      # Pytest test suite
├── alembic/                    # Database migrations
├── data/                       # SQLite database + exports
│   ├── mcps.db                # Main database (WAL mode)
│   └── exports/               # Generated flatfiles
│
├── pyproject.toml             # Python dependencies (uv)
├── Makefile                   # Development commands
└── .env.example               # Environment variables template
```

## Technology Stack

### Backend (Python 3.12+)
- **Database:** PostgreSQL 15+ with asyncpg driver (production), SQLite for dev/testing
- **Cache:** Redis 7+ for caching layer with graceful degradation
- **ORM:** SQLModel (Pydantic v2 + SQLAlchemy 2.0) with async sessions
- **API:** FastAPI with 9-layer middleware stack (logging, metrics, security, compression)
- **Auth:** API key-based with SlowAPI rate limiting (Redis-backed)
- **Scheduler:** APScheduler (AsyncIO backend) for background tasks
- **HTTP:** httpx with tenacity retry logic
- **Logging:** loguru with structured JSON logging, request ID tracking, Sentry integration
- **Metrics:** Prometheus metrics for monitoring (requests, DB queries, cache hits, etc.)
- **CLI:** Typer for command-line interface
- **Testing:** pytest with async support, pytest-cov for coverage

### Frontend (TypeScript)
- **Framework:** Next.js 15 (App Router, Server Actions, Streaming)
- **React:** React 19 RC (useOptimistic, useFormStatus, useActionState hooks)
- **Styling:** Tailwind CSS 4 (Oxide engine) with dark mode
- **Database Access:** pg (node-postgres) for PostgreSQL (Server Components)
- **Data Fetching:** @tanstack/react-query for client-side caching
- **State Management:** Zustand for global state
- **Visualization:** D3.js for force graphs, Visx for charts
- **Icons:** lucide-react
- **UI Components:** Shadcn-style component library (components/ui/)
- **Validation:** Zod for schema validation
- **Type Safety:** Full TypeScript with strict mode
- **Testing:** Vitest (unit), Playwright (E2E), React Testing Library

### Documentation
- **Generator:** Sphinx with shibuya theme
- **Markdown:** MyST-Parser for .md support
- **API Docs:** autodoc2 for automatic Python API reference
- **Diagrams:** Mermaid via sphinxcontrib-mermaid

## Key Design Patterns

### 1. Polymorphic Strategy Pattern (Harvesters)
All harvesters inherit from `BaseHarvester` and implement:
- `fetch(url)` - Retrieve raw data from source
- `parse(data)` - Transform into Server model
- `store(server, session)` - Persist to database

See: `packages/harvester/core/base_harvester.py`

### 2. Checkpoint System
Uses `ProcessingLog` table to track ingestion state and prevent duplicate processing.
Supports automatic retry with exponential backoff via tenacity.

### 3. Health Scoring Algorithm
Algorithmic 0-100 score based on:
- Stars (logarithmic scale, 0-20 points)
- Forks (logarithmic scale, 0-10 points)
- README presence (10 points)
- License presence (10 points)
- Recent activity (15 points)
- Test indicators (15 points)
- Open issues (0-10 points, inverse)

See: `packages/harvester/adapters/github.py::_calculate_health_score()`

### 4. Risk Level Calculation
Based on AST analysis detecting:
- **CRITICAL:** eval(), exec() usage
- **HIGH:** Subprocess + network/filesystem access
- **MODERATE:** Network or filesystem operations only
- **SAFE:** No dangerous patterns detected

See: `packages/harvester/analysis/ast_analyzer.py::calculate_risk_score()`

### 5. Server Components (Next.js)
Dashboard uses Server Components to query PostgreSQL directly without API serialization overhead.
Database access via node-postgres (pg) in `apps/web/src/lib/db.ts`.

### 6. Middleware Stack (FastAPI)
9-layer middleware stack with specific ordering (first added is outermost):
1. **HealthCheckBypassMiddleware** - Skip logging/metrics for health checks
2. **ErrorHandlerMiddleware** - Catches all exceptions, returns proper JSON responses
3. **SecurityHeadersMiddleware** - HSTS, CSP, X-Frame-Options, etc.
4. **CompressionMiddleware** - Gzip compression for responses >1KB
5. **MetricsMiddleware** - Prometheus metrics collection
6. **LoggingMiddleware** - Request/response logging with request IDs
7. **RateLimitHeadersMiddleware** - Add rate limit info to response headers
8. **RequestIDMiddleware** - Generate/track unique request IDs
9. **CORSMiddleware** - CORS handling (innermost)

### 7. Caching Strategy (Redis)
Three-tier caching with TTLs:
- **Server list endpoints** - 300s TTL, invalidate on server write
- **Server detail endpoints** - 600s TTL, invalidate on specific server update
- **Search results** - 60s TTL, invalidate on any server write
- **Statistics** - 900s TTL, invalidate on daily refresh
- **Cache decorators** - `@cached(ttl=300)` and `@invalidate_cache(pattern="servers:*")`

### 8. Monitoring & Observability
Comprehensive monitoring stack:
- **Structured Logging** - JSON logs with request IDs, correlation IDs, contextual metadata
- **Prometheus Metrics** - HTTP requests, DB queries, cache hits, background tasks
- **Sentry Integration** - Error tracking and performance monitoring
- **Health Checks** - `/health` endpoint with DB and cache status
- **Metrics Endpoint** - `/metrics` for Prometheus scraping
- **Slow Query Detection** - Automatic logging of queries >1s
- **Connection Pool Monitoring** - Track pool size, overflow, timeouts

## Important Constraints and Rules

### Database Operations (PostgreSQL)
1. **ALWAYS use Alembic for schema changes** - Never use `SQLModel.metadata.create_all()` in production
2. **Use async sessions exclusively** - `AsyncSession` with asyncpg driver
3. **Connection pooling configured** - Pool size: 20, max overflow: 10, pre-ping enabled
4. **Use JSONB for JSON data** - PostgreSQL native JSON type with indexing support
5. **Enable query logging in dev** - Set `DB_ECHO=true` to see SQL queries
6. **Monitor slow queries** - Queries >1s are automatically logged
7. **Use indexes wisely** - Add indexes for frequently queried columns
8. **Transactions for writes** - Always wrap writes in transactions
9. **Legacy SQLite support** - Set `USE_SQLITE=true` for dev/testing only

### Cache Operations (Redis)
1. **Cache enabled by default** - Graceful degradation if Redis unavailable
2. **Use cache decorators** - `@cached` and `@invalidate_cache` for easy integration
3. **Set appropriate TTLs** - Default 300s, adjust per endpoint
4. **Cache invalidation** - Invalidate on writes (POST/PUT/DELETE)
5. **Connection pooling** - Pool size: 10 connections
6. **Fail silently option** - Continue operation if cache fails (default: True)
7. **Monitor cache metrics** - Track hit rate, latency, errors

### Static Analysis
1. **NEVER import downloaded modules** - Always use AST parsing (ast.parse for Python, regex for TypeScript)
2. **Sandboxed execution** - If execution is required, use isolated containers
3. **Risk scoring is mandatory** - All servers must have a calculated risk_level

### API Authentication
1. **All endpoints require API key** - Except /health and / (root)
2. **Admin endpoints require admin role** - Delete, bulk update, prune operations
3. **Rate limits enforced** - Via SlowAPI (60/min reads, 30/min writes, 5/min admin)

### Next.js Conventions
1. **Server Components by default** - Only use "use client" when necessary
2. **Database access in Server Components** - Never expose DB credentials to client
3. **Tailwind classes only** - No inline styles or CSS modules

### Documentation
1. **MyST markdown preferred** - For new documentation files
2. **Google-style docstrings** - For Python code
3. **autodoc2 for API docs** - Automatic generation from source code
4. **Mermaid for diagrams** - Use ` ```mermaid` code blocks

## Common Entry Points

### CLI Commands
```bash
# Harvest a GitHub repository
uv run python -m packages.harvester.cli ingest --strategy github --target https://github.com/modelcontextprotocol/servers

# Export data to Parquet
uv run python -m packages.harvester.cli export --format parquet --destination ./data/exports

# Run API server
uv run uvicorn apps.api.main:app --reload --port 8000

# Run web dashboard
cd apps/web && pnpm dev --port 3000

# Build documentation
cd docs && make html
```

### Development Workflow
```bash
# Install dependencies
uv sync
cd apps/web && pnpm install

# Start infrastructure (Docker)
make docker-up          # Start PostgreSQL + Redis
make docker-logs       # View logs
make docker-down       # Stop services

# Run database migrations
make migrate           # Or: uv run alembic upgrade head

# Run tests
make test              # Or: uv run pytest
make test-coverage     # With coverage report

# Code quality checks
make lint              # Run all linters
uv run ruff check .
uv run mypy packages/

# Development servers
make dev-api          # Start FastAPI on :8000
make dev-web          # Start Next.js on :3000
make dev              # Start both (requires tmux/screen)
```

## Sub-AGENTS.md References

For detailed guidance on specific areas, refer to:

- **Harvester System:** `packages/harvester/AGENTS.md`
- **Adapter Implementation:** `packages/harvester/adapters/AGENTS.md`
- **Analysis Modules:** `packages/harvester/analysis/AGENTS.md`
- **Core Abstractions:** `packages/harvester/core/AGENTS.md`
- **API Development:** `apps/api/AGENTS.md`
- **Web Dashboard:** `apps/web/AGENTS.md`
- **Documentation:** `docs/source/AGENTS.md`

## Quick Reference: Key Files

| File | Purpose |
|------|---------|
| `packages/harvester/models/models.py` | SQLModel entity definitions (single source of truth) |
| `packages/harvester/core/base_harvester.py` | Abstract base class for all harvesters |
| `packages/harvester/database.py` | Async session factory and engine setup |
| `apps/api/main.py` | FastAPI application with all endpoints |
| `apps/web/src/lib/db.ts` | Next.js database access layer |
| `docs/source/conf.py` | Sphinx configuration |
| `pyproject.toml` | Python dependencies and project metadata |
| `alembic/env.py` | Alembic migration configuration |

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mcps
# Or use individual components:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=mcps
POSTGRES_PASSWORD=mcps_password
POSTGRES_DB=mcps

# Redis Cache
REDIS_URL=redis://localhost:6379/0
# Or use individual components:
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300

# GitHub API access (for GraphQL queries)
GITHUB_TOKEN=ghp_...

# Social Media APIs (Phase 11)
REDDIT_CLIENT_ID=...           # Reddit API credentials
REDDIT_CLIENT_SECRET=...
TWITTER_BEARER_TOKEN=...       # Twitter/X API v2 credentials
YOUTUBE_API_KEY=...            # YouTube Data API v3 key

# Logging & Monitoring
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                # json for production, text for development
SENTRY_DSN=...                 # Optional: Sentry error tracking
METRICS_ENABLED=true           # Enable Prometheus metrics

# Security
SECURITY_HEADERS_ENABLED=true  # Enable security headers
HSTS_ENABLED=true             # Enable HSTS header
CORS_ENABLED=true             # Enable CORS
CORS_ORIGINS=["http://localhost:3000"]

# Performance
COMPRESSION_ENABLED=true       # Enable gzip compression
COMPRESSION_MINIMUM_SIZE=1024  # Minimum size to compress (bytes)

# OpenAI (Optional for embeddings)
OPENAI_API_KEY=sk-...

# Environment
ENVIRONMENT=development        # development, production, test
```

**Note:** Social media credentials are optional but required for `harvest-social` CLI command. See `.env.example` for all configuration options including subreddit lists, search queries, and quality thresholds.

## Social Media Integration (Phase 11)

MCPS now tracks MCP ecosystem discussions across social media platforms, transforming it from a code-only database into a comprehensive intelligence hub.

### Supported Platforms

1. **Reddit** (`packages/harvester/adapters/reddit.py`)
   - Tracks 10+ programming subreddits (r/LocalLLaMA, r/ChatGPT, r/programming, etc.)
   - Keyword-based post filtering with MCP-specific regex patterns
   - VADER sentiment analysis on post content
   - Extracts GitHub/NPM/PyPI URLs and links to servers
   - Quality scoring based on upvotes, comments, and upvote ratio

2. **Twitter/X** (`packages/harvester/adapters/twitter.py`)
   - Uses Twitter API v2 recent search
   - Tracks hashtags (#MCP), mentions (@modelcontextprotocol), and keywords
   - Engagement metrics: likes, retweets, replies, views
   - Hashtag and mention extraction
   - Sentiment analysis and relevance scoring

3. **YouTube** (`packages/harvester/adapters/youtube.py`)
   - YouTube Data API v3 for video search
   - Discovers tutorials, demos, and educational content
   - Extracts view counts, likes, comments, duration
   - Calculates educational value scores
   - Caption/transcript availability detection

### Data Models

- **SocialPost** - Reddit/Twitter/Discord posts with engagement metrics, sentiment, category
- **Video** - YouTube/Vimeo videos with educational value scores, transcripts
- **Article** - Blog posts from Medium, Dev.to (future)
- **Discussion** - Hacker News, Stack Overflow threads (future)
- **Event** - Meetups, conferences, webinars (future)
- **Company** - Organizations using/building MCP (future)

### CLI Usage

```bash
# Harvest from all platforms
uv run python -m packages.harvester.cli harvest-social --platform all

# Harvest specific platform
uv run python -m packages.harvester.cli harvest-social --platform reddit
uv run python -m packages.harvester.cli harvest-social --platform twitter
uv run python -m packages.harvester.cli harvest-social --platform youtube
```

### Key Features

- **Automatic Server Linking:** URLs mentioned in social posts are automatically linked to Server records
- **Sentiment Analysis:** VADER sentiment classifier (very_positive → very_negative)
- **Quality Scoring:** Algorithmic quality scores (0-100) based on engagement
- **Relevance Scoring:** How relevant content is to MCP (0.0-1.0)
- **Category Classification:** Tutorial, announcement, question, showcase, etc.
- **Configurable Filters:** Minimum score thresholds, search queries, subreddit lists

### Implementation Notes

- Social media APIs are **synchronous** (PRAW, Tweepy, Google API Client)
- Use `asyncio.to_thread()` to wrap sync calls in async harvesters
- All adapters extend `BaseHarvester` for consistency
- Rate limiting handled via API client configuration
- Retry logic with exponential backoff via tenacity decorators

### Future Enhancements (Phases 12-15)

- **Phase 12:** Blog/CMS for curated content and ecosystem updates
- **Phase 13:** Advanced explorers (trend analysis, network graphs, sentiment dashboards)
- **Phase 14:** Community features (user reviews, bookmarks, recommendations)
- **Phase 15:** Predictive analytics (trending detection, quality prediction, ML models)

## Testing Strategy

- **Unit tests:** Test individual functions and classes in isolation
- **Integration tests:** Test harvester workflows end-to-end
- **Fixtures:** Use pytest fixtures for database sessions and mock data
- **Async tests:** Use `pytest-asyncio` for testing async functions
- **Coverage:** Aim for >80% coverage on core modules

## Common Pitfalls to Avoid

1. **Mixing sync and async code** - Use async/await consistently in harvester code
2. **Forgetting to commit sessions** - Always call `await session.commit()` after modifications
3. **Hardcoding URLs** - Use settings.py for configuration
4. **Importing without type checking** - Always use TYPE_CHECKING for circular imports
5. **Client Components for data fetching** - Use Server Components in Next.js for DB queries
6. **Skipping validation** - Let Pydantic handle validation, don't bypass it
7. **Not handling retries** - Use tenacity decorators for network operations
8. **Exposing raw errors to API** - Always return structured error responses
9. **Using SQLite in production** - Always use PostgreSQL for production deployments
10. **Disabling cache without fallback** - Ensure graceful degradation if Redis is down
11. **Ignoring middleware order** - Middleware order matters! First added is outermost
12. **Not setting cache TTLs** - Always specify appropriate TTLs for cached endpoints
13. **Missing request IDs in logs** - Use RequestContext for distributed tracing
14. **Not monitoring metrics** - Always check `/metrics` endpoint for system health

## Getting Help

- **Documentation:** https://mcps.readthedocs.io (or `cd docs && make html`)
- **PRD:** See `PRD.md` for product requirements and design decisions
- **TASKS:** See `TASKS.md` for implementation protocol and phase details
- **Code Comments:** Most complex algorithms have inline documentation
- **Type Hints:** Full type coverage for IDE support

## Version Information

- **Python:** 3.12+ required (uses modern async features)
- **Node.js:** 18+ required (Next.js 15 dependency)
- **PostgreSQL:** 15+ required (production database)
- **Redis:** 7+ required (caching layer)
- **Next.js:** 15.x (App Router with Server Actions)
- **React:** 19.0.0-rc.0 (Release Candidate)
- **FastAPI:** 0.100+
- **SQLModel:** 0.0.14+
- **Tailwind CSS:** 4.x (Oxide engine)

---

**Last Updated:** 2025-11-19
**Maintainer:** Wyatt Walsh
**License:** MIT
