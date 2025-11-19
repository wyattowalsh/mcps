# Contributing to MCPS

> Thank you for your interest in contributing to the Model Context Protocol System! This guide will help you get started with development, testing, and submitting contributions.

**Project:** Model Context Protocol System (MCPS)
**Repository:** https://github.com/your-org/mcps
**License:** MIT

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Development Environment Setup](#development-environment-setup)
  - [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
  - [Creating a Branch](#creating-a-branch)
  - [Making Changes](#making-changes)
  - [Running Tests](#running-tests)
  - [Code Quality](#code-quality)
- [Adding New Features](#adding-new-features)
  - [Adding a New Registry Adapter](#adding-a-new-registry-adapter)
  - [Adding New Analysis Modules](#adding-new-analysis-modules)
  - [Adding Export Formats](#adding-export-formats)
- [Code Style Guidelines](#code-style-guidelines)
  - [Python Style (Ruff + MyPy)](#python-style-ruff--mypy)
  - [Naming Conventions](#naming-conventions)
  - [Documentation Standards](#documentation-standards)
- [Testing Guidelines](#testing-guidelines)
  - [Unit Tests](#unit-tests)
  - [Integration Tests](#integration-tests)
  - [Test Coverage](#test-coverage)
- [Submitting Changes](#submitting-changes)
  - [Pull Request Process](#pull-request-process)
  - [Commit Message Guidelines](#commit-message-guidelines)
  - [Code Review Process](#code-review-process)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

---

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Prioritize the project's goals over personal preferences

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - Check with `python --version`
- **uv** - Fast Python package installer ([Installation](https://github.com/astral-sh/uv))
- **Git** - Version control
- **SQLite 3.35+** - Should be included with Python

**Optional but Recommended:**
- **GitHub CLI (gh)** - For managing PRs
- **make** - For using Makefile commands
- **Node.js 20+** - If working on the web dashboard

### Development Environment Setup

1. **Clone the repository:**

```bash
git clone https://github.com/your-org/mcps.git
cd mcps
```

2. **Install Python dependencies:**

```bash
# Install all dependencies including dev tools
uv sync

# Or use make command
make install
```

3. **Set up environment variables:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
# GITHUB_TOKEN=your_github_personal_access_token
```

4. **Initialize the database:**

```bash
# Run database migrations
make db-migrate

# Or manually:
uv run alembic upgrade head
```

5. **Verify installation:**

```bash
# Run tests to ensure everything works
uv run pytest

# Check code formatting
uv run ruff check .
```

### Project Structure

```
mcps/
├── packages/harvester/       # Core ETL logic
│   ├── adapters/            # Source-specific harvesters
│   │   ├── github.py        # GitHub GraphQL adapter
│   │   ├── npm.py           # NPM registry adapter
│   │   ├── pypi.py          # PyPI adapter
│   │   ├── docker.py        # Docker registry adapter
│   │   └── http.py          # HTTP/SSE adapter
│   ├── analysis/            # Code analysis & security
│   │   ├── ast_analyzer.py  # AST-based security scanning
│   │   ├── embeddings.py    # Vector embedding generation
│   │   └── bus_factor.py    # Contributor analysis
│   ├── core/                # Base classes & models
│   │   ├── models.py        # Enums and base entities
│   │   └── base_harvester.py
│   ├── exporters/           # Data export formats
│   │   └── exporter.py      # Parquet, JSONL, Vector exports
│   ├── models/              # Database models
│   │   └── models.py        # SQLModel definitions
│   ├── utils/               # Utilities
│   │   ├── http_client.py   # HTTP retry logic
│   │   └── checkpointing.py # Processing state management
│   ├── cli.py               # Typer CLI interface
│   ├── database.py          # DB connection management
│   └── settings.py          # Pydantic settings
├── apps/
│   ├── api/                 # FastAPI service (future)
│   └── web/                 # Next.js dashboard (future)
├── alembic/                 # Database migrations
│   └── versions/            # Migration files
├── tests/                   # Test suite
│   ├── test_github_harvester.py
│   └── ...
├── data/                    # Data storage (gitignored)
│   └── mcps.db              # SQLite database
├── Makefile                 # Dev workflow automation
├── pyproject.toml           # Python dependencies
├── ruff.toml                # Ruff configuration
└── alembic.ini              # Alembic configuration
```

---

## Development Workflow

### Creating a Branch

Always create a new branch for your work:

```bash
# Feature branch
git checkout -b feature/add-gitlab-adapter

# Bug fix branch
git checkout -b fix/github-rate-limit

# Documentation branch
git checkout -b docs/update-contributing-guide
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Making Changes

1. **Understand the architecture:**
   - Read `PRD.md` for product requirements
   - Review `ARCHITECTURE.md` for system design
   - Check `DATA_DICTIONARY.md` for database schema

2. **Make focused commits:**
   - One logical change per commit
   - Write clear commit messages
   - Test before committing

3. **Keep dependencies updated:**
   - Use `uv add package-name` to add dependencies
   - Update `pyproject.toml` for version constraints

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Run specific test file
uv run pytest tests/test_github_harvester.py

# Run with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Format code with Ruff
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Auto-fix linting issues (when possible)
uv run ruff check --fix .

# Type checking with MyPy
uv run mypy packages/

# All checks via Makefile
make lint
```

---

## Adding New Features

### Adding a New Registry Adapter

Follow the **Polymorphic Strategy Pattern** to add support for new package registries or hosting platforms.

**Example: Adding a GitLab Adapter**

1. **Create the adapter file:**

```python
# packages/harvester/adapters/gitlab.py

from typing import Any, Dict
from sqlmodel.ext.asyncio.session import AsyncSession
from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models.models import Server

class GitLabHarvester(BaseHarvester):
    """GitLab-specific harvester using REST API."""

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch repository data from GitLab API."""
        # Implementation here
        pass

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse GitLab response into Server model."""
        # Implementation here
        pass

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server to database."""
        # Use parent class implementation
        await super().store(server, session)
```

2. **Implement the base methods:**

All adapters must implement:
- `fetch(url: str) -> Dict[str, Any]` - Retrieve raw data from source
- `parse(data: Dict[str, Any]) -> Server` - Transform data into Server model
- `store(server: Server, session: AsyncSession) -> None` - Persist to database

3. **Add tests:**

```python
# tests/test_gitlab_harvester.py

import pytest
from packages.harvester.adapters.gitlab import GitLabHarvester

@pytest.mark.asyncio
async def test_gitlab_harvester_fetch(mock_session):
    """Test fetching from GitLab API."""
    harvester = GitLabHarvester(mock_session)
    data = await harvester.fetch("https://gitlab.com/owner/repo")
    assert data is not None
```

4. **Register in CLI:**

```python
# packages/harvester/cli.py

async def _ingest_gitlab(target: str, session) -> None:
    """Ingest from GitLab."""
    from packages.harvester.adapters.gitlab import GitLabHarvester
    harvester = GitLabHarvester(session)
    await harvester.harvest(target)
```

5. **Update documentation:**

Add your adapter to:
- `README.md` - Usage examples
- `ARCHITECTURE.md` - Component descriptions
- This `CONTRIBUTING.md` - List of available adapters

**Available Adapters:**
- `GitHubHarvester` - GitHub GraphQL API
- `NPMHarvester` - NPM registry API
- `PyPIHarvester` - PyPI JSON API
- `DockerHarvester` - Docker registry v2
- `HTTPHarvester` - Generic HTTP/SSE endpoints

### Adding New Analysis Modules

Security analysis and code inspection modules.

**Example: Adding Dependency Vulnerability Scanning**

1. **Create the analyzer:**

```python
# packages/harvester/analysis/vulnerability_scanner.py

from typing import List, Dict
from packages.harvester.models.models import Dependency

class VulnerabilityScanner:
    """Scans dependencies for known CVEs."""

    async def scan_dependencies(
        self, dependencies: List[Dependency]
    ) -> Dict[str, List[str]]:
        """Scan dependencies against vulnerability databases."""
        # Implementation using OSV API or similar
        pass
```

2. **Integrate into harvester flow:**

Modify the harvester to call your analyzer during the `parse()` phase.

### Adding Export Formats

1. **Create exporter class:**

```python
# packages/harvester/exporters/exporter.py

class CSVExporter:
    """Exports MCPS data to CSV format."""

    @staticmethod
    async def export_servers(output_path: Path, session: AsyncSession) -> None:
        """Export servers to CSV."""
        # Implementation here
        pass
```

2. **Add CLI command:**

Update `cli.py` to support the new format in the `export` command.

---

## Code Style Guidelines

### Python Style (Ruff + MyPy)

We use **Ruff** for linting and formatting, and **MyPy** for type checking.

**Ruff Configuration (`ruff.toml`):**
- Line length: 100 characters
- Target: Python 3.12+
- Enabled rules: E, F, I, B, C4, UP, ARG, SIM, TCH, PTH, RUF

**Key Rules:**
1. **Always use pathlib over os.path:**
   ```python
   # Good
   from pathlib import Path
   file_path = Path("data/mcps.db")

   # Bad
   import os
   file_path = os.path.join("data", "mcps.db")
   ```

2. **Use type hints:**
   ```python
   # Good
   def fetch_server(url: str) -> Server:
       ...

   # Bad
   def fetch_server(url):
       ...
   ```

3. **Prefer async/await for I/O:**
   ```python
   # Good
   async def fetch_data(url: str) -> dict:
       async with httpx.AsyncClient() as client:
           response = await client.get(url)
           return response.json()
   ```

4. **Use Pydantic/SQLModel validation:**
   ```python
   # Good
   server = Server(name="example", primary_url="https://...")

   # Bad (bypasses validation)
   server = Server()
   server.name = "example"
   ```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Modules | snake_case | `github_harvester.py` |
| Classes | PascalCase | `GitHubHarvester` |
| Functions | snake_case | `parse_github_url()` |
| Constants | UPPER_SNAKE | `GRAPHQL_QUERY` |
| Private | _leading_underscore | `_parse_json()` |
| Async functions | async_ prefix (optional) | `async_fetch_data()` |

### Documentation Standards

**Docstrings:**
Use Google-style docstrings for all public functions and classes:

```python
def calculate_health_score(
    stars: int,
    forks: int,
    has_readme: bool,
) -> int:
    """Calculate health score from 0-100 based on various metrics.

    Args:
        stars: Number of GitHub stars
        forks: Number of forks
        has_readme: Whether README exists

    Returns:
        Health score from 0-100

    Raises:
        ValueError: If stars or forks are negative

    Example:
        >>> calculate_health_score(100, 20, True)
        85
    """
```

**Comments:**
- Explain "why", not "what"
- Use for complex logic only
- Keep comments up-to-date

---

## Testing Guidelines

### Unit Tests

Write unit tests for all new functions and classes.

**Test Structure:**
```python
# tests/test_github_harvester.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from packages.harvester.adapters.github import GitHubHarvester

@pytest.fixture
def mock_session():
    """Create mock database session."""
    return AsyncMock()

@pytest.fixture
def mock_github_response():
    """Mock GitHub GraphQL response."""
    return {
        "repository": {
            "name": "test-server",
            "stargazerCount": 100,
            # ... more fields
        }
    }

@pytest.mark.asyncio
async def test_github_harvester_parse(mock_session, mock_github_response):
    """Test parsing GitHub API response."""
    harvester = GitHubHarvester(mock_session)
    server = await harvester.parse(mock_github_response)

    assert server.name == "test-server"
    assert server.stars == 100
    assert server.host_type == HostType.GITHUB

def test_parse_github_url():
    """Test GitHub URL parsing."""
    harvester = GitHubHarvester(AsyncMock())
    owner, repo = harvester._parse_github_url(
        "https://github.com/modelcontextprotocol/servers"
    )

    assert owner == "modelcontextprotocol"
    assert repo == "servers"
```

### Integration Tests

Test end-to-end workflows:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_github_harvest_workflow(test_db_session):
    """Test complete GitHub harvesting workflow."""
    harvester = GitHubHarvester(test_db_session)

    # This will make actual API calls (use sparingly)
    server = await harvester.harvest(
        "https://github.com/modelcontextprotocol/servers"
    )

    assert server is not None
    assert len(server.tools) > 0
```

### Test Coverage

Aim for **80%+ code coverage** for new code:

```bash
# Generate coverage report
uv run pytest --cov=packages --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Coverage Requirements:**
- Core logic (adapters, parsers): 90%+
- Utilities: 80%+
- CLI commands: 60%+

---

## Submitting Changes

### Pull Request Process

1. **Ensure all checks pass:**
   ```bash
   # Run full test suite
   uv run pytest

   # Check code quality
   make lint

   # Verify types
   uv run mypy packages/
   ```

2. **Update documentation:**
   - Add docstrings to new functions
   - Update README.md if adding features
   - Update DATA_DICTIONARY.md if changing schema

3. **Create pull request:**
   ```bash
   # Push your branch
   git push origin feature/your-feature-name

   # Create PR using GitHub CLI
   gh pr create --title "Add GitLab adapter" --body "Implements GitLab harvesting support as described in #123"
   ```

4. **PR Template:**
   ```markdown
   ## Description
   Brief description of what this PR does

   ## Related Issues
   Fixes #123

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing performed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests pass locally
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

### Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

**Examples:**
```bash
feat(adapters): add GitLab harvester with GraphQL support

Implements full GitLab repository harvesting including:
- GraphQL query optimization
- Dependency parsing
- Contributor extraction

Closes #123

---

fix(github): handle rate limiting with exponential backoff

GitHub API occasionally returns 429 errors during bulk harvesting.
Added retry logic with tenacity to handle rate limits gracefully.

Fixes #456
```

### Code Review Process

1. **Automated checks run on PR creation:**
   - Ruff linting
   - MyPy type checking
   - Pytest test suite
   - Coverage report

2. **Reviewer guidelines:**
   - Check for code clarity
   - Verify test coverage
   - Ensure documentation exists
   - Look for potential bugs

3. **Addressing feedback:**
   - Respond to all comments
   - Push new commits (don't force-push)
   - Re-request review when ready

4. **Merging:**
   - Requires 1 approval
   - All checks must pass
   - Squash and merge preferred

---

## Issue Guidelines

### Reporting Bugs

Use the bug report template:

```markdown
**Description:**
Brief description of the bug

**To Reproduce:**
1. Run command X
2. Observe error Y

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12.0
- MCPS version: 2.5.0

**Logs:**
```
Paste relevant logs here
```
```

### Feature Requests

Use the feature request template:

```markdown
**Problem Statement:**
What problem does this solve?

**Proposed Solution:**
How should it work?

**Alternatives Considered:**
What other approaches did you consider?

**Additional Context:**
Any relevant links, diagrams, etc.
```

---

## Community

### Getting Help

- **Documentation:** Check `docs/` directory
- **GitHub Discussions:** For questions and ideas
- **Issues:** For bugs and feature requests

### Communication Channels

- GitHub Issues: Bug reports and features
- GitHub Discussions: Q&A and brainstorming
- Pull Requests: Code contributions

---

## License

By contributing to MCPS, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to MCPS!**

For questions about contributing, open a GitHub Discussion or reach out to the maintainers.
