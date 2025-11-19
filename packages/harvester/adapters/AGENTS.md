# AGENTS.md - Adapter Implementation Guide

## Context

The `packages/harvester/adapters/` directory contains source-specific harvester implementations. Each adapter inherits from `BaseHarvester` and implements the polymorphic strategy pattern described in PRD.md Section 4.1.

**Purpose:** Enable data ingestion from heterogeneous sources (GitHub, NPM, PyPI, Docker Hub, HTTP endpoints) using a unified interface.

**Architecture:** Each adapter implements fetch -> parse -> store lifecycle with automatic retry, checkpointing, and error handling.

## Key Files

| File | Strategy | Fidelity | Primary Use Case |
|------|----------|----------|------------------|
| `github.py` | GitHub GraphQL API | High | Official/community GitHub repos |
| `npm.py` | NPM Registry API | Medium | Package-only servers (no GitHub) |
| `pypi.py` | PyPI JSON API | Medium | Python package servers |
| `docker.py` | Docker Registry v2 | Medium | Containerized servers |
| `http.py` | Generic HTTP/SSE | Low | Direct endpoint servers |

## Patterns

### 1. Polymorphic Strategy Pattern

All adapters must implement three methods:

```python
class MyAdapter(BaseHarvester):
    async def fetch(self, url: str) -> Dict[str, Any]:
        """
        Retrieve raw data from source.
        - Make API calls
        - Download artifacts
        - Return unprocessed data
        """
        pass

    async def parse(self, data: Dict[str, Any]) -> Server:
        """
        Transform raw data into Server model.
        - Extract metadata
        - Parse MCP configuration
        - Calculate health score
        - Determine risk level
        - Populate tools, resources, prompts, dependencies
        """
        pass

    async def store(self, server: Server, session: AsyncSession) -> None:
        """
        Persist server to database.
        - Check for existing server (upsert logic)
        - Update or create new record
        - Handle related entities (cascade updates)
        """
        pass
```

### 2. URL Parsing Convention

Each adapter should validate and parse its specific URL format:

```python
def _parse_url(self, url: str) -> tuple:
    """Extract relevant components from source URL.

    Examples:
        GitHub: https://github.com/owner/repo -> (owner, repo)
        NPM: https://npmjs.com/package/@scope/name -> (@scope/name,)
        PyPI: https://pypi.org/project/package-name -> (package-name,)
    """
    # Validation logic
    # URL parsing
    # Return tuple of components
```

### 3. Health Score Calculation

Each adapter implements health scoring based on available metrics:

```python
def _calculate_health_score(
    self,
    stars: int = 0,
    downloads: int = 0,
    has_readme: bool = False,
    has_license: bool = False,
    has_recent_activity: bool = False,
    has_tests: bool = False,
    open_issues: int = 0,
) -> int:
    """Calculate 0-100 health score.

    Formula (GitHub):
        - Base: 20 points
        - Stars: 0-20 (logarithmic)
        - Forks: 0-10 (logarithmic)
        - README: 10 points
        - License: 10 points
        - Recent activity: 15 points
        - Tests: 15 points
        - Low issues: 0-10 (inverse)
    """
    score = 20  # Base score
    # Add scoring logic
    return min(100, score)
```

### 4. Risk Level Determination

Risk level based on verification and dependencies:

```python
def _determine_risk_level(self, is_official: bool, has_dangerous_deps: bool) -> RiskLevel:
    """Determine risk level.

    Logic:
        - Official + no dangerous deps = SAFE
        - Official + dangerous deps = MODERATE
        - Unofficial + dangerous deps = HIGH
        - Unofficial + no dangerous deps = MODERATE
    """
    if is_official:
        return RiskLevel.MODERATE if has_dangerous_deps else RiskLevel.SAFE

    return RiskLevel.HIGH if has_dangerous_deps else RiskLevel.MODERATE
```

### 5. Dependency Extraction

Parse package manifests for dependencies:

```python
def _parse_dependencies(self, manifest: str) -> List[Dependency]:
    """Extract dependencies from package manifest.

    Supported formats:
        - package.json (npm)
        - pyproject.toml (Python)
        - Cargo.toml (Rust)
        - go.mod (Go)
    """
    dependencies = []
    # Parsing logic
    return dependencies
```

## URL Parsing Conventions

