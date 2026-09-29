from collections.abc import Generator
import asyncio
from uuid import uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(create_app()) as test_client:
        yield test_client


async def _create_test_database(database_name: str) -> None:
    conn = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
    await conn.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = $1 AND pid <> pg_backend_pid()
        """,
        database_name,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
    await conn.execute(f'CREATE DATABASE "{database_name}"')
    await conn.close()


async def _drop_test_database(database_name: str) -> None:
    conn = await asyncpg.connect("postgresql://agenthub:agenthub@127.0.0.1:5433/agenthub")
    await conn.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = $1 AND pid <> pg_backend_pid()
        """,
        database_name,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{database_name}"')
    await conn.close()


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    database_name = f"agenthub_test_{uuid4().hex}"
    database_url = f"postgresql+asyncpg://agenthub:agenthub@127.0.0.1:5433/{database_name}"

    asyncio.run(_create_test_database(database_name))

    engine = create_async_engine(database_url, poolclass=NullPool)
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose_engine() -> None:
        await engine.dispose()

    asyncio.run(create_schema())

    async def override_get_db_session():
        async with TestingSessionLocal() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        asyncio.run(dispose_engine())
        asyncio.run(_drop_test_database(database_name))
