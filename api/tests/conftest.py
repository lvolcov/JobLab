"""Shared pytest fixtures.

Purpose: provide an ephemeral per-test Postgres schema and an HTTPX client
bound to the FastAPI app with its DB dependency redirected at that schema.
Created: 2026-05-19
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("FERNET_KEY", "ZmFrZS1mZXJuZXQta2V5LTMyLWJ5dGVzLWxvbmcuLi4uLi4=")
os.environ["JOBLAB_TEST_MODE"] = "1"

from joblab_api import models  # noqa: E402, F401 — register tables on metadata
from joblab_api.auth.security import (  # noqa: E402
    SESSION_COOKIE_NAME,
    hash_password,
    issue_session_token,
)
from joblab_api.config import get_settings  # noqa: E402
from joblab_api.db import get_session  # noqa: E402
from joblab_api.main import app  # noqa: E402
from joblab_api.security_middleware import CSRF_COOKIE, CSRF_HEADER  # noqa: E402
from joblab_api.users.models import User  # noqa: E402

_TEST_CSRF_TOKEN = "test-csrf-token-fixed"


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session bound to a fresh, ephemeral Postgres schema."""
    settings = get_settings()
    schema_name = f"test_{uuid4().hex[:12]}"

    admin_engine = create_async_engine(settings.async_database_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    await admin_engine.dispose()

    scoped_engine = create_async_engine(
        settings.async_database_url,
        connect_args={"options": f"-csearch_path={schema_name}"},
    )
    async with scoped_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(scoped_engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await scoped_engine.dispose()
        cleanup = create_async_engine(settings.async_database_url, isolation_level="AUTOCOMMIT")
        async with cleanup.connect() as conn:
            await conn.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
        await cleanup.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTPX client wired to the FastAPI app, with get_session overridden."""

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={CSRF_HEADER: _TEST_CSRF_TOKEN},
            cookies={CSRF_COOKIE: _TEST_CSRF_TOKEN},
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@test.local",
        hashed_password=hash_password("admin-pass-1234"),
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession) -> User:
    user = User(
        email="user@test.local",
        hashed_password=hash_password("user-pass-1234"),
        is_superuser=False,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_cookie(user: User) -> dict[str, str]:
    """Return a cookies dict authenticating as the given user.

    Always re-adds the CSRF cookie so tests that call `cookies.clear()` before
    switching users don't trip the CSRF middleware on subsequent writes.
    """
    return {
        SESSION_COOKIE_NAME: issue_session_token(user.id),
        CSRF_COOKIE: _TEST_CSRF_TOKEN,
    }