### GitHub URLs
```python
# Accepted formats:
https://github.com/owner/repo
https://github.com/owner/repo.git
github.com/owner/repo
git@github.com:owner/repo.git

# Parse to: (owner, repo)
def _parse_github_url(self, url: str) -> tuple[str, str]:
    # Remove protocol, .git extension
    # Split on '/' to extract owner and repo
    # Validate format
```

### NPM Package Names
```python
# Accepted formats:
@scope/package-name
package-name
https://npmjs.com/package/@scope/package-name

# Parse to: package identifier
def _parse_npm_package(self, identifier: str) -> str:
    # Extract package name from URL or use as-is
    # Validate package name format
```

### PyPI Package Names
```python
# Accepted formats:
package-name
package_name
https://pypi.org/project/package-name/

# Parse to: normalized package name
def _parse_pypi_package(self, identifier: str) -> str:
    # Normalize underscores/hyphens
    # Extract from URL if needed
```

### Docker Images
```python
# Accepted formats:
org/image:tag
registry.com/org/image:tag
image:tag

# Parse to: (registry, org, image, tag)
def _parse_docker_image(self, identifier: str) -> tuple:
    # Split on '/', ':' to extract components
    # Default registry to docker.io
```

## Examples of Good Adapter Code

### Example 1: GitHub GraphQL Fetching

```python
async def fetch(self, url: str) -> Dict[str, Any]:
    """Fetch using GitHub GraphQL API (single request for all data)."""
    owner, repo = self._parse_github_url(url)

    client = get_client()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.github_token}",
    }

    response = await client.post(
        "https://api.github.com/graphql",
        json={
            "query": self.GRAPHQL_QUERY,
            "variables": {"owner": owner, "repo": repo},
        },
        headers=headers,
    )

    response.raise_for_status()
    data = response.json()

    # Check for GraphQL errors
    if "errors" in data:
        raise HarvesterError(f"GraphQL error: {data['errors'][0]['message']}")

    return data["data"]["repository"]
```

### Example 2: NPM Registry Parsing

```python
async def parse(self, data: Dict[str, Any]) -> Server:
    """Parse NPM registry response."""
    # Extract package.json from latest version
    latest_version = data.get("dist-tags", {}).get("latest")
    version_data = data.get("versions", {}).get(latest_version, {})

    server = Server(
        name=data.get("name"),
        primary_url=f"npm://{data.get('name')}",
        host_type=HostType.NPM,
        description=version_data.get("description"),
        author_name=self._extract_author(version_data.get("author")),
        license=version_data.get("license"),
        downloads=data.get("downloads", 0),
    )

    # Parse dependencies
    deps = version_data.get("dependencies", {})
    for lib_name, version_constraint in deps.items():
        dep = Dependency(
            library_name=lib_name,
            version_constraint=version_constraint,
            ecosystem="npm",
            type="runtime",
        )
        server.dependencies.append(dep)

    # Calculate health score
    server.health_score = self._calculate_health_score(
        downloads=server.downloads,
        has_readme=bool(data.get("readme")),
        has_license=bool(server.license),
    )

    return server
```

### Example 3: Upsert Logic in Store

```python
async def store(self, server: Server, session: AsyncSession) -> None:
    """Store or update server with upsert logic."""
    # Check if server exists
    statement = select(Server).where(Server.primary_url == server.primary_url)
    result = await session.execute(statement)
    existing_server = result.scalar_one_or_none()

    if existing_server:
        # Update existing server
        logger.info(f"Updating existing server: {server.name}")

        # Update scalar fields
        for field in ["name", "description", "stars", "forks", "health_score"]:
            setattr(existing_server, field, getattr(server, field))

        existing_server.updated_at = datetime.utcnow()

        # Replace related entities
        existing_server.tools.clear()
        existing_server.dependencies.clear()

        for tool in server.tools:
            tool.server_id = existing_server.id
            existing_server.tools.append(tool)

        session.add(existing_server)
    else:
        # Create new server
        logger.info(f"Creating new server: {server.name}")
        session.add(server)

    await session.commit()
```

## Testing Adapters

### Test Structure

```python
# tests/test_adapters/test_github.py
import pytest
from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.database import async_session_maker

@pytest.mark.asyncio
async def test_github_url_parsing():
    """Test URL parsing logic."""
    harvester = GitHubHarvester(None)

    owner, repo = harvester._parse_github_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"

@pytest.mark.asyncio
async def test_github_harvest():
    """Test full harvest workflow."""
    async with async_session_maker() as session:
        harvester = GitHubHarvester(session)

        # Use a known test repository or mock
        server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")

        assert server is not None
        assert server.host_type == "github"
        assert server.health_score > 0
```

