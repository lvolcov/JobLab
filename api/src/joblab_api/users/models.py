"""User ORM model.

Purpose: identity record used by auth, with admin flag (is_superuser).
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from joblab_api.llm.models import LLMProvider, llm_provider_column


class User(SQLModel, table=True):
    """Application user. is_superuser=True grants admin privileges."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False, max_length=320)
    hashed_password: str = Field(nullable=False, max_length=1024)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    is_premium: bool = Field(default=False, nullable=False)
    default_provider: LLMProvider | None = Field(
        default=None, sa_column=llm_provider_column(nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
