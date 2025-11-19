"""FastAPI application for MCPS API.

This module provides a RESTful API for the MCPS system with:
- CRUD endpoints for all entities
- Admin endpoints for maintenance operations
- Full-text search
- Authentication and rate limiting
- CORS middleware
"""

import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Security,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from loguru import logger
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import and_, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.models import HostType, RiskLevel
from packages.harvester.core.updater import ServerUpdater, UpdateError, ValidationError
from packages.harvester.database import async_session_maker, close_db, health_check, init_db
from packages.harvester.models.models import (
    Dependency,
    Prompt,
    ResourceTemplate,
    Server,
    Tool,
)
from packages.harvester.models.social import (
    Article,
    ArticlePlatform,
    ContentCategory,
    SentimentScore,
    SocialPlatform,
    SocialPost,
    Video,
    VideoPlatform,
)

# Initialize FastAPI app
app = FastAPI(
    title="MCPS API",
    description="Model Context Protocol Server (MCPS) API for querying and managing MCP ecosystem data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In production, store this securely (environment variable, secrets manager, etc.)
VALID_API_KEYS = {
    "dev_key_12345": "development",
    "admin_key_67890": "admin",
}


# --- Pydantic Models ---


class ServerResponse(BaseModel):
    """Response model for server data."""

    id: int
    uuid: str
    name: str
    primary_url: str
    host_type: str
    description: Optional[str] = None
    author_name: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    keywords: List[str] = []
    categories: List[str] = []
    stars: int
    downloads: int
    forks: int
    open_issues: int
    risk_level: str
    verified_source: bool
    health_score: int
    last_indexed_at: datetime
    created_at: datetime
    updated_at: datetime


class ServerUpdate(BaseModel):
    """Request model for server updates."""

    name: Optional[str] = None
    description: Optional[str] = None
    author_name: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    stars: Optional[int] = None
    downloads: Optional[int] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    risk_level: Optional[str] = None
    verified_source: Optional[bool] = None
    health_score: Optional[int] = None


class BulkUpdateRequest(BaseModel):
    """Request model for bulk updates."""

    filters: Dict[str, Any] = Field(..., description="Filter conditions")
    updates: Dict[str, Any] = Field(..., description="Fields to update")


class RefreshRequest(BaseModel):
    """Request model for server refresh."""

    url: str = Field(..., description="Primary URL of server to refresh")


class PruneRequest(BaseModel):
    """Request model for pruning stale servers."""

    days: int = Field(180, ge=1, description="Days of inactivity before pruning")


class SocialPostResponse(BaseModel):
    """Response model for social media posts."""

    id: int
    uuid: str
    platform: str
    post_id: str
    url: str
    title: Optional[str] = None
    content: str
    author: str
    author_url: Optional[str] = None
    score: int
    comment_count: int
    share_count: int
    view_count: Optional[int] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    language: str
    mentioned_servers: List[int] = []
    mentioned_urls: List[str] = []
    platform_created_at: datetime
    subreddit: Optional[str] = None  # Reddit-specific
    twitter_hashtags: List[str] = []  # Twitter-specific
    relevance_score: Optional[float] = None
    quality_score: Optional[int] = None
    created_at: datetime


class VideoResponse(BaseModel):
    """Response model for videos."""

    id: int
    uuid: str
    platform: str
    video_id: str
    url: str
    title: str
    description: str
    channel: str
    channel_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    language: str
    view_count: int
    like_count: int
    comment_count: int
    category: Optional[str] = None
    tags: List[str] = []
    mentioned_servers: List[int] = []
    mentioned_urls: List[str] = []
    has_captions: bool
    published_at: datetime
    relevance_score: Optional[float] = None
    quality_score: Optional[int] = None
    educational_value: Optional[int] = None
    created_at: datetime


class ArticleResponse(BaseModel):
    """Response model for articles."""

    id: int
    uuid: str
    platform: str
    article_id: Optional[str] = None
    url: str
    title: str
    subtitle: Optional[str] = None
    excerpt: Optional[str] = None
    author: str
    author_url: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    language: str
    view_count: Optional[int] = None
    like_count: int
    comment_count: int
    reading_time_minutes: Optional[int] = None
    mentioned_servers: List[int] = []
    mentioned_urls: List[str] = []
    published_at: datetime
    relevance_score: Optional[float] = None
    quality_score: Optional[int] = None
    technical_depth: Optional[int] = None
    created_at: datetime


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: int
    server_id: int
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class SearchResponse(BaseModel):
    """Response model for search results."""

    servers: List[ServerResponse]
    tools: List[ToolResponse]
    total: int


# --- Dependency Functions ---


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key and return user role.

    Args:
        api_key: API key from header

    Returns:
        User role (development, admin, etc.)

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return VALID_API_KEYS[api_key]


async def verify_admin(role: str = Depends(verify_api_key)) -> str:
    """Verify user has admin role.

    Args:
        role: User role from API key verification

    Returns:
        User role

    Raises:
        HTTPException: If user is not admin
    """
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return role


# --- Startup/Shutdown Events ---


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    logger.info("Starting MCPS API...")
    await init_db()
    logger.success("MCPS API started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down MCPS API...")
    await close_db()
    logger.success("MCPS API shutdown complete")


# --- Health Check ---


@app.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check_api():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/db", tags=["Health"])
@limiter.limit("100/minute")
async def health_check_database():
    """Database health check endpoint with connection pool statistics.

    Returns:
        Database health information including:
        - Connection status
        - Query latency
        - Connection pool statistics (PostgreSQL only)
        - Database type and version

    Raises:
        HTTPException: If database is unhealthy
    """
    try:
        health_info = await health_check()

        if not health_info.get("healthy"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database unhealthy: {health_info.get('error', 'Unknown error')}",
            )

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": health_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}",
        )


