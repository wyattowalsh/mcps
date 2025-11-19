# AGENTS.md - Core Module Guide

## Context

The `packages/harvester/core/` directory contains the foundational abstractions and base classes that define the harvester architecture. This module provides the polymorphic strategy pattern infrastructure that all adapters inherit from.

**Key Responsibilities:**
- Define abstract base class for harvesters (BaseHarvester)
- Provide CRUD operations for servers (ServerUpdater)
- Define core data models and enums (RiskLevel, HostType, etc.)
- Implement checkpoint and retry logic
- Manage error handling patterns

## Key Files

| File | Purpose |
|------|---------|
| `base_harvester.py` | Abstract base class for all harvesting strategies |
| `updater.py` | ServerUpdater class for CRUD and maintenance operations |
| `models.py` | Core enums and constants (HostType, RiskLevel, DependencyType) |

## BaseHarvester Implementation Guide

### Class Structure

```python
from abc import ABC, abstractmethod
from packages.harvester.core.base_harvester import BaseHarvester

class MyHarvester(BaseHarvester):
    """Custom harvester implementation.

    Attributes:
        session: Async database session
        # Add custom attributes here
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        # Initialize custom attributes

    @abstractmethod
    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch raw data from source."""
        pass

    @abstractmethod
    async def parse(self, data: Dict[str, Any]) -> Server:
        """Transform raw data into Server model."""
        pass

    @abstractmethod
    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server to database."""
        pass
```

### Lifecycle Methods

#### 1. fetch() - Data Retrieval

**Purpose:** Retrieve raw data from external source without transformation.

**Best Practices:**
- Use httpx for HTTP requests (via `get_client()`)
- Add retry logic with tenacity
- Validate URL before making requests
- Return unprocessed data as dictionary
- Raise `HarvesterError` on failures

```python
async def fetch(self, url: str) -> Dict[str, Any]:
    """Fetch data from API."""
    # Validate URL
    if not self._is_valid_url(url):
        raise HarvesterError(f"Invalid URL: {url}")

    # Make request with retry logic
    client = get_client()
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except HTTPClientError as e:
        raise HarvesterError(f"Failed to fetch: {str(e)}") from e
```

#### 2. parse() - Data Transformation

**Purpose:** Transform raw data into structured Server model with all relationships.

**Best Practices:**
- Extract all available metadata
- Create related entities (tools, dependencies, etc.)
- Calculate health score
- Determine risk level
- Handle missing/malformed data gracefully
- Return fully populated Server instance

```python
async def parse(self, data: Dict[str, Any]) -> Server:
    """Parse raw data into Server model."""
    # Create base Server entity
    server = Server(
        name=data.get("name"),
        primary_url=data.get("url"),
        host_type=HostType.GITHUB,
        description=data.get("description"),
        # ... other fields
    )

    # Parse and add tools
    for tool_data in data.get("tools", []):
        tool = Tool(
            name=tool_data.get("name"),
            description=tool_data.get("description"),
            input_schema=tool_data.get("inputSchema", {}),
        )
        server.tools.append(tool)

    # Calculate metrics
    server.health_score = self._calculate_health_score(...)
    server.risk_level = self._determine_risk_level(...)

    return server
```

#### 3. store() - Data Persistence

**Purpose:** Persist Server and all related entities to database with upsert logic.

**Best Practices:**
- Check for existing server by primary_url
- Update existing or create new
- Handle related entities (clear and repopulate)
- Use transactions (commit or rollback)
- Update timestamps
- Log operations

```python
async def store(self, server: Server, session: AsyncSession) -> None:
    """Store server with upsert logic."""
    # Check if exists
    statement = select(Server).where(Server.primary_url == server.primary_url)
    result = await session.execute(statement)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        for field in ["name", "description", "health_score"]:
            setattr(existing, field, getattr(server, field))

        # Replace related entities
        existing.tools.clear()
        for tool in server.tools:
            tool.server_id = existing.id
            existing.tools.append(tool)

        session.add(existing)
    else:
        # Create new
        session.add(server)

    await session.commit()
```

### Checkpoint Methods

BaseHarvester provides automatic checkpointing via ProcessingLog:

