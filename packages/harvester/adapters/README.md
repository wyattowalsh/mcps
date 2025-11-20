# Harvester Adapters

This directory contains source-specific harvester adapters for the MCPS system. Each adapter implements the `BaseHarvester` interface to provide a consistent harvesting pipeline across different data sources.

## Available Adapters

### GitHubHarvester

**Status:** ✅ Implemented (Phase 2.2 Complete)

**Source:** `github.py`

**Purpose:** High-fidelity harvesting of MCP servers from GitHub repositories using GraphQL API.

#### Features

- **Efficient Data Fetching**: Uses a single GraphQL query to fetch:
  - Repository metadata (name, description, stars, forks, issues)
  - File contents (mcp.json, package.json, pyproject.toml, README.md)
  - Contributors (for bus factor calculation)
  - Recent releases (version history)

- **Comprehensive Parsing**:
  - Extracts MCP server definitions from `mcp.json`
  - Parses tools with full JSON schemas
  - Extracts resources and prompts
  - Analyzes dependencies from npm (package.json) or Python (pyproject.toml)
  - Creates contributor and release records

- **Intelligent Scoring**:
  - **Health Score** (0-100): Based on stars, forks, documentation, tests, activity
  - **Risk Level**: SAFE, MODERATE, HIGH, or CRITICAL based on verification and dependencies
  - **Bus Factor**: Calculated from contributor distribution

- **Resilient Operation**:
  - Automatic retry logic with exponential backoff
  - Graceful handling of missing files
  - Checkpoint system for resumable processing
  - Comprehensive error logging

#### Usage

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from packages.harvester.adapters import GitHubHarvester

# Initialize with async session
async with AsyncSession(engine) as session:
    harvester = GitHubHarvester(session)

    # Harvest a repository
    server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")

    print(f"Name: {server.name}")
    print(f"Stars: {server.stars}")
    print(f"Health Score: {server.health_score}/100")
    print(f"Risk Level: {server.risk_level.value}")
    print(f"Tools: {len(server.tools)}")
```

#### Authentication

The harvester uses the `GITHUB_TOKEN` environment variable for authentication:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Rate Limits:**
- Without token: 60 requests/hour
- With token: 5,000 requests/hour

#### GraphQL Query

The harvester executes an optimized GraphQL query that fetches all required data in a single API call:

```graphql
query GetRepoData($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    name
    description
    stargazerCount
    forkCount

    # Fetch configuration files
    mcpJson: object(expression: "HEAD:mcp.json") { text }
    packageJson: object(expression: "HEAD:package.json") { text }
    pyprojectToml: object(expression: "HEAD:pyproject.toml") { text }
    readme: object(expression: "HEAD:README.md") { text }

    # Get contributors
    mentionableUsers(first: 10) {
      nodes { login }
    }

    # Get releases
    releases(first: 5) {
      nodes {
        tagName
        publishedAt
        description
      }
    }
  }
}
```

#### Health Score Algorithm

The health score (0-100) is calculated based on multiple factors:

| Factor | Points | Description |
|--------|--------|-------------|
| Base Score | 20 | Starting baseline |
| Stars | 0-20 | Logarithmic scale (log10) |
| Forks | 0-10 | Logarithmic scale (log10) |
| README | 10 | Documentation present |
| License | 10 | License specified |
| Recent Activity | 15 | Commits within 6 months |
| Tests | 15 | Test indicators detected |
| Issue Management | 0-10 | Based on open issues count |

**Example Calculation:**
```python
# Repository with:
# - 1000 stars (+15 points)
# - 100 forks (+6 points)
# - README (+10 points)
# - MIT license (+10 points)
# - Recent commit (+15 points)
# - Test suite (+15 points)
# - 5 open issues (+10 points)
# = 20 + 15 + 6 + 10 + 10 + 15 + 15 + 10 = 101 → capped at 100
```

#### Risk Level Determination

| Scenario | Risk Level | Reasoning |
|----------|-----------|-----------|
| Official repo + safe deps | SAFE | Verified source, no security concerns |
| Official repo + dangerous deps | MODERATE | Verified but uses system access |
| Community repo + safe deps | MODERATE | Unverified but limited capabilities |
| Community repo + dangerous deps | HIGH | Unverified with system access |

**Dangerous Dependencies:**
- **NPM**: `child_process`, `shelljs`, `execa`
- **Python**: `subprocess`, `os`, `sys`, `shutil`

#### Error Handling

The harvester handles various error scenarios gracefully:

1. **Invalid URLs**: Validates GitHub URL format
2. **Repository Not Found**: Returns clear error message
3. **Missing Files**: Continues processing with available data
4. **Malformed JSON**: Logs warning and skips parsing
5. **API Rate Limits**: Automatic retry with exponential backoff
6. **Network Errors**: Tenacity retry logic (5 attempts)

#### Database Operations

The `store()` method implements upsert logic:

1. Check if server exists by `primary_url`
2. If exists:
   - Update all scalar fields
   - Replace all related entities (tools, dependencies, etc.)
   - Preserve UUID and creation timestamp
3. If new:
   - Insert server with all relationships
4. Commit transaction or rollback on error

#### Testing

Comprehensive test suite in `tests/test_github_harvester.py`:

```bash
# Run tests
uv run pytest tests/test_github_harvester.py -v