### Mocking External APIs

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_github_fetch_with_mock():
    """Test fetch with mocked API response."""
    mock_response = {
        "data": {
            "repository": {
                "name": "test-repo",
                "description": "Test description",
                "stargazerCount": 100,
            }
        }
    }

    async with async_session_maker() as session:
        harvester = GitHubHarvester(session)

        with patch("packages.harvester.utils.http_client.get_client") as mock_client:
            mock_client.return_value.post = AsyncMock(
                return_value=AsyncMock(
                    json=lambda: mock_response,
                    raise_for_status=lambda: None
                )
            )

            data = await harvester.fetch("https://github.com/owner/repo")
            assert data["name"] == "test-repo"
```

## Common Tasks

### 1. Add New Data Source

**Steps:**
1. Create new adapter file (e.g., `gitlab.py`)
2. Inherit from `BaseHarvester`
3. Implement fetch(), parse(), store()
4. Add URL parsing method
5. Add health score calculation
6. Add to HARVESTERS dict in `cli.py`
7. Write tests

### 2. Enhance Existing Adapter

**Common enhancements:**
- Add more metadata fields
- Improve health score formula
- Extract additional MCP capabilities
- Add better error handling
- Optimize API usage (reduce requests)

### 3. Handle Rate Limiting

```python
from packages.harvester.utils.http_client import get_client

# HTTP client automatically handles retries
client = get_client()  # Has built-in retry logic

# For custom rate limiting:
import asyncio

async def fetch_with_rate_limit(self, url: str):
    await asyncio.sleep(1)  # Simple rate limiting
    # Or use more sophisticated rate limiter
```

## Constraints

### 1. Never Execute Untrusted Code
```python
# NEVER do this:
# import downloaded_module  # DANGEROUS!

# ALWAYS do this:
import ast
tree = ast.parse(code_string)
# Analyze AST safely
```

### 2. Always Handle Errors
```python
try:
    data = await self.fetch(url)
except HTTPClientError as e:
    raise HarvesterError(f"Failed to fetch: {str(e)}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HarvesterError(f"Unexpected error: {str(e)}") from e
```

### 3. Respect API Limits
```python
# Check rate limit headers
if response.headers.get("X-RateLimit-Remaining") == "0":
    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
    wait_time = reset_time - time.time()
    logger.warning(f"Rate limited. Waiting {wait_time}s")
    await asyncio.sleep(wait_time)
```

### 4. Validate Input URLs
```python
def _parse_github_url(self, url: str) -> tuple[str, str]:
    parsed = urlparse(url)

    if parsed.netloc not in ("github.com", "www.github.com"):
        raise HarvesterError(f"Not a valid GitHub URL: {url}")

    path_parts = [p for p in parsed.path.split("/") if p]
    if len(path_parts) < 2:
        raise HarvesterError(f"Invalid GitHub URL format: {url}")

    return path_parts[0], path_parts[1]
```

## Related Areas

- **Base Harvester:** See `packages/harvester/core/AGENTS.md` for BaseHarvester details
- **Analysis:** See `packages/harvester/analysis/AGENTS.md` for security analysis integration
- **Models:** See `packages/harvester/models/models.py` for Server entity structure
- **Parent Guide:** See `packages/harvester/AGENTS.md` for harvester system overview

## Performance Tips

1. **Batch API calls** - Use GraphQL or batch endpoints when available
2. **Cache responses** - Use ProcessingLog to avoid re-fetching
3. **Concurrent harvesting** - Use asyncio.gather() for multiple URLs
4. **Minimize downloads** - Only download artifacts when necessary
5. **Stream large files** - Don't load entire files into memory

## Troubleshooting

### Issue: GraphQL Errors
**Solution:** Check token permissions, query syntax, and rate limits

### Issue: Package Not Found
**Solution:** Verify package name, check for typos, ensure package is public

### Issue: Timeout Errors
**Solution:** Increase timeout in http_client, check network connectivity

### Issue: Inconsistent Data
**Solution:** Add validation in parse(), handle missing fields gracefully

---

**Last Updated:** 2025-11-19
**See Also:** BaseHarvester documentation, PRD.md Section 4.1
