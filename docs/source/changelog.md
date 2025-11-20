---
title: Changelog
description: Version history and release notes for MCPS
---

# Changelog

All notable changes to the Model Context Protocol System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2025-11-19

### Added
- Comprehensive MyST Markdown documentation with enhanced features
- Mermaid diagram support for architecture visualization
- Sphinx design components (grids, cards, tabs)
- Interactive code examples with copy buttons
- Comprehensive Sphinx configuration with 15+ extensions
- Enhanced API documentation with autodoc2

### Changed
- Converted all documentation from reStructuredText to MyST Markdown
- Updated documentation dependencies in pyproject.toml
- Improved documentation structure with new guides section
- Enhanced theme configuration with custom CSS

### Documentation
- Added harvesting guide with examples
- Added analysis guide for security scanning
- Added deployment guide for production setups
- Added tools overview section
- Updated all cross-references to use MyST syntax

## [2.0.0] - 2025-11-18

### Added
- Complete MCPS harvester implementation (Phases 0-4)
- GitHub adapter with GraphQL API integration
- NPM adapter with tarball inspection
- PyPI adapter with wheel/sdist analysis
- AST-based security analyzer
- Health score calculation
- SQLite database with WAL mode
- Alembic migrations
- Parquet export functionality
- JSONL export for LLM training
- CLI interface with Typer
- Comprehensive test suite

### Changed
- Refactored code structure for improved readability
- Enhanced error handling and retry logic
- Optimized database queries with proper indexing

## [1.0.0] - 2025-11-17

### Added
- Initial project structure
- Product Requirements Document (PRD)
- Master Implementation Protocol (TASKS)
- Base harvester abstract class
- SQLModel database models
- Basic CLI scaffolding

[2.5.0]: https://github.com/wyattowalsh/mcps/compare/v2.0.0...v2.5.0
[2.0.0]: https://github.com/wyattowalsh/mcps/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/wyattowalsh/mcps/releases/tag/v1.0.0