```python
# These methods are called automatically by harvest()
await self._mark_processing_started(url)    # Set status to 'processing'
await self._mark_processing_completed(url)  # Set status to 'completed'
await self._mark_processing_failed(url, error_message)  # Set status to 'failed'

# Check if URL was already processed
log = await self._get_processing_log(url)
if log and log.status == "completed":
    logger.info(f"Skipping {url} - already completed")
    return None
```

### Error Handling

```python
from packages.harvester.core.base_harvester import HarvesterError

# Raise HarvesterError for all harvester-specific errors
if not data:
    raise HarvesterError("No data received from API")

# Base class handles retry logic automatically
# Exponential backoff: 2s, 4s, 8s, 16s, 30s (max 5 attempts)
```

## ServerUpdater Usage

The ServerUpdater class provides CRUD operations and maintenance tasks:

### Basic CRUD

```python
from packages.harvester.core.updater import ServerUpdater
from packages.harvester.database import async_session_maker

async with async_session_maker() as session:
    updater = ServerUpdater(session)

    # Get server by ID
    server = await updater.get_server(server_id=1)

    # Update server
    updated = await updater.update_server(
        server_id=1,
        updates={"verified_source": True, "health_score": 95}
    )

    # Delete server (cascade to related entities)
    await updater.delete_server(server_id=1)
```

### Bulk Operations

```python
# Bulk update servers matching filter
filters = {"host_type": "github", "stars__gte": 100}
updates = {"verified_source": True}
count = await updater.bulk_update_servers(filters, updates)

# Get servers with filters
servers = await updater.get_servers(
    filters={"host_type": "npm", "risk_level": "high"},
    limit=50
)
```

### Refresh Operations

```python
# Refresh single server (re-harvest)
server = await updater.refresh_server("https://github.com/owner/repo")

# Auto-refresh stale servers (> 7 days old)
count = await updater.refresh_stale_servers(days=7)
```

### Maintenance Operations

```python
# Recalculate health scores for all servers
count = await updater.update_health_scores()

# Recalculate risk levels for all servers
count = await updater.update_risk_levels()

# Prune inactive servers (> 180 days)
count = await updater.prune_stale_servers(days=180)

# Get database statistics
stats = await updater.get_statistics()
# Returns: total_servers, by_host_type, by_risk_level, etc.
```

## Database Session Management

### Async Session Factory

```python
from packages.harvester.database import async_session_maker

# Use as async context manager
async with async_session_maker() as session:
    # Perform database operations
    result = await session.execute(select(Server))
    servers = result.scalars().all()

    # Session automatically committed on exit
    # Or rolled back on exception
```

### Manual Session Control

```python
session = async_session_maker()

try:
    async with session:
        # Operations
        await session.commit()
except Exception as e:
    await session.rollback()
    raise
finally:
    await session.close()
```

### Session Best Practices

1. **Always use async sessions** - Never use sync sessions
2. **One session per request** - Don't share sessions across requests
3. **Commit explicitly** - Call `await session.commit()` after modifications
4. **Rollback on errors** - Ensure rollback in exception handlers
5. **Close sessions** - Use context managers for automatic cleanup

## Core Data Models

### Enums

```python
from packages.harvester.core.models import HostType, RiskLevel, DependencyType

# HostType - Source of server
HostType.GITHUB    # GitHub repositories
HostType.NPM       # NPM packages
HostType.PYPI      # PyPI packages
HostType.DOCKER    # Docker images
HostType.HTTP      # HTTP/SSE endpoints

# RiskLevel - Security risk assessment
RiskLevel.SAFE        # Verified, no dangerous patterns
RiskLevel.MODERATE    # Network/filesystem operations
RiskLevel.HIGH        # Subprocess execution
RiskLevel.CRITICAL    # eval(), exec(), or multiple high-risk ops
RiskLevel.UNKNOWN     # Not yet analyzed

# DependencyType
DependencyType.RUNTIME  # Production dependencies
DependencyType.DEV      # Development dependencies
DependencyType.PEER     # Peer dependencies
```

## Examples

### Example 1: Complete Harvester Implementation

