# Changelog

All notable changes to MCPS (Model Context Protocol System) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-01-15

### Added

- **Next.js Web Dashboard** - Complete web UI for browsing and analyzing MCP servers
  - Interactive server catalog with search and filters
  - Detailed server information pages with dependency graphs
  - Health scoring visualization
  - Semantic search capabilities
  - Responsive design with dark mode support

- **Enhanced FastAPI Backend** - Comprehensive REST API for all MCPS operations
  - Server listing, search, and filtering endpoints
  - Detailed server information retrieval
  - Health score calculations via API
  - Vector search integration
  - Rate limiting and CORS support
  - Comprehensive API documentation with Swagger/OpenAPI

- **Deployment Infrastructure** - Production-ready deployment setup
  - Docker containerization with optimized multi-stage builds
  - Docker Compose for local development
  - GitHub Actions CI/CD pipelines
  - Automated testing on push and PR
  - Pre-commit hooks for code quality

- **Documentation Portal** - Comprehensive documentation site
  - Sphinx-based documentation
  - Architecture and design documentation
  - API reference and usage guides
  - Contribution guidelines
  - Deployment instructions

- **Semantic Analysis Framework** - AI-powered analysis capabilities
  - Semantic similarity search using embeddings
  - Context-aware server recommendations
  - Natural language query support
  - Vector database integration

### Changed

- Restructured database schema for better performance
- Improved harvesting pipeline efficiency
- Enhanced error handling and recovery
- Optimized security scanning algorithms
- Updated all dependencies to latest compatible versions

### Fixed

- Database connection pooling issues
- Rate limiting edge cases
- Export format compatibility
- Security scanning false positives

### Deprecated

- Legacy export format support (use Parquet instead)
- Old CLI argument syntax (migration guide provided)

---

## [2.5.0] - 2024-12-20

### Added

- **Vector Search Capabilities** - Semantic similarity search for MCP servers
  - SQLite-vec integration for fast local vector queries
  - Embedding generation for server descriptions
  - Similarity scoring between servers
  - Recommendation engine based on semantic similarity

- **Enhanced Analysis Module** - Deeper code analysis features
  - AST-based vulnerability detection
  - Dependency tree visualization
  - License compatibility checking
  - Code quality metrics

- **Parquet Export Format** - Efficient columnar data export
  - Apache Parquet support for big data workflows
  - Compression support (snappy, gzip)
  - Schema preservation
  - Metadata export

### Changed

- Improved GraphQL query efficiency with batching
- Enhanced NPM package introspection
- Better error messages and logging
- Optimized SQLite queries for large datasets

### Fixed

