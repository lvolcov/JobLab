"""Async SQLAlchemy engine and session factory for the API runtime.

Purpose: a single AsyncEngine + sessionmaker, plus a FastAPI dependency.
Created: 2026-05-19
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from joblab_api.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
)

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a per-request session."""
    async with SessionFactory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
