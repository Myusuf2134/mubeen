"""Test configuration and shared fixtures.

Tests run against the dev Postgres instance (Docker on localhost:5432).
The db fixture cleans up all tables after each test using the same session
so there's no connection pool contention in teardown.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mubeen.api.deps import create_operator_token
from mubeen.db.base import Base
from mubeen.db.models.masjid import Masjid
from mubeen.db.models.operator import OperatorAccount
from mubeen.db.session import get_session
from mubeen.main import app

_TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://mubeen:mubeen@localhost:5432/mubeen",
)

_engine = create_async_engine(_TEST_DB_URL, echo=False)
_SessionMaker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

# Delete order respects FK constraints (children before parents)
_CLEANUP_TABLES = [
    "khutbah_segments",
    "khutbah_sessions",
    "jumuah_times",
    "iqamah_times",
    "operator_accounts",
    "masjids",
]


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _SessionMaker() as session:
        yield session
        # Rollback any uncommitted work (e.g. flushed-but-not-committed seed data)
        await session.rollback()
        # Delete all committed data using the same session/connection — avoids pool contention
        for table_name in _CLEANUP_TABLES:
            table = Base.metadata.tables[table_name]
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_session] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── Seed helpers ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def seed_masjid(db: AsyncSession) -> Masjid:
    masjid = Masjid(
        id=uuid4(),
        name="Masjid Al-Noor",
        address_line="1234 Lake St",
        city="Minneapolis",
        state="MN",
        country="US",
        lat=44.9778,
        lon=-93.2650,
        calculation_method="ISNA",
    )
    db.add(masjid)
    await db.flush()
    return masjid


@pytest_asyncio.fixture
async def seed_operator(db: AsyncSession, seed_masjid: Masjid) -> tuple[OperatorAccount, str]:
    import bcrypt

    operator = OperatorAccount(
        id=uuid4(),
        masjid_id=seed_masjid.id,
        email="test-operator@example.com",
        hashed_password=bcrypt.hashpw(b"fixture-only", bcrypt.gensalt(rounds=4)).decode(),
    )
    db.add(operator)
    await db.flush()
    token = create_operator_token(operator.id, seed_masjid.id)
    return operator, token
