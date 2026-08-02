import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main import app
from src.modules.identity.infrastructure import (
    models,  # noqa: F401  (registers tables on Base.metadata)
)
from src.platform.config import get_settings
from src.platform.db import Base, get_db

settings = get_settings()


@pytest.fixture(scope="session", autouse=True)
def _schema() -> None:
    """Creates/drops tables using a throwaway engine+loop, independent of any test's event loop."""

    async def _create() -> None:
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_create())
    yield

    async def _drop() -> None:
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_drop())


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    """Fresh engine per test, created in that test's own loop to avoid cross-loop reuse."""
    engine = create_async_engine(settings.database_url)
    yield engine
    table_names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncGenerator[AsyncClient]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _get_db_override() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client():
    from fastapi.testclient import TestClient

    return TestClient(app)
