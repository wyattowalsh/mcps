# AGENTS.md - Adapter Implementation Guide

## Context

The `packages/harvester/adapters/` directory contains source-specific harvester implementations. Each adapter inherits from `BaseHarvester` and implements the polymorphic strategy pattern described in PRD.md Section 4.1.

**Purpose:** Enable data ingestion from heterogeneous sources including code repositories (GitHub, NPM, PyPI, Docker, HTTP) and social media platforms (Reddit, Twitter, YouTube).

**Architecture:** Each adapter implements fetch -> parse -> store lifecycle with automatic retry, checkpointing, and error handling.

## Key Files

### Code Repository Adapters

| File | Strategy | Fidelity | Primary Use Case |
|------|----------|----------|------------------|
| `github.py` | GitHub GraphQL API | High | Official/community GitHub repos |
| `npm.py` | NPM Registry API | Medium | Package-only servers (no GitHub) |
| `pypi.py` | PyPI JSON API | Medium | Python package servers |
| `docker.py` | Docker Registry v2 | Medium | Containerized servers |
| `http.py` | Generic HTTP/SSE | Low | Direct endpoint servers |

### Social Media Adapters (NEW in Phase 11)

| File | Platform | API | Primary Use Case |
|------|----------|-----|------------------|
| `reddit.py` | Reddit | PRAW (Reddit API) | Community discussions, questions, announcements |
| `twitter.py` | Twitter/X | Tweepy (Twitter API v2) | Real-time mentions, hashtags, threads |
| `youtube.py` | YouTube | Google API Client (YouTube Data API v3) | Tutorials, demos, educational content |

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

## Social Media Adapters (Phase 11 Implementation)

Social media adapters differ from code repository adapters in that they:
1. Return **lists** of social content (posts, videos) rather than single Server objects
2. Use **sentiment analysis** and **quality scoring** algorithms
3. **Link content to servers** by extracting and matching URLs
4. Work with **synchronous APIs** that must be wrapped in asyncio.to_thread()

### Reddit Adapter (`reddit.py`)

**Purpose:** Track MCP discussions across programming subreddits

**Key Methods:**
```python
async def fetch(self, url: str) -> dict[str, Any]:
    """Fetch posts from a subreddit.

    Args:
        url: Subreddit name (e.g., "r/LocalLLaMA" or "LocalLLaMA")

    Returns:
        {"subreddit": str, "posts": list[dict]}
    """
    # Uses PRAW (synchronous) wrapped in asyncio.to_thread()
    # Filters posts using MCP keyword regex patterns
    # Extracts post metadata, scores, comments

async def parse(self, data: dict[str, Any]) -> list[SocialPost]:
    """Parse Reddit data into SocialPost models.

    Returns:
        List of SocialPost objects with:
        - Sentiment analysis (VADER)
        - Category classification (tutorial, question, etc.)
        - Quality scoring (0-100 based on engagement)
        - Relevance scoring (0.0-1.0)
    """

async def harvest(self, session: AsyncSession) -> dict[str, Any]:
    """Harvest from all configured subreddits.

    Iterates through config.subreddits list and processes each.
    """
```

**Configuration:**
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - API credentials
- `REDDIT_SUBREDDITS` - Comma-separated subreddit list
- `REDDIT_KEYWORDS` - Comma-separated keyword list
- `REDDIT_MIN_SCORE_THRESHOLD` - Minimum upvotes to store

**Sentiment Analysis:**
Uses VADER (Valence Aware Dictionary and sEntiment Reasoner):
```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
scores = analyzer.polarity_scores(text)
compound = scores["compound"]  # -1.0 to 1.0
```

**URL Extraction & Server Linking:**
```python
# Extract GitHub/NPM/PyPI URLs from post text
mentioned_urls = self._extract_urls(text)

# Find matching servers in database
for url in mentioned_urls:
    result = await session.execute(
        select(Server).where(Server.primary_url.contains(url))
    )
    server = result.scalar_one_or_none()
    if server:
        mentioned_server_ids.append(server.id)
```

### Twitter Adapter (`twitter.py`)

**Purpose:** Track real-time MCP mentions and hashtags

**Key Methods:**
```python
async def fetch(self, url: str) -> dict[str, Any]:
    """Search Twitter for MCP-related tweets.

    Args:
        url: Search query (e.g., "Model Context Protocol")

    Returns:
        {"query": str, "tweets": list[dict]}
    """
    # Uses Tweepy Client (synchronous) wrapped in asyncio.to_thread()
    # Twitter API v2 recent search endpoint
    # Extracts tweet text, author, engagement metrics
    # Parses hashtags, mentions, URLs from entities
```

**Configuration:**
- `TWITTER_BEARER_TOKEN` - Twitter API v2 bearer token (required)
- `TWITTER_API_KEY` / `TWITTER_API_SECRET` - Optional for OAuth
- `TWITTER_SEARCH_QUERIES` - Comma-separated query list
- `TWITTER_MAX_RESULTS_PER_QUERY` - 10-100 tweets per query
- `TWITTER_MIN_LIKES_THRESHOLD` - Minimum likes to store

**Engagement Metrics:**
Twitter provides rich engagement data:
- `like_count` - Number of likes
- `retweet_count` - Number of retweets
- `reply_count` - Number of replies
- `quote_count` - Number of quote tweets
- `impression_count` - Total views (if available)

