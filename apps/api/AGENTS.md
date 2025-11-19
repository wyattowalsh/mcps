# AGENTS.md - FastAPI Application Guide

## Context

The `apps/api/` directory contains the FastAPI RESTful API that provides HTTP access to MCPS data and operations. It serves as the write-access and administrative interface to the system.

**Purpose:** Provide secure, rate-limited API access for CRUD operations, bulk updates, server refreshing, and administrative maintenance tasks.

**Architecture:** Single-file FastAPI application (`main.py`) with async database access, API key authentication, rate limiting, and comprehensive OpenAPI documentation.

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Complete FastAPI application with all endpoints and middleware |

## Endpoint Design Patterns

### 1. Standard CRUD Endpoints

All entity endpoints follow RESTful conventions:

```python
# List resources (with pagination)
@app.get("/servers", response_model=List[ServerResponse])
async def list_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """List servers with pagination."""
    pass

# Get single resource
@app.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get server by ID."""
    pass

# Update resource
@app.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    updates: ServerUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update server."""
    pass

# Delete resource (admin only)
@app.delete("/servers/{server_id}")
async def delete_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Delete server (admin only)."""
    pass
```

### 2. Filtering and Search

```python
# Filter with query parameters
@app.get("/servers")
async def list_servers(
    host_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    verified_only: bool = Query(False),
):
    """List servers with filters."""
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

    return await session.execute(query)

# Full-text search
@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    """Search across servers and tools."""
    servers = await session.execute(
        select(Server).where(
            or_(
                Server.name.ilike(f"%{q}%"),
                Server.description.ilike(f"%{q}%"),
            )
        )
    )
    return servers
```

### 3. Pagination

```python
@app.get("/servers")
async def list_servers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
):
    """Paginated server list."""
    query = select(Server).offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
```

## Authentication and Rate Limiting

### API Key Authentication

```python
# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Valid API keys (in production, use secure storage)
VALID_API_KEYS = {
    "dev_key_12345": "development",
    "admin_key_67890": "admin",
}

# Verify API key dependency
async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key and return user role."""
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return VALID_API_KEYS[api_key]

# Admin-only verification
async def verify_admin(role: str = Depends(verify_api_key)) -> str:
    """Verify user has admin role."""
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return role

# Use in endpoints
@app.get("/servers")
async def list_servers(_role: str = Depends(verify_api_key)):
    """Requires any valid API key."""
    pass

@app.delete("/servers/{id}")
async def delete_server(role: str = Depends(verify_admin)):
    """Requires admin API key."""
    pass
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.get("/servers")
@limiter.limit("60/minute")  # 60 requests per minute
async def list_servers():
    pass

@app.post("/servers/refresh")
@limiter.limit("10/minute")  # Stricter limit for expensive operations
async def refresh_server():
    pass

@app.post("/admin/prune-stale")
@limiter.limit("5/minute")  # Very strict for admin operations
async def prune_stale(role: str = Depends(verify_admin)):
    pass
```

## Pydantic Model Conventions

### Request Models

```python
from pydantic import BaseModel, Field

class ServerUpdate(BaseModel):
    """Request model for server updates.

    Use Optional for all fields to support partial updates.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    stars: Optional[int] = Field(None, ge=0)  # Validation: >= 0
    verified_source: Optional[bool] = None

class ServerCreate(BaseModel):
    """Request model for creating servers.

    Use required fields for creation.
    """
    name: str
    primary_url: str
    host_type: str
    description: Optional[str] = None
```

### Response Models

```python
class ServerResponse(BaseModel):
    """Response model for server data.

    Include all fields that should be exposed to API clients.
    """
    id: int
    uuid: str
    name: str
    primary_url: str
    host_type: str
    description: Optional[str] = None
    stars: int
    health_score: int
    risk_level: str
    created_at: datetime
    updated_at: datetime

    # Configure Pydantic v2
    model_config = ConfigDict(from_attributes=True)
```

### Nested Models

```python
class ToolResponse(BaseModel):
    """Response model for tool data."""
    id: int
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = {}

class ServerDetailResponse(ServerResponse):
    """Extended response with related entities."""
    tools: List[ToolResponse] = []
    dependencies: List[DependencyResponse] = []
```

## Error Response Formats

### Standard Error Response

```python
# HTTPException automatically formats errors
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Server not found",
)

# Returns:
{
    "detail": "Server not found"
}
```

### Custom Error Response