```python
from packages.harvester.core.base_harvester import BaseHarvester, HarvesterError
from packages.harvester.models.models import Server, Tool

class CustomHarvester(BaseHarvester):
    """Example custom harvester."""

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch data from custom API."""
        client = get_client()
        response = await client.get(f"https://api.example.com/servers/{url}")
        response.raise_for_status()
        return response.json()

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse API response."""
        server = Server(
            name=data["name"],
            primary_url=data["url"],
            host_type=HostType.HTTP,
            description=data.get("description"),
        )

        # Add tools
        for tool_data in data.get("tools", []):
            tool = Tool(
                name=tool_data["name"],
                description=tool_data.get("description"),
            )
            server.tools.append(tool)

        # Calculate health score
        server.health_score = 50  # Simplified

        return server

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Store server with upsert logic."""
        # Implement upsert logic (see pattern above)
        pass
```

### Example 2: Using ServerUpdater

```python
from packages.harvester.core.updater import ServerUpdater

async def maintenance_task():
    """Run nightly maintenance."""
    async with async_session_maker() as session:
        updater = ServerUpdater(session)

        # Update health scores
        health_count = await updater.update_health_scores()
        logger.info(f"Updated health scores for {health_count} servers")

        # Update risk levels
        risk_count = await updater.update_risk_levels()
        logger.info(f"Updated risk levels for {risk_count} servers")

        # Prune stale servers
        pruned = await updater.prune_stale_servers(days=180)
        logger.info(f"Pruned {pruned} stale servers")
```

## Testing

### Test BaseHarvester Subclass

```python
import pytest
from packages.harvester.database import async_session_maker

@pytest.mark.asyncio
async def test_custom_harvester():
    """Test custom harvester implementation."""
    async with async_session_maker() as session:
        harvester = CustomHarvester(session)

        # Test fetch
        data = await harvester.fetch("test-url")
        assert data is not None

        # Test parse
        server = await harvester.parse(data)
        assert server.name is not None
        assert len(server.tools) > 0

        # Test store
        await harvester.store(server, session)

        # Verify stored
        result = await session.execute(
            select(Server).where(Server.primary_url == server.primary_url)
        )
        stored = result.scalar_one_or_none()
        assert stored is not None
```

## Common Tasks

### 1. Add Custom Checkpoint Logic

```python
class MyHarvester(BaseHarvester):
    async def harvest(self, url: str) -> Optional[Server]:
        """Override harvest with custom checkpointing."""
        # Custom pre-processing
        logger.info(f"Custom checkpoint: {url}")

        # Call parent harvest
        return await super().harvest(url)
```

### 2. Implement Retry with Custom Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def fetch_with_custom_retry(self, url: str) -> Dict[str, Any]:
    """Fetch with custom retry configuration."""
    # Implementation
    pass
```

### 3. Add Health Score Calculation

```python
def _calculate_health_score(
    self,
    has_docs: bool,
    has_tests: bool,
    activity_score: int,
) -> int:
    """Calculate custom health score."""
    score = 0

    if has_docs:
        score += 30

    if has_tests:
        score += 40

    score += min(30, activity_score)

    return score
```

## Related Areas

- **Adapters:** See `packages/harvester/adapters/AGENTS.md` for adapter implementations
- **Models:** See `packages/harvester/models/models.py` for full entity schemas
- **Database:** See `packages/harvester/database.py` for session configuration
- **Parent Guide:** See `packages/harvester/AGENTS.md` for harvester system overview

## Constraints

### Never Skip Checkpointing
- Always let BaseHarvester.harvest() handle checkpointing
- Don't bypass _mark_processing_* methods
- Checkpoints prevent duplicate processing

### Use Proper Error Types
- Raise `HarvesterError` for harvester-specific errors
- Let other exceptions propagate for retry logic
- Log errors before raising

### Follow Async Patterns
- Use async/await consistently
- Don't mix sync and async code
- Use AsyncSession exclusively

## Troubleshooting

### Issue: harvest() Not Retrying
**Solution:** Ensure you're raising HarvesterError, not generic Exception

### Issue: Duplicate Processing
**Solution:** Check ProcessingLog table, verify checkpoint methods are called

### Issue: Session Not Committed
**Solution:** Explicitly call `await session.commit()` in store()

---

**Last Updated:** 2025-11-19
**See Also:** base_harvester.py source, PRD.md Section 4.1