**Category Classification:**
```python
def _categorize_tweet(self, tweet_data: dict) -> ContentCategory:
    text = tweet_data["text"].lower()

    if "tutorial" in text or "how to" in text:
        return ContentCategory.TUTORIAL
    elif "announcing" in text or "released" in text:
        return ContentCategory.ANNOUNCEMENT
    elif "?" in text:
        return ContentCategory.QUESTION
    # ... more classification logic
```

### YouTube Adapter (`youtube.py`)

**Purpose:** Discover MCP tutorials and demonstration videos

**Key Methods:**
```python
async def fetch(self, url: str) -> dict[str, Any]:
    """Search YouTube for MCP-related videos.

    Args:
        url: Search query (e.g., "MCP tutorial")

    Returns:
        {"query": str, "videos": list[dict]}
    """
    # Uses Google API Client (synchronous) wrapped in asyncio.to_thread()
    # YouTube Data API v3 search.list endpoint
    # Fetches detailed statistics via videos.list endpoint
    # Parses ISO 8601 duration format
```

**Configuration:**
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `YOUTUBE_SEARCH_QUERIES` - Comma-separated query list
- `YOUTUBE_MAX_RESULTS_PER_QUERY` - Max videos per query
- `YOUTUBE_MIN_VIEW_COUNT` - Minimum views to store
- `YOUTUBE_ORDER_BY` - relevance, date, viewCount, or rating

**Educational Value Scoring:**
```python
def _calculate_educational_value(self, video_data: dict) -> int:
    """Calculate educational value (0-100)."""
    score = 0

    # Tutorial indicators in title
    if "tutorial" in title or "guide" in title:
        score += 30

    # Has captions (accessibility)
    if video_data["caption"] == "true":
        score += 20

    # Ideal length (10-30 minutes)
    if 600 <= duration <= 1800:
        score += 20

    # Contains resource links
    if has_urls_in_description:
        score += 15

    # Educational tags
    if has_educational_tags:
        score += 15

    return min(100, score)
```

**Duration Parsing:**
YouTube returns ISO 8601 durations (e.g., "PT15M30S"):
```python
def _parse_duration(self, duration_str: str) -> int:
    """Parse ISO 8601 duration to seconds."""
    # PT1H30M15S -> 1 hour, 30 minutes, 15 seconds
    pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
    match = pattern.match(duration_str)
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds
```

### Common Patterns for Social Media Adapters

#### 1. Wrapping Synchronous APIs
Social media libraries are synchronous, so wrap them:
```python
async def fetch(self, url: str) -> dict:
    if not self.client:
        self.client = await asyncio.to_thread(self._init_client)

    def _fetch_data():
        # Synchronous API calls here
        return data

    return await asyncio.to_thread(_fetch_data)
```

#### 2. Quality Scoring Algorithm
```python
def _calculate_quality(self, data: dict) -> int:
    """Score 0-100 based on engagement."""
    score = 0

    # Primary engagement (40 points)
    if data["primary_metric"] > threshold_high:
        score += 40
    elif data["primary_metric"] > threshold_medium:
        score += 30
    # ... more tiers

    # Secondary engagement (30 points)
    # Engagement ratio (30 points)

    return min(100, score)
```

#### 3. Relevance Scoring
```python
def _calculate_relevance(self, data: dict) -> float:
    """Score 0.0-1.0 for MCP relevance."""
    score = 0.0

    # Direct mentions (0.6 max)
    if "model context protocol" in text.lower():
        score += 0.6
    elif "mcp" in text.lower():
        score += 0.3

    # Contains relevant links (0.2 max)
    if has_github_npm_pypi_urls:
        score += 0.2

    # High engagement = likely relevant (0.2 max)
    if engagement > threshold:
        score += 0.2

    return min(1.0, score)
```

### Testing Social Media Adapters

**Mock API Responses:**
```python
@pytest.mark.asyncio
async def test_reddit_parse():
    """Test Reddit post parsing."""
    harvester = RedditHarvester()

    mock_data = {
        "subreddit": "LocalLLaMA",
        "posts": [{
            "id": "abc123",
            "title": "New MCP server for...",
            "selftext": "Check out my new...",
            "score": 150,
            "num_comments": 20,
            # ... more fields
        }]
    }

    posts = await harvester.parse(mock_data)

    assert len(posts) == 1
    assert posts[0].platform == SocialPlatform.REDDIT
    assert posts[0].quality_score > 0
```

**Integration Testing:**
Use real APIs with test queries to validate:
```bash
# Test Reddit adapter
uv run python -m packages.harvester.cli harvest-social --platform reddit

# Check database for stored posts
sqlite3 data/mcps.db "SELECT count(*) FROM social_posts WHERE platform='reddit';"
```

## Related Areas

- **Base Harvester:** See `packages/harvester/core/AGENTS.md` for BaseHarvester details
- **Analysis:** See `packages/harvester/analysis/AGENTS.md` for security analysis integration
- **Models:** See `packages/harvester/models/models.py` for Server entity structure
- **Social Models:** See `packages/harvester/models/social.py` for SocialPost, Video, Article entities
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
