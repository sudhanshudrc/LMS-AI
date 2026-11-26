"""Pytest configuration and global test fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Test database URL
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_secure_password@localhost:5432/lms_db",
)


@pytest_asyncio.fixture
async def db_engine():
    """Create async SQLAlchemy engine for test suite."""
    engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide transactional async session for tests that rolls back automatically."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
