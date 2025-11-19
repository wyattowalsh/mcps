# AGENTS.md - Harvester Package Guide

## Context

The `packages/harvester` directory contains the core Python ETL (Extract, Transform, Load) engine for MCPS. It implements the "Universal Harvester" system that ingests MCP servers from multiple heterogeneous sources using a polymorphic strategy pattern.

**Key Responsibilities:**
- Source-agnostic data ingestion (GitHub, NPM, PyPI, Docker, HTTP)
- Deep metadata extraction and enrichment
- Static code analysis for security risk assessment
- Health score calculation and quality metrics
- Data export in multiple formats
- Background task scheduling for automated maintenance

## Key Files

| File | Purpose |
|------|---------|
| `models/models.py` | SQLModel entity definitions (Server, Tool, Dependency, etc.) |
| `database.py` | Async session factory and engine configuration |
| `settings.py` | Pydantic settings with environment variable support |
| `cli.py` | Typer-based command-line interface |
| `core/base_harvester.py` | Abstract base class for all harvesting strategies |
| `core/updater.py` | ServerUpdater for CRUD operations and maintenance |
| `adapters/*.py` | Source-specific harvester implementations |
| `analysis/*.py` | AST analysis, embeddings, bus factor calculation |
| `exporters/*.py` | Data export logic (Parquet, JSONL, CSV) |
| `tasks/background.py` | APScheduler background tasks |

## Patterns

### 1. Polymorphic Strategy Pattern

All harvesters implement the same interface via `BaseHarvester`:

```python
class YourHarvester(BaseHarvester):
    async def fetch(self, url: str) -> Dict[str, Any]:
        """Retrieve raw data from source"""
        pass

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Transform raw data into Server model"""
        pass

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server and related entities to database"""
        pass
```

The `harvest()` method orchestrates this workflow with automatic checkpointing and retry logic.

### 2. Checkpoint System

Uses `ProcessingLog` table to track state:
- **Status:** `processing`, `completed`, `failed`
- **Retry Logic:** Exponential backoff with tenacity (5 attempts max)
- **Deduplication:** Skips URLs already marked as `completed`

```python
# Checkpoint tracking happens automatically in BaseHarvester.harvest()
await self._mark_processing_started(url)
# ... do work ...
await self._mark_processing_completed(url)
```

### 3. Async Session Management

All database operations use async sessions:

```python
from packages.harvester.database import async_session_maker

async with async_session_maker() as session:
    # Perform database operations
    await session.commit()
```

### 4. Health Scoring

Calculated algorithmically in adapter parse() methods:

```python
health_score = self._calculate_health_score(
    stars=stars,
    forks=forks,
    has_readme=bool(readme_text),
    has_license=bool(license_name),
    has_recent_activity=self._has_recent_activity(pushed_at_str),
    has_tests=self._has_tests_indicator(package_json_text, pyproject_toml_text),
    open_issues=open_issues,
)
```

Score range: 0-100 (see root AGENTS.md for formula breakdown)

### 5. Risk Level Determination

Based on AST analysis results:

```python
from packages.harvester.analysis.ast_analyzer import analyze_file, calculate_risk_score

patterns, risk_level = analyze_file(Path("code.py"))
# risk_level: SAFE, MODERATE, HIGH, or CRITICAL
```

## Constraints

### Database Schema Changes
1. **NEVER modify models.py without creating an Alembic migration**
2. **NEVER use create_all()** - Always use `alembic upgrade head`
3. **JSON columns for lists/dicts** - SQLite requires `sa_column=Column(JSON)`

Example migration workflow:
```bash
# After modifying models.py
uv run alembic revision --autogenerate -m "Add new field"
uv run alembic upgrade head
```

### Async/Await Usage
1. **All database operations must be async** - Use `AsyncSession` exclusively
2. **HTTP requests must be async** - Use httpx via `get_client()`
3. **No blocking I/O** - Use aiofiles for file operations if needed

### Static Analysis Safety
1. **NEVER import untrusted code** - Use `ast.parse()` for Python, regex for TypeScript
2. **NEVER execute downloaded code** - Static analysis only
3. **Sandbox if execution required** - Use Docker containers

### Retry Logic
1. **Use tenacity decorators** - For network operations
2. **Exponential backoff** - Start at 2s, max 30s
3. **Limit attempts** - Default 5 retries maximum

Example:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30)
)
async def fetch_data(url: str):
    # Network operation
    pass
```

## Examples

### Adding a New Harvester

1. Create adapter file in `adapters/`:

```python
# packages/harvester/adapters/gitlab.py
from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models.models import Server

class GitLabHarvester(BaseHarvester):
    async def fetch(self, url: str) -> Dict[str, Any]:
        # Implement GitLab API fetching
        pass

    async def parse(self, data: Dict[str, Any]) -> Server:
        # Transform to Server model
        pass

    async def store(self, server: Server, session: AsyncSession) -> None:
        # Upsert logic (check for existing server by primary_url)
        pass
```

2. Register in CLI (`cli.py`):

```python
HARVESTERS = {
    "github": GitHubHarvester,
    "npm": NPMHarvester,
    "gitlab": GitLabHarvester,  # Add here
}
```

### Running a Harvest

```python
from packages.harvester.database import async_session_maker
from packages.harvester.adapters.github import GitHubHarvester

async def main():
    async with async_session_maker() as session:
        harvester = GitHubHarvester(session)
        server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")
        print(f"Harvested: {server.name}")

