"""Database configuration and session management with PostgreSQL support.

This module provides production-ready database connection management with:
- Automatic connection pooling
- Health checks and connection testing
- Retry logic for transient failures
- Support for both PostgreSQL (production) and SQLite (development)
- Query performance monitoring
- Slow query detection
- Connection pool metrics
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from loguru import logger
from sqlalchemy import event, exc, pool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .settings import settings

# Try to import metrics (optional)
try:
    from .metrics import (
        collect_db_pool_metrics,
        db_connection_errors_total,
        db_queries_total,
        db_query_duration_seconds,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

# Create async engine with production-ready configuration
engine_kwargs: Dict[str, Any] = {
    "echo": settings.db_echo,
    "future": True,
}

# Add PostgreSQL-specific optimizations
if settings.is_postgresql:
    engine_kwargs.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": settings.db_pool_pre_ping,
            "pool_timeout": 30,  # Timeout for getting connection from pool
            # Use QueuePool for asyncpg (best for production)
            "poolclass": pool.QueuePool,
        }
    )
    logger.info(
        f"Configuring PostgreSQL connection pool: "
        f"size={settings.db_pool_size}, "
        f"max_overflow={settings.db_max_overflow}, "
        f"recycle={settings.db_pool_recycle}s"
    )
else:
    # SQLite-specific configuration
    engine_kwargs.update(
        {
            # Use NullPool for SQLite (single connection)
            "poolclass": pool.NullPool,
            "connect_args": {"check_same_thread": False},
        }
    )
    logger.info("Using SQLite with NullPool (development mode)")

# Create async engine
engine = create_async_engine(
    settings.db_url,
    **engine_kwargs,
)

# Log connection info (without password)
safe_url = settings.db_url
if "@" in safe_url:
    # Mask password in URL
    parts = safe_url.split("@")
    user_pass = parts[0].split("://")[1]
    if ":" in user_pass:
        user = user_pass.split(":")[0]
        safe_url = safe_url.replace(user_pass, f"{user}:****")
logger.info(f"Database engine created: {safe_url}")


# Add event listeners for connection pool monitoring (PostgreSQL only)
if settings.is_postgresql:

    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new database connections."""
        logger.debug(f"New database connection established: {id(dbapi_conn)}")

    @event.listens_for(engine.sync_engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log closed database connections."""
        logger.debug(f"Database connection closed: {id(dbapi_conn)}")

    @event.listens_for(engine.sync_engine, "handle_error")
    def receive_error(exception_context):
        """Log and track database errors."""
        error = exception_context.original_exception
        logger.error(f"Database error: {error}", exc_info=True)

        # Track error metrics
        if METRICS_AVAILABLE:
            error_type = error.__class__.__name__
            db_connection_errors_total.labels(error_type=error_type).inc()


# Query performance monitoring
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query start time."""
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Track query execution time and log slow queries."""
    import time

    total_time = time.time() - conn.info["query_start_time"].pop()

    # Log slow queries (>1 second)
    if total_time > 1.0:
        logger.warning(
            f"Slow query detected ({total_time:.2f}s): {statement[:200]}...",
            duration_ms=total_time * 1000,
            query=statement[:500],
        )

    # Track metrics
    if METRICS_AVAILABLE:
        # Extract operation and table from statement
        operation = statement.strip().split()[0].upper() if statement else "UNKNOWN"
        table = "unknown"

        # Try to extract table name (simple heuristic)
        if "FROM" in statement.upper():
            parts = statement.upper().split("FROM")[1].strip().split()
            if parts:
                table = parts[0].strip("(),;").lower()

        db_queries_total.labels(operation=operation, table=table).inc()
        db_query_duration_seconds.labels(operation=operation, table=table).observe(total_time)


# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@retry(
    retry=retry_if_exception_type((exc.OperationalError, exc.DatabaseError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def init_db() -> None:
    """Initialize database tables with retry logic.

    Retries up to 3 times with exponential backoff for transient failures.
    """
    logger.info("Initializing database schema...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.success("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


async def get_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """Get async database session.

    Usage:
        async for session in get_session():
            # use session

    Or use async_session_maker() directly:
        async with async_session_maker() as session:
            # use session
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


@retry(
    retry=retry_if_exception_type((exc.OperationalError, exc.DatabaseError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
async def health_check() -> Dict[str, Any]:
    """Check database connection health.

    Returns:
        Dictionary with health check results including:
        - healthy: bool
        - latency_ms: float
        - pool_size: int (PostgreSQL only)
        - pool_checked_in: int (PostgreSQL only)
        - pool_checked_out: int (PostgreSQL only)
        - pool_overflow: int (PostgreSQL only)
        - database_type: str

    Raises:
        Exception: If health check fails
    """
    import time

    start_time = time.time()

    try:
        async with async_session_maker() as session:
            # Execute simple query to test connection
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        latency_ms = (time.time() - start_time) * 1000

        health_info = {
            "healthy": True,
            "latency_ms": round(latency_ms, 2),
            "database_type": "postgresql" if settings.is_postgresql else "sqlite",
            "database_url": safe_url,
        }

        # Add connection pool stats for PostgreSQL
        if settings.is_postgresql:
            pool_obj = engine.pool
            pool_stats = {
                "pool_size": pool_obj.size(),
                "pool_checked_in": pool_obj.checkedin(),
                "pool_checked_out": pool_obj.checkedout(),
                "pool_overflow": pool_obj.overflow(),
                "pool_timeout": pool_obj.timeout(),
            }
            health_info.update(pool_stats)

            # Update metrics if available
            if METRICS_AVAILABLE:
                collect_db_pool_metrics(pool_obj)

        logger.debug(f"Database health check passed: {health_info}")
        return health_info

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "database_type": "postgresql" if settings.is_postgresql else "sqlite",
        }


async def close_db() -> None:
    """Close database connections gracefully.

    This disposes the connection pool and waits for all connections to close.
    """
    logger.info("Closing database connections...")
    try:
        await engine.dispose()
        logger.success("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# Convenience context manager for transactions
@asynccontextmanager
async def transaction() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """Context manager for database transactions.

    Usage:
        async with transaction() as session:
            # perform database operations
            # transaction is automatically committed on success
            # or rolled back on exception
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            await session.close()
