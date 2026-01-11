# -*- coding: utf-8 -*-

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from learn_fastapi_auth.database import Base
from learn_fastapi_auth.one.api import one

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create test database session for direct database operations."""
    async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    """Create test client with overridden database session."""
    from learn_fastapi_auth.app import app
    from learn_fastapi_auth.ratelimit import reset_rate_limit_storage

    # Reset rate limit storage before each test to avoid interference
    reset_rate_limit_storage()

    async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_async_session():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[one.get_async_session] = override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    # Reset rate limit storage after each test as well
    reset_rate_limit_storage()
