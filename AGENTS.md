# AGENTS.md - MCPS Project Guide for AI Coding Assistants

## Overview

MCPS (Model Context Protocol System) is the definitive intelligence hub for the MCP ecosystem. It aggregates, indexes, analyzes, and visualizes Model Context Protocol servers from multiple sources including code repositories (GitHub, NPM, PyPI, Docker, HTTP endpoints) and social media platforms (Reddit, Twitter, YouTube).

**Version:** 3.1.0 (Phase 11: Social Media Integration)
**Stack:** Python 3.12+ (Backend), Next.js 15 (Frontend), SQLite with WAL mode
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
- **Database:** SQLite with WAL mode, sqlite-vec for vector search
- **ORM:** SQLModel (Pydantic v2 + SQLAlchemy 2.0)
- **API:** FastAPI with async SQLAlchemy sessions
- **Auth:** API key-based with SlowAPI rate limiting
- **Scheduler:** APScheduler (AsyncIO backend) for background tasks
- **HTTP:** httpx with tenacity retry logic
- **Logging:** loguru for structured logging
- **CLI:** Typer for command-line interface
- **Testing:** pytest with async support

### Frontend (TypeScript)
- **Framework:** Next.js 15 (App Router, React 19 RC)
- **Styling:** Tailwind CSS 4 (Oxide engine)
- **Database Access:** better-sqlite3 (Server Components)
- **Visualization:** D3.js for force graphs, Visx for charts
- **Icons:** lucide-react
- **Type Safety:** Full TypeScript with strict mode

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
Dashboard uses Server Components to query SQLite directly without API serialization overhead.
Database access via better-sqlite3 in `apps/web/src/lib/db.ts`.

## Important Constraints and Rules

### Database Operations
1. **ALWAYS use Alembic for schema changes** - Never use `SQLModel.metadata.create_all()` in production
2. **WAL mode is required** - Enables concurrent reads during writes
3. **Foreign keys enabled** - `PRAGMA foreign_keys = ON`
4. **JSON columns for arrays** - SQLite doesn't support native arrays, use `sa_column=Column(JSON)`

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

# Run database migrations
uv run alembic upgrade head

# Run tests
uv run pytest

# Code quality checks
uv run ruff check .
uv run mypy packages/
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
# GitHub API access (for GraphQL queries)
GITHUB_TOKEN=ghp_...

# Social Media APIs (NEW in Phase 11)
REDDIT_CLIENT_ID=...           # Reddit API credentials
REDDIT_CLIENT_SECRET=...
TWITTER_BEARER_TOKEN=...       # Twitter/X API v2 credentials
YOUTUBE_API_KEY=...            # YouTube Data API v3 key

# Optional: Database path override
DATABASE_URL=sqlite:///data/mcps.db

# Optional: OpenAI API key (for embeddings)
OPENAI_API_KEY=sk-...

# Optional: Log level
LOG_LEVEL=INFO
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

## Getting Help

- **Documentation:** https://mcps.readthedocs.io (or `cd docs && make html`)
- **PRD:** See `PRD.md` for product requirements and design decisions
- **TASKS:** See `TASKS.md` for implementation protocol and phase details
- **Code Comments:** Most complex algorithms have inline documentation
- **Type Hints:** Full type coverage for IDE support

## Version Information

- **Python:** 3.12+ required (uses modern async features)
- **Node.js:** 18+ required (Next.js 15 dependency)
- **SQLite:** 3.35+ required (for WAL mode and JSON support)
- **Next.js:** 15.x (App Router)
- **FastAPI:** 0.100+
- **SQLModel:** 0.0.14+

---

**Last Updated:** 2025-11-19
**Maintainer:** Wyatt Walsh
**License:** MIT
