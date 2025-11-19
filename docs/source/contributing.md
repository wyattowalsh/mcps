---
title: Contributing to MCPS
description: Guidelines for contributing to the Model Context Protocol System
---

# Contributing to MCPS

Thank you for your interest in contributing to the Model Context Protocol System!

**Repository:** https://github.com/wyattowalsh/mcps | **License:** MIT

## Getting Started

::::{grid} 2
:gutter: 3

:::{grid-item-card} Required
- Python 3.12+
- uv package installer
- Git
- SQLite 3.35+
:::

:::{grid-item-card} Optional
- GitHub CLI (gh)
- make
- Node.js 20+
:::

::::

### Setup

```bash
git clone https://github.com/wyattowalsh/mcps.git
cd mcps
uv sync
cp .env.example .env
make db-migrate
uv run pytest
```

## Development Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Running Tests

```bash
uv run pytest                                    # All tests
uv run pytest --cov=packages --cov-report=html  # With coverage
uv run pytest tests/test_github_harvester.py    # Specific file
uv run pytest -v                                 # Verbose
uv run pytest -n auto                            # Parallel
```

### Code Quality

```bash
uv run ruff format .      # Format code
uv run ruff check .       # Check linting
uv run ruff check --fix . # Auto-fix
uv run mypy packages/     # Type checking
make lint                 # All checks
```

## Code Style

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} Use pathlib
```python
from pathlib import Path
file_path = Path("data/mcps.db")
```
:::

:::{grid-item-card} Type hints
```python
def fetch(url: str) -> Server:
    ...
```
:::

:::{grid-item-card} Async/await
```python
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```
:::

::::

## Testing

```python
@pytest.mark.asyncio
async def test_github_harvester(mock_session):
    harvester = GitHubHarvester(mock_session)
    server = await harvester.parse(data)
    assert server.name == "test-server"
```

**Coverage Requirements:**
- Core logic: 90%+
- Utilities: 80%+
- CLI: 60%+

## Pull Requests

1. Run tests: `uv run pytest`
2. Check quality: `make lint`
3. Update docs
4. Push branch
5. Create PR with descriptive title

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(adapters): add GitLab harvester

Implements full GitLab repository harvesting including:
- GraphQL query optimization
- Dependency parsing

Closes #123
```

**Types:** feat, fix, docs, style, refactor, test, chore

## License

By contributing, you agree your contributions will be licensed under MIT.

---

**Thank you for contributing!** Questions? Open a GitHub Discussion.
