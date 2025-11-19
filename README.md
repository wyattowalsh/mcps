# MCPS - Model Context Protocol System

> The definitive intelligence hub for the MCP ecosystem.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-sphinx-blue.svg)](https://mcps.readthedocs.io)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black.svg)](https://github.com/your-org/mcps)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/your-org/mcps/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://github.com/your-org/mcps)

**Version:** 3.3.0 | **Status:** Production Ready | **Last Updated:** 2025-11-19

## Overview

MCPS is a **production-ready, Supabase-powered** system that aggregates, indexes, analyzes, and visualizes Model Context Protocol servers from **code repositories AND social media**:

### 🚀 New in v3.3.0: Supabase Integration
- ☁️ **Supabase Backend-as-a-Service** - Auth, Storage, Realtime
- 🔐 **Built-in Authentication** - Email/password + OAuth (GitHub, Google)
- 📁 **File Storage** - CDN-backed storage with Supabase Storage
- ⚡ **Real-time Updates** - WebSocket subscriptions to data changes
- 🔒 **Row Level Security** - Database-level security policies
- 🌐 **Type-safe APIs** - Auto-generated TypeScript types

### Code Repositories
- ✅ GitHub repositories (GraphQL API)
- ✅ NPM packages (registry + tarball inspection)
- ✅ PyPI packages (JSON API + wheel analysis)
- ✅ Docker containers (registry v2)
- ✅ HTTP/SSE endpoints (MCP introspection)

### Social Media & Community (Phase 11 - NEW! 🎉)
- ✅ **Reddit** posts and discussions (PRAW API)
- ✅ **Twitter/X** mentions and threads (Tweepy v2)
- ✅ **YouTube** tutorials and demos (YouTube Data API v3)
- 📊 Sentiment analysis (VADER)
- 🎯 Quality and relevance scoring
- 🔗 Automatic server linking via URL extraction

## Quick Start

### Using Setup Script (Recommended)

```bash
# Clone and install
git clone https://github.com/your-org/mcps.git
cd mcps

# Run setup script (handles everything)
bash scripts/setup.sh

# Start development environment
bash scripts/dev.sh
```

### Manual Installation

```bash
# Clone and install
git clone https://github.com/your-org/mcps.git
cd mcps
uv sync

# Set up environment
cp .env.example .env
# Edit .env and add your API keys (GITHUB_TOKEN, OPENAI_API_KEY, etc.)

# Initialize database
uv run alembic upgrade head

# Start FastAPI backend
uv run uvicorn apps.api.main:app --reload --port 8000

# In another terminal, start Next.js dashboard
cd apps/web && npm run dev
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up

# Application will be available at:
# - API: http://localhost:8000
# - Web: http://localhost:3000
```

## Features

### Core Capabilities
- 🔍 **Deep Metadata Extraction** - Parses mcp.json, package.json, pyproject.toml
- 🛡️ **Security Analysis** - AST-based scanning for dangerous patterns
- 📊 **Health Scoring** - Algorithmic quality assessment
- 🧠 **Semantic Search** - Vector embeddings for similarity search
- 📈 **Dependency Graphs** - Full dependency tree extraction
- 💾 **SQLite-First** - Zero-latency local analytics
- 📦 **Data Exports** - Parquet, JSONL, and binary vector formats

### Social Media Intelligence (Phase 11)
- 📱 **Multi-Platform Harvesting** - Reddit, Twitter/X, YouTube
- 😊 **Sentiment Analysis** - VADER-based emotion classification
- 🎯 **Content Categorization** - Tutorial, news, discussion, showcase, etc.
- 🏆 **Quality Scoring** - Engagement-based quality metrics (0-100)
- 🔗 **Automatic Linking** - Links social mentions to code repositories
- 📊 **Trending Detection** - Identifies popular content over time
- 🎓 **Educational Value** - Scores video content for learning value
- 🌐 **Web Dashboard** - Interactive social media explorer at `/social`

## Documentation

**📚 [Full Documentation](https://mcps.readthedocs.io)** (or build locally with `cd docs && make html`)

Key documentation:

- [Installation](docs/source/installation.rst) - Detailed setup guide
- [Quick Start](docs/source/quick-start.rst) - Getting started tutorial
- [Architecture](docs/source/architecture.rst) - System design
- [API Reference](docs/source/api/index.rst) - Python API docs
- [Contributing](docs/source/contributing.rst) - How to contribute

## Project Structure

```
mcps/
├── packages/harvester/     # Core Python logic
│   ├── adapters/          # Source-specific harvesters
│   ├── analysis/          # Security & analysis modules
│   ├── core/              # Base classes
│   └── exporters/         # Data export formats
├── apps/
│   ├── api/               # FastAPI service
│   └── web/               # Next.js dashboard
├── docs/                  # Sphinx documentation
├── tests/                 # Test suite
└── alembic/               # Database migrations
```

## Development

### Useful Scripts

```bash
# Setup and run
bash scripts/setup.sh      # One-time project setup
bash scripts/dev.sh        # Start development servers
bash scripts/test.sh       # Run all tests and checks
bash scripts/build.sh      # Build for production
bash scripts/backup-db.sh  # Backup SQLite database
```

### Manual Development Commands

```bash
# Run tests with coverage
uv run pytest tests/ --cov=packages --cov-report=html

# Check code quality
uv run ruff check . --fix
uv run mypy packages/
uv run ruff format .

# Start servers individually
uv run uvicorn apps.api.main:app --reload      # FastAPI on :8000
cd apps/web && npm run dev                      # Next.js on :3000

# Build documentation
cd docs && make html
open _build/html/index.html
```

### CLI Commands

```bash
# Code repository harvesting
uv run python -m packages.harvester.cli ingest --strategy github --target https://github.com/owner/repo
uv run python -m packages.harvester.cli export --format parquet --destination ./exports

# Social media harvesting (NEW!)
uv run python -m packages.harvester.cli harvest-social --platform all       # All platforms
uv run python -m packages.harvester.cli harvest-social --platform reddit    # Reddit only
uv run python -m packages.harvester.cli harvest-social --platform twitter   # Twitter/X only
uv run python -m packages.harvester.cli harvest-social --platform youtube   # YouTube only

# Server operations
uv run python -m packages.harvester.cli refresh --url https://github.com/owner/repo
uv run python -m packages.harvester.cli update-health    # Recalculate health scores
uv run python -m packages.harvester.cli update-risk      # Recalculate risk levels
uv run python -m packages.harvester.cli prune --days 180 # Remove stale servers
uv run python -m packages.harvester.cli stats            # Show database statistics
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/source/contributing.rst) for detailed guidelines.

### Report Issues or Request Features

- [Bug Report](https://github.com/your-org/mcps/issues/new?template=bug_report.yml) - Report a bug
- [Feature Request](https://github.com/your-org/mcps/issues/new?template=feature_request.yml) - Suggest an enhancement
- [Documentation](https://github.com/your-org/mcps/issues/new?template=documentation.yml) - Improve docs
- [Question](https://github.com/your-org/mcps/issues/new?template=question.yml) - Ask a question
- [Discussions](https://github.com/your-org/mcps/discussions) - General discussion

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and commit (`git commit -am 'Add feature'`)
4. Run tests: `bash scripts/test.sh`
5. Build and verify: `bash scripts/build.sh`
6. Push to your fork (`git push origin feature/your-feature`)
7. Open a Pull Request with a clear description

See [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) for PR guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

### Documentation

- **[Full Documentation](https://mcps.readthedocs.io)** - Complete project documentation
- **[API Reference](https://mcps.readthedocs.io/en/latest/api/)** - Python API documentation
- **[Architecture Guide](https://mcps.readthedocs.io/en/latest/architecture.html)** - System design
- **[Quick Start Guide](https://mcps.readthedocs.io/en/latest/quick-start.html)** - Getting started tutorial
- **[Deployment Guide](https://mcps.readthedocs.io/en/latest/deployment.html)** - Production deployment

### Community

- **[GitHub Issues](https://github.com/your-org/mcps/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/your-org/mcps/discussions)** - General discussion and Q&A
- **[GitHub Security](https://github.com/your-org/mcps/security)** - Security policy and advisories

### Project Files

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[LICENSE](LICENSE)** - MIT license details
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Project status and roadmap
- **[scripts/](scripts/)** - Utility scripts for setup, testing, building, and backups

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI | REST API and async request handling |
| Web Dashboard | Next.js | Modern React-based UI |
| Database | SQLite | Lightweight local data storage |
| ORM | SQLModel | Type-safe database interactions |
| CLI | Typer | User-friendly command-line interface |
| Testing | Pytest | Comprehensive test suite |
| Linting | Ruff | Fast Python linting and formatting |
| Type Checking | Mypy | Static type analysis |
| Documentation | Sphinx | Professional documentation generation |
| Deployment | Docker | Containerized deployment |

## Acknowledgments

- **Anthropic** - For creating the Model Context Protocol
- **SQLModel** - For elegant ORM with Pydantic integration
- **Ruff** - For blazing-fast Python linting
- **uv** - For fast, reliable Python packaging
- **FastAPI** - For the modern Python web framework
- **Next.js** - For the React framework and deployment options

---

**Built with care for the AI Agent ecosystem**

Made with :heart: | [MIT License](LICENSE) | [Security Policy](SECURITY.md)
