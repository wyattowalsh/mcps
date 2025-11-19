"""Database configuration and session management."""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from mcps.settings import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)

# Create async session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> SQLModelAsyncSession:
    """Get async database session.
    
    Usage:
        async for session in get_session():
            # use session
            
    Or use async_session_maker() directly:
        async with async_session_maker() as session:
            # use session
    """
    async with async_session_maker() as session:
        yield session


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