- NPM tarball extraction edge cases (#127)
- GitHub API rate limit handling (#134)
- Database migration issues (#141)
- Incorrect health score calculations (#149)

### Security

- Added input validation for all CLI commands
- Implemented CORS restrictions
- Enhanced API key management
- Added request signing for critical operations

---

## [2.0.0] - 2024-11-10

### Added

- **PyPI Package Integration** - Full support for Python package repositories
  - Package metadata extraction
  - Wheel analysis
  - Dependency extraction
  - Version history tracking
  - Requires-dist parsing

- **Docker Registry Support** (Beta) - Docker container introspection
  - Layer analysis
  - Image manifest parsing
  - Vulnerability scanning integration

- **Comprehensive Health Scoring** - Algorithmic server quality assessment
  - Documentation completeness score
  - Dependency health metric
  - Security risk scoring
  - Maintenance activity indicator
  - Overall health percentage

- **Advanced Security Scanning** - Code analysis and vulnerability detection
  - Tree-sitter based AST analysis
  - Dangerous pattern detection
  - Dependency vulnerability checking
  - License compliance scanning

### Changed

- Complete refactor of adapter architecture
- Improved async/await patterns throughout
- Enhanced logging with structured logging (loguru)
- Better separation of concerns in modules

### Removed

- Legacy synchronous harvester code
- Old configuration system (replaced with pydantic-settings)
- Deprecated export formats

### Fixed

- Memory leaks in large dataset processing (#89)
- Concurrency issues in parallel harvesting (#94)
- GitHub API pagination bugs (#101)
- Database deadlock issues (#107)

### Migration Guide

For users upgrading from 1.x to 2.0:

1. Update your environment variables (see .env.example)
2. Run database migrations: `uv run alembic upgrade head`
3. Update CLI commands to use new syntax:
   ```bash
   # Old: python -m harvester ingest --source github
   # New: python -m packages.harvester.cli ingest --strategy github
   ```

---

## [1.5.0] - 2024-10-15

### Added

- **JSONL Export Format** - Line-delimited JSON for streaming workflows
  - Efficient line-by-line processing
  - Suitable for big data pipelines
  - Gzip compression support

- **CSV Export Format** - Spreadsheet-compatible data export
  - Configurable delimiters
  - Header row support
  - Quote handling

### Changed

- Improved type hints throughout codebase
- Better error messages for debugging
- Enhanced documentation with examples

### Fixed

- GitHub GraphQL query timeout issues (#78)
- NPM dependency resolution edge cases (#82)
- Export file encoding problems (#85)

---

## [1.0.0] - 2024-09-20

### Added

- **Initial Release** - Core MCPS system with complete feature set

- **GitHub Harvester** - Comprehensive GitHub MCP server discovery
  - GraphQL API integration
  - Repository crawling
  - Manifest parsing (mcp.json)
  - Metadata extraction (package.json, pyproject.toml)
  - Rate limiting handling
  - Pagination support

- **NPM Registry Integration** - JavaScript/Node.js package support
  - NPM registry API integration
  - Tarball download and extraction
  - Package manifest parsing
  - Dependency extraction
  - Version information

- **SQLite Database** - Zero-latency local data storage
  - SQLModel ORM integration
  - Pydantic v2 compatibility
  - Async query support via aiosqlite
  - Schema migrations with Alembic
  - Full-text search capabilities

- **Data Export System** - Multiple output formats
  - JSON export with pretty printing
  - Binary vector format for ML workflows
  - Metadata CSV export
  - Configurable export options

- **CLI Interface** - User-friendly command-line tools
  - Server ingestion commands
  - Data export capabilities
  - Database management utilities
  - Configuration management
  - Help and documentation

- **Documentation** - Comprehensive project documentation
  - Installation guide
  - Quick start tutorial
  - API reference
  - Architecture documentation
  - Configuration guide

### Features

- **Parallel Processing** - Concurrent harvesting for speed
  - Configurable worker pool
  - Backpressure handling
  - Error recovery

- **Metadata Extraction** - Deep package inspection
  - README parsing
  - License detection
  - Dependency extraction
  - Version tracking

- **Type Safety** - Full Python type hints
  - Mypy compatibility
  - Pydantic validation
  - SQLModel relationships

---

## [0.1.0] - 2024-08-15

### Added

- **Initial Framework** - Proof of concept for MCP server aggregation
  - Basic repository structure
  - Core data models
  - Initial CLI scaffolding
  - Documentation skeleton
  - Development environment setup

---

## Unreleased

### Planned Features

- [ ] Real-time server status monitoring
- [ ] Performance metrics and analytics
- [ ] Advanced filtering and query language
- [ ] GraphQL API alongside REST API
- [ ] Server health check endpoints
- [ ] Automated testing infrastructure
- [ ] Kubernetes deployment guides
- [ ] Multi-language support
- [ ] Plugin system for custom harvesters
- [ ] Webhooks for event notifications
- [ ] Server rating and review system

### Known Limitations

- Docker registry support is experimental
- HTTP/SSE endpoint introspection is not yet implemented
- Real-time updates require full re-harvesting
- Limited query language capabilities

---

## Release Notes

### How to Update

```bash
# Update from PyPI (when released)
pip install --upgrade mcps

# Or from GitHub
pip install git+https://github.com/your-org/mcps.git@latest
```

### Reporting Issues

Found a bug? Please report it on our [GitHub Issues](https://github.com/your-org/mcps/issues) page.

### Contributing

Want to contribute? See [CONTRIBUTING](docs/source/contributing.rst) for guidelines.

---

## Links

- [GitHub Repository](https://github.com/your-org/mcps)
- [Documentation](https://mcps.readthedocs.io)
- [Issue Tracker](https://github.com/your-org/mcps/issues)
- [Discussions](https://github.com/your-org/mcps/discussions)
- [Security Policy](SECURITY.md)