# --- Server Endpoints ---


@app.get("/servers", response_model=List[ServerResponse], tags=["Servers"])
@limiter.limit("60/minute")
async def list_servers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    host_type: Optional[str] = Query(None, description="Filter by host type"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    verified_only: bool = Query(False, description="Show only verified sources"),
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """List servers with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        host_type: Filter by host type
        risk_level: Filter by risk level
        verified_only: Show only verified sources
        session: Database session
        _role: User role (from API key)

    Returns:
        List of servers
    """
    logger.info(f"Listing servers: skip={skip}, limit={limit}")

    # Build query
    query = select(Server)

    # Apply filters
    conditions = []
    if host_type:
        conditions.append(Server.host_type == host_type)
    if risk_level:
        conditions.append(Server.risk_level == risk_level)
    if verified_only:
        conditions.append(Server.verified_source == True)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await session.execute(query)
    servers = result.scalars().all()

    return [ServerResponse(**server.model_dump()) for server in servers]


@app.get("/servers/{server_id}", response_model=ServerResponse, tags=["Servers"])
@limiter.limit("60/minute")
async def get_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Get server details by ID.

    Args:
        server_id: Server ID
        session: Database session
        _role: User role (from API key)

    Returns:
        Server details

    Raises:
        HTTPException: If server not found
    """
    logger.info(f"Getting server {server_id}")

    result = await session.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    return ServerResponse(**server.model_dump())


@app.put("/servers/{server_id}", response_model=ServerResponse, tags=["Servers"])
@limiter.limit("30/minute")
async def update_server(
    server_id: int,
    updates: ServerUpdate,
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Update server by ID.

    Args:
        server_id: Server ID
        updates: Fields to update
        session: Database session
        _role: User role (from API key)

    Returns:
        Updated server

    Raises:
        HTTPException: If server not found or update fails
    """
    logger.info(f"Updating server {server_id}")

    updater = ServerUpdater(session)

    try:
        # Convert to dict, excluding None values
        update_dict = updates.model_dump(exclude_none=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        server = await updater.update_server(server_id, update_dict)

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server {server_id} not found",
            )

        return ServerResponse(**server.model_dump())

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.delete("/servers/{server_id}", tags=["Servers"])
@limiter.limit("20/minute")
async def delete_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Delete server by ID (admin only).

    Args:
        server_id: Server ID
        session: Database session
        role: User role (must be admin)

    Returns:
        Success message

    Raises:
        HTTPException: If server not found or delete fails
    """
    logger.info(f"Deleting server {server_id}")

    result = await session.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    await session.delete(server)
    await session.commit()

    logger.success(f"Deleted server {server_id}")
    return {"message": f"Server {server_id} deleted successfully"}


@app.post("/servers/refresh", response_model=ServerResponse, tags=["Servers"])
@limiter.limit("10/minute")
async def refresh_server(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Trigger re-harvest of a server.

    Args:
        request: Refresh request with URL
        session: Database session
        _role: User role (from API key)

    Returns:
        Refreshed server

    Raises:
        HTTPException: If server not found or refresh fails
    """
    logger.info(f"Refreshing server: {request.url}")

    updater = ServerUpdater(session)

    try:
        server = await updater.refresh_server(request.url)

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with URL {request.url} not found",
            )

        return ServerResponse(**server.model_dump())

    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# --- Tool Endpoints ---