```python
class ErrorResponse(BaseModel):
    """Custom error response format."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Use in endpoint
@app.get("/servers/{id}")
async def get_server(id: int):
    if not server:
        return JSONResponse(
            status_code=404,
            content={
                "error": "NotFound",
                "message": f"Server {id} not found",
                "details": {"server_id": id}
            }
        )
```

### Validation Errors

```python
# Pydantic automatically validates request bodies
class ServerUpdate(BaseModel):
    stars: int = Field(..., ge=0, le=1000000)

# Invalid request automatically returns:
{
    "detail": [
        {
            "loc": ["body", "stars"],
            "msg": "ensure this value is greater than or equal to 0",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

## Examples

### Example 1: Complete CRUD Endpoint

```python
from packages.harvester.core.updater import ServerUpdater

@app.put("/servers/{server_id}", response_model=ServerResponse)
@limiter.limit("30/minute")
async def update_server(
    server_id: int,
    updates: ServerUpdate,
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Update server by ID."""
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
```

### Example 2: Admin Endpoint with Maintenance Operation

```python
@app.post("/admin/update-health-scores", tags=["Admin"])
@limiter.limit("5/minute")
async def update_health_scores(
    session: AsyncSession = Depends(get_session),
    role: str = Depends(verify_admin),
):
    """Recalculate health scores for all servers (admin only)."""
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
```

### Example 3: Search Endpoint

```python
@app.get("/search", response_model=SearchResponse, tags=["Search"])
@limiter.limit("30/minute")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _role: str = Depends(verify_api_key),
):
    """Full-text search across servers and tools."""
    logger.info(f"Searching for: {q}")

    # Search servers
    server_query = (
        select(Server)
        .where(
            or_(
                Server.name.ilike(f"%{q}%"),
                Server.description.ilike(f"%{q}%"),
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
```

## Common Tasks

### 1. Add New Endpoint

**Steps:**
1. Define Pydantic request/response models
2. Add endpoint function with decorators
3. Add rate limiting
4. Add authentication dependency
5. Implement logic using ServerUpdater or direct database access
6. Add error handling
7. Document with docstring
8. Test with curl or Postman

### 2. Modify Authentication

**Steps:**
1. Update VALID_API_KEYS (in production, use environment variables)
2. Modify verify_api_key() for custom logic
3. Add role-based access control if needed

### 3. Adjust Rate Limits

**Steps:**
1. Modify @limiter.limit() decorator
2. Test with repeated requests
3. Monitor rate limit exceeded errors

## Testing

### Manual Testing with curl

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# List servers (requires API key)
curl -H "X-API-Key: dev_key_12345" http://localhost:8000/servers

# Update server
curl -X PUT http://localhost:8000/servers/1 \
  -H "X-API-Key: dev_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"verified_source": true}'

# Admin endpoint
curl -X POST http://localhost:8000/admin/update-health-scores \
  -H "X-API-Key: admin_key_67890"
```

### Automated Testing

```python
import pytest
from httpx import AsyncClient
from apps.api.main import app

@pytest.mark.asyncio
async def test_list_servers():
    """Test server listing endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/servers",
            headers={"X-API-Key": "dev_key_12345"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

## Constraints

### API Key Security
- **NEVER hardcode production keys** - Use environment variables
- **Rotate keys regularly** - Implement key rotation mechanism
- **Use HTTPS only** - Never transmit keys over HTTP

### Rate Limiting
- **Set appropriate limits** - Balance usability and protection
- **Document limits** - Include in API documentation
- **Monitor abuse** - Log and alert on rate limit violations

### Error Handling
- **Never expose internal details** - Don't leak stack traces or DB errors
- **Use appropriate status codes** - 400 for validation, 404 for not found, 500 for server errors
- **Provide helpful messages** - Guide users to fix issues

## Related Areas

- **Harvester:** See `packages/harvester/AGENTS.md` for data harvesting operations
- **Web Dashboard:** See `apps/web/AGENTS.md` for frontend integration
- **Root Guide:** See `/home/user/mcps/AGENTS.md` for project overview

## Dependencies

Key packages:
- **FastAPI** - Web framework
- **SlowAPI** - Rate limiting
- **Pydantic** - Request/response validation
- **SQLModel** - Database ORM
- **uvicorn** - ASGI server

## Running the API

```bash
# Development
uv run uvicorn apps.api.main:app --reload --port 8000

# Production
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# With auto-reload and debug
uv run uvicorn apps.api.main:app --reload --log-level debug
```

## OpenAPI Documentation

Access interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

**Last Updated:** 2025-11-19
**See Also:** FastAPI documentation, apps/api/main.py source