# CLI equivalent:
# uv run python -m packages.harvester.cli ingest --strategy github --target https://github.com/modelcontextprotocol/servers
```

### Bulk Update Operations

```python
from packages.harvester.core.updater import ServerUpdater

async with async_session_maker() as session:
    updater = ServerUpdater(session)

    # Update single server
    await updater.update_server(server_id=1, updates={"verified_source": True})

    # Bulk update
    filters = {"host_type": "github", "stars__gt": 100}
    updates = {"verified_source": True}
    count = await updater.bulk_update_servers(filters, updates)

    # Refresh server (re-harvest)
    server = await updater.refresh_server("https://github.com/owner/repo")
```

## Testing

### Test Structure

```
tests/
├── test_adapters/
│   ├── test_github.py          # GitHub harvester tests
│   ├── test_npm.py             # NPM harvester tests
│   └── test_pypi.py            # PyPI harvester tests
├── test_analysis/
│   └── test_ast_analyzer.py    # AST analysis tests
└── conftest.py                 # Shared fixtures
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/test_adapters/test_github.py

# With coverage
uv run pytest --cov=packages/harvester --cov-report=html

# Async tests (automatically handled by pytest-asyncio)
uv run pytest -v
```

### Example Test

```python
import pytest
from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.database import async_session_maker

@pytest.mark.asyncio
async def test_github_harvester():
    async with async_session_maker() as session:
        harvester = GitHubHarvester(session)

        # Mock or use a known test repository
        server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")

        assert server is not None
        assert server.host_type == "github"
        assert server.health_score >= 0
```

## Common Tasks

### 1. Add New Server Field

**Steps:**
1. Add field to `models/models.py`:
```python
class Server(BaseEntity, table=True):
    # ... existing fields ...
    new_field: Optional[str] = None
```

2. Create migration:
```bash
uv run alembic revision --autogenerate -m "Add new_field to Server"
```

3. Review generated migration in `alembic/versions/`

4. Apply migration:
```bash
uv run alembic upgrade head
```

5. Update adapter parse() methods to populate new field

### 2. Add New Background Task

**Steps:**
1. Add task function in `tasks/background.py`:
```python
async def my_new_task():
    logger.info("Running my new task")
    async with async_session_maker() as session:
        # Task logic
        pass
```

2. Register task in scheduler:
```python
scheduler.add_job(
    my_new_task,
    trigger="cron",
    hour=3,
    minute=0,
    id="my_new_task",
    replace_existing=True
)
```

### 3. Export Data in New Format

**Steps:**
1. Create exporter in `exporters/`:
```python
# packages/harvester/exporters/excel.py
from packages.harvester.exporters.exporter import BaseExporter

class ExcelExporter(BaseExporter):
    async def export(self, destination: Path):
        # Export logic using pandas or openpyxl
        pass
```

2. Register in CLI

### 4. Calculate New Metric

**Steps:**
1. Add calculation method to appropriate adapter:
```python
def _calculate_bus_factor(self, contributors: List[Contributor]) -> int:
    # Calculate bus factor (minimum team size)
    pass
```

2. Add field to Server model (see task #1)

3. Update parse() method to call calculation

4. Create migration

## Related Areas

- **Adapters:** See `packages/harvester/adapters/AGENTS.md` for adapter-specific guidance
- **Analysis:** See `packages/harvester/analysis/AGENTS.md` for AST and security analysis
- **Core:** See `packages/harvester/core/AGENTS.md` for base classes and abstractions
- **API Integration:** See `apps/api/AGENTS.md` for how harvesters integrate with API
- **Root Guide:** See `/home/user/mcps/AGENTS.md` for project-wide context

## Dependencies

Key Python packages used:
- **SQLModel** - ORM with Pydantic validation
- **httpx** - Async HTTP client
- **tenacity** - Retry logic with backoff
- **loguru** - Structured logging
- **pydantic-settings** - Environment variable management
- **typer** - CLI framework
- **APScheduler** - Background task scheduling

## Logging

Structured logging via loguru:

```python
from loguru import logger

logger.info("Fetching data from {url}", url=url)
logger.success("Successfully harvested {name}", name=server.name)
logger.warning("No mcp.json found for {name}", name=name)
logger.error("Failed to harvest {url}: {error}", url=url, error=str(e))
```

Log levels configured via `LOG_LEVEL` environment variable (default: INFO)

## Performance Considerations

1. **Batch database operations** - Use bulk inserts when possible
2. **Connection pooling** - Session factory manages pool automatically
3. **Rate limiting** - Respect API rate limits (GitHub: 5000/hour authenticated)
4. **Concurrent harvesting** - Use asyncio.gather() for parallel harvests
5. **Checkpoint frequently** - Prevents re-processing on failure

## Troubleshooting

### Database Locked
**Symptom:** `sqlite3.OperationalError: database is locked`
**Solution:** Ensure WAL mode is enabled in `database.py`:
```python
connect_args={"check_same_thread": False, "isolation_level": None}
```

### Import Errors
**Symptom:** `ModuleNotFoundError: No module named 'packages'`
**Solution:** Run from project root, not from within packages/

### Async Issues
**Symptom:** `RuntimeWarning: coroutine 'xyz' was never awaited`
**Solution:** Always use `await` with async functions

---

**Last Updated:** 2025-11-19
**See Also:** Root AGENTS.md, PRD.md, TASKS.md