@app.get("/tools", response_model=List[ToolResponse], tags=["Tools"])
@limiter.limit("60/minute")
async def list_tools(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    server_id: Optional[int] = Query(None, description="Filter by server ID"),
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """List tools with pagination.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        server_id: Filter by server ID
        session: Database session
        _role: User role (from API key)

    Returns:
        List of tools
    """
    logger.info(f"Listing tools: skip={skip}, limit={limit}")

    query = select(Tool)

    if server_id:
        query = query.where(Tool.server_id == server_id)

    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    tools = result.scalars().all()

    return [ToolResponse(**tool.model_dump()) for tool in tools]


# --- Search Endpoints ---


@app.get("/search", response_model=SearchResponse, tags=["Search"])
@limiter.limit("30/minute")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Max results per category"),
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Full-text search across servers and tools.

    Args:
        q: Search query
        limit: Max results per category
        session: Database session
        _role: User role (from API key)

    Returns:
        Search results
    """
    logger.info(f"Searching for: {q}")

    # Search servers
    server_query = (
        select(Server)
        .where(
            or_(
                Server.name.ilike(f"%{q}%"),
                Server.description.ilike(f"%{q}%"),
                Server.author_name.ilike(f"%{q}%"),
            )
        )
        .limit(limit)
    )
    server_result = await session.execute(server_query)
    servers = server_result.scalars().all()

    # Search tools
    tool_query = (
        select(Tool)
        .where(
            or_(
                Tool.name.ilike(f"%{q}%"),
                Tool.description.ilike(f"%{q}%"),
            )
        )
        .limit(limit)
    )
    tool_result = await session.execute(tool_query)
    tools = tool_result.scalars().all()

    return SearchResponse(
        servers=[ServerResponse(**s.model_dump()) for s in servers],
        tools=[ToolResponse(**t.model_dump()) for t in tools],
        total=len(servers) + len(tools),
    )


# --- Admin Endpoints ---


@app.post("/admin/update-health-scores", tags=["Admin"])
@limiter.limit("5/minute")
async def update_health_scores(
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Recalculate health scores for all servers (admin only).

    Args:
        session: Database session
        role: User role (must be admin)

    Returns:
        Update statistics
    """
    logger.info("Updating health scores")

    updater = ServerUpdater(session)

    try:
        count = await updater.update_health_scores()
        return {"message": f"Updated health scores for {count} servers"}
    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/admin/update-risk-levels", tags=["Admin"])
@limiter.limit("5/minute")
async def update_risk_levels(
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Recalculate risk levels for all servers (admin only).

    Args:
        session: Database session
        role: User role (must be admin)

    Returns:
        Update statistics
    """
    logger.info("Updating risk levels")

    updater = ServerUpdater(session)

    try:
        count = await updater.update_risk_levels()
        return {"message": f"Updated risk levels for {count} servers"}
    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/admin/prune-stale", tags=["Admin"])
@limiter.limit("5/minute")
async def prune_stale_servers(
    request: PruneRequest,
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Remove stale servers (admin only).

    Args:
        request: Prune request with days parameter
        session: Database session
        role: User role (must be admin)

    Returns:
        Prune statistics
    """
    logger.info(f"Pruning stale servers (>{request.days} days)")

    updater = ServerUpdater(session)

    try:
        count = await updater.prune_stale_servers(request.days)
        return {"message": f"Pruned {count} stale servers"}
    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/admin/bulk-update", tags=["Admin"])
@limiter.limit("5/minute")
async def bulk_update(
    request: BulkUpdateRequest,
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Perform bulk update on servers (admin only).

    Args:
        request: Bulk update request with filters and updates
        session: Database session
        role: User role (must be admin)

    Returns:
        Update statistics
    """
    logger.info("Performing bulk update")

    updater = ServerUpdater(session)

    try:
        count = await updater.bulk_update_servers(request.filters, request.updates)
        return {"message": f"Updated {count} servers"}
    except (ValidationError, UpdateError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get("/admin/stats", tags=["Admin"])
@limiter.limit("10/minute")
async def get_statistics(
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Get detailed database statistics (admin only).

    Args:
        session: Database session
        role: User role (must be admin)

    Returns:
        Database statistics
    """
    logger.info("Getting statistics")

    updater = ServerUpdater(session)

    try:
        stats = await updater.get_statistics()
        return stats
    except UpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# --- Social Media Endpoints ---


@app.get("/social/posts", response_model=List[SocialPostResponse], tags=["Social Media"])
@limiter.limit("60/minute")
async def list_social_posts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    platform: Optional[str] = Query(None, description="Filter by platform (reddit, twitter)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    min_score: Optional[int] = Query(None, description="Minimum engagement score"),
    server_id: Optional[int] = Query(None, description="Filter by mentioned server"),
    session: AsyncSession = Depends(get_session),
):
    """List social media posts with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        platform: Filter by platform
        category: Filter by content category
        sentiment: Filter by sentiment
        min_score: Minimum engagement score
        server_id: Filter by mentioned server ID
        session: Database session

    Returns:
        List of social posts
    """
    logger.info(f"Listing social posts (skip={skip}, limit={limit}, platform={platform})")

    # Build query with filters
    statement = select(SocialPost)

    if platform:
        statement = statement.where(SocialPost.platform == platform)
    if category:
        statement = statement.where(SocialPost.category == category)
    if sentiment:
        statement = statement.where(SocialPost.sentiment == sentiment)
    if min_score is not None:
        statement = statement.where(SocialPost.score >= min_score)

    statement = statement.offset(skip).limit(limit).order_by(SocialPost.platform_created_at.desc())

    result = await session.execute(statement)
    posts = result.scalars().all()

    # Filter by server_id if specified (JSON array contains check)
    if server_id is not None:
        posts = [p for p in posts if server_id in (p.mentioned_servers or [])]

    return posts


@app.get("/social/posts/{post_id}", response_model=SocialPostResponse, tags=["Social Media"])
@limiter.limit("100/minute")
async def get_social_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific social media post by ID.

    Args:
        post_id: Post ID
        session: Database session

    Returns:
        Social post details

    Raises:
        HTTPException: If post not found
    """
    logger.info(f"Getting social post {post_id}")

    result = await session.execute(select(SocialPost).where(SocialPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Social post {post_id} not found",
        )

    return post


@app.get("/social/videos", response_model=List[VideoResponse], tags=["Social Media"])
@limiter.limit("60/minute")
async def list_videos(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    platform: Optional[str] = Query(None, description="Filter by platform (youtube, vimeo)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_views: Optional[int] = Query(None, description="Minimum view count"),
    min_educational_value: Optional[int] = Query(None, description="Minimum educational value score"),
    server_id: Optional[int] = Query(None, description="Filter by mentioned server"),
    session: AsyncSession = Depends(get_session),
):
    """List videos with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        platform: Filter by platform
        category: Filter by content category
        min_views: Minimum view count
        min_educational_value: Minimum educational value score
        server_id: Filter by mentioned server ID
        session: Database session

    Returns:
        List of videos
    """
    logger.info(f"Listing videos (skip={skip}, limit={limit}, platform={platform})")

    # Build query with filters
    statement = select(Video)

    if platform:
        statement = statement.where(Video.platform == platform)
    if category:
        statement = statement.where(Video.category == category)
    if min_views is not None:
        statement = statement.where(Video.view_count >= min_views)
    if min_educational_value is not None:
        statement = statement.where(Video.educational_value >= min_educational_value)

    statement = statement.offset(skip).limit(limit).order_by(Video.published_at.desc())

    result = await session.execute(statement)
    videos = result.scalars().all()

    # Filter by server_id if specified
    if server_id is not None:
        videos = [v for v in videos if server_id in (v.mentioned_servers or [])]

    return videos


@app.get("/social/videos/{video_id}", response_model=VideoResponse, tags=["Social Media"])
@limiter.limit("100/minute")
async def get_video(
    video_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific video by ID.

    Args:
        video_id: Video ID
        session: Database session

    Returns:
        Video details

    Raises:
        HTTPException: If video not found
    """
    logger.info(f"Getting video {video_id}")

    result = await session.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found",
        )

    return video


@app.get("/social/articles", response_model=List[ArticleResponse], tags=["Social Media"])
@limiter.limit("60/minute")
async def list_articles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    platform: Optional[str] = Query(None, description="Filter by platform (medium, dev_to, etc)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_reading_time: Optional[int] = Query(None, description="Minimum reading time (minutes)"),
    server_id: Optional[int] = Query(None, description="Filter by mentioned server"),
    session: AsyncSession = Depends(get_session),
):
    """List articles with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        platform: Filter by platform
        category: Filter by content category
        min_reading_time: Minimum reading time in minutes
        server_id: Filter by mentioned server ID
        session: Database session

    Returns:
        List of articles
    """
    logger.info(f"Listing articles (skip={skip}, limit={limit}, platform={platform})")

    # Build query with filters
    statement = select(Article)

    if platform:
        statement = statement.where(Article.platform == platform)
    if category:
        statement = statement.where(Article.category == category)
    if min_reading_time is not None:
        statement = statement.where(Article.reading_time_minutes >= min_reading_time)

    statement = statement.offset(skip).limit(limit).order_by(Article.published_at.desc())

    result = await session.execute(statement)
    articles = result.scalars().all()

    # Filter by server_id if specified
    if server_id is not None:
        articles = [a for a in articles if server_id in (a.mentioned_servers or [])]

    return articles


@app.get("/social/articles/{article_id}", response_model=ArticleResponse, tags=["Social Media"])
@limiter.limit("100/minute")
async def get_article(
    article_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific article by ID.

    Args:
        article_id: Article ID
        session: Database session

    Returns:
        Article details

    Raises:
        HTTPException: If article not found
    """
    logger.info(f"Getting article {article_id}")

    result = await session.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article {article_id} not found",
        )

    return article


@app.get("/servers/{server_id}/social", tags=["Social Media"])
@limiter.limit("60/minute")
async def get_server_social_content(
    server_id: int,
    content_type: Optional[str] = Query(None, description="Filter by type (posts, videos, articles)"),
    session: AsyncSession = Depends(get_session),
):
    """Get all social media content mentioning a specific server.

    Args:
        server_id: Server ID
        content_type: Optional filter by content type
        session: Database session

    Returns:
        Social media content mentioning the server

    Raises:
        HTTPException: If server not found
    """
    logger.info(f"Getting social content for server {server_id}")

    # Verify server exists
    server_result = await session.execute(select(Server).where(Server.id == server_id))
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found",
        )

    result = {"server_id": server_id, "server_name": server.name}

    # Get posts mentioning this server
    if content_type in (None, "posts"):
        posts_result = await session.execute(select(SocialPost))
        posts = posts_result.scalars().all()
        result["posts"] = [p for p in posts if server_id in (p.mentioned_servers or [])]

    # Get videos mentioning this server
    if content_type in (None, "videos"):
        videos_result = await session.execute(select(Video))
        videos = videos_result.scalars().all()
        result["videos"] = [v for v in videos if server_id in (v.mentioned_servers or [])]

    # Get articles mentioning this server
    if content_type in (None, "articles"):
        articles_result = await session.execute(select(Article))
        articles = articles_result.scalars().all()
        result["articles"] = [a for a in articles if server_id in (a.mentioned_servers or [])]

    return result


@app.get("/social/trending", tags=["Social Media"])
@limiter.limit("30/minute")
async def get_trending_content(
    days: int = Query(7, ge=1, le=30, description="Look back N days"),
    min_score: int = Query(50, description="Minimum engagement score"),
    session: AsyncSession = Depends(get_session),
):
    """Get trending social media content from the last N days.

    Args:
        days: Number of days to look back
        min_score: Minimum engagement score
        session: Database session

    Returns:
        Trending posts, videos, and articles
    """
    logger.info(f"Getting trending content (last {days} days)")

    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get trending posts
    posts_statement = (
        select(SocialPost)
        .where(
            and_(
                SocialPost.platform_created_at >= cutoff_date, SocialPost.score >= min_score
            )
        )
        .order_by(SocialPost.score.desc())
        .limit(20)
    )
    posts_result = await session.execute(posts_statement)
    posts = posts_result.scalars().all()

    # Get trending videos
    videos_statement = (
        select(Video)
        .where(and_(Video.published_at >= cutoff_date, Video.view_count >= min_score))
        .order_by(Video.view_count.desc())
        .limit(20)
    )
    videos_result = await session.execute(videos_statement)
    videos = videos_result.scalars().all()

    # Get trending articles
    articles_statement = (
        select(Article)
        .where(and_(Article.published_at >= cutoff_date, Article.like_count >= min_score))
        .order_by(Article.like_count.desc())
        .limit(20)
    )
    articles_result = await session.execute(articles_statement)
    articles = articles_result.scalars().all()

    return {"posts": posts, "videos": videos, "articles": articles, "days": days}


# --- Root Endpoint ---


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MCPS API",
        "version": "1.0.0",
        "description": "Model Context Protocol Server API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
