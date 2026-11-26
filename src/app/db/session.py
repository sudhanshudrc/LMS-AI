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
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_engine() -> AsyncEngine:
    """Return process-wide singleton async SQLAlchemy engine."""
    settings = get_settings()
    logger.info("initializing_database_engine", pool_size=settings.db_pool_size)
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
    try:
        async with get_session_factory()() as session:
            result = await session.execute(text("SELECT 1"))
            is_ok = result.scalar() == 1
            if is_ok:
                logger.info("database_ping_successful")
            else:
                logger.warning("database_ping_unexpected_result")
            return is_ok
    except Exception as exc:
        logger.exception("database_ping_failed", error=str(exc))
        return False