# Run specific test
uv run pytest tests/test_github_harvester.py::TestGitHubHarvester::test_calculate_health_score -v
```

**Test Coverage:**
- URL parsing (valid and invalid)
- Health score calculation
- Risk level determination
- Dependency detection
- File parsing (mcp.json, package.json, pyproject.toml)
- Full integration test with mock GraphQL response

#### Future Enhancements

Planned improvements for future phases:

1. **Pagination**: Handle repositories with >100 contributors
2. **AST Analysis**: Deep code scanning for security patterns
3. **Caching**: Store GraphQL responses to reduce API calls
4. **Embeddings**: Generate semantic vectors for tools/resources
5. **Change Detection**: Only update if repository changed since last harvest
6. **Parallel Processing**: Batch process multiple repositories concurrently

## Implementation Checklist

Based on TASKS.md Phase 2.2:

- [x] Create `packages/harvester/adapters/github.py`
- [x] Implement `GitHubHarvester` class extending `BaseHarvester`
- [x] Implement `fetch()` method with GraphQL query
- [x] Implement `parse()` method transforming data to Server model
- [x] Implement `store()` method with upsert logic
- [x] GraphQL query fetching mcp.json, package.json, pyproject.toml
- [x] GraphQL query fetching stars, contributors, releases
- [x] Handle pagination with hasNextPage
- [x] Extract MCP server definitions from mcp.json
- [x] Parse tools with input schemas
- [x] Parse resources with URI templates
- [x] Parse prompts with arguments
- [x] Extract contributors for bus factor
- [x] Calculate health_score (0-100)
- [x] Determine risk_level based on verification
- [x] Handle missing files gracefully
- [x] Use GITHUB_TOKEN environment variable
- [x] Use http_client utility
- [x] Use loguru for logging
- [x] Import models from packages.harvester.models
- [x] Use async/await patterns
- [x] Full type hints
- [x] Comprehensive error handling
- [x] Parse owner/repo from GitHub URLs
- [x] Set host_type=HostType.GITHUB
- [x] Create related Tool, Contributor, Release records
- [x] Export GitHubHarvester from `__init__.py`
- [x] Create comprehensive test suite
- [x] Create usage examples
- [x] Document implementation

## Architecture Compliance

This implementation adheres to:

- **PRD Section 4.1**: "Strategy A: GitHub Strategy (High Fidelity)"
- **TASKS.md Phase 2.2**: Lines 221-238
- **BaseHarvester Interface**: Abstract methods implemented
- **Data Models**: Uses SQLModel entities from `packages.harvester.models`
- **HTTP Client**: Uses shared `http_client` utility
- **Error Handling**: Tenacity retry logic and checkpointing
- **Type Safety**: Full type hints with mypy compliance
- **Logging**: Structured logging with loguru

## Next Steps

After implementing GitHubHarvester, the following adapters are planned:

1. **NPMHarvester** (Phase 2.3): Strategy B - Registry/Artifact Strategy
2. **PyPIHarvester** (Phase 2.3): Strategy B - Registry/Artifact Strategy
3. **DockerHarvester** (Phase 2.4): Strategy C - Container Inspection
4. **HTTPHarvester** (Phase 2.5): Strategy D - Generic HTTP/SSE

Each adapter will follow the same pattern established by GitHubHarvester.
