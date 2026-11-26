"""Async engine, session factory, and session dependencies."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Return process-wide singleton async SQLAlchemy engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return process-wide session factory bound to async engine."""
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI request dependency yielding an open AsyncSession."""
    async with get_session_factory()() as session:
        yield session


async def check_database_connection() -> bool:
    """Check connectivity to database by executing SELECT 1."""
    async with get_session_factory()() as session:
        result = await session.execute(text("SELECT 1"))
        return result.scalar() == 1
