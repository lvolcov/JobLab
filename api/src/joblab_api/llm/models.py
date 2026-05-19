"""LLM key ORM model.

Purpose: store encrypted provider API keys, either global (admin-owned)
or per-user. Assignment table arrives in Prompt 5.
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey
from sqlmodel import Field, SQLModel


class LLMProvider(str, Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


def llm_provider_column(*, nullable: bool, index: bool = False) -> Column:
    """SQLA column for LLMProvider that serialises member *values* (lowercase).

    The Postgres enum type ``llmprovider`` was created by Alembic with
    lowercase values; SQLAlchemy's default serialises member NAMES. Without
    ``values_callable`` every INSERT raises "invalid input value for enum".
    """
    return Column(
        SAEnum(
            LLMProvider,
            name="llmprovider",
            values_callable=lambda enum: [m.value for m in enum],
        ),
        nullable=nullable,
        index=index,
    )


class LLMKey(SQLModel, table=True):
    """Encrypted API key for an LLM provider.

    - is_global=True, owner_user_id IS NULL  → admin-curated global key.
    - is_global=False, owner_user_id IS NOT NULL → user's personal key.
    """

    __tablename__ = "llm_keys"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    owner_user_id: UUID | None = Field(
        default=None,
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
    )
    provider: LLMProvider = Field(sa_column=llm_provider_column(nullable=False, index=True))
    encrypted_key: str = Field(nullable=False, max_length=4096)
    label: str = Field(nullable=False, max_length=128)
    is_global: bool = Field(default=False, nullable=False, index=True)
    is_premium_only: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
