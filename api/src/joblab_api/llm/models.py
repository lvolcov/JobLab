"""LLM key ORM model.

Purpose: store encrypted provider API keys, either global (admin-owned)
or per-user. Assignment table arrives in Prompt 5.
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlmodel import Field, SQLModel


class LLMProvider(str, Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


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
    provider: LLMProvider = Field(nullable=False, index=True)
    encrypted_key: str = Field(nullable=False, max_length=4096)
    label: str = Field(nullable=False, max_length=128)
    is_global: bool = Field(default=False, nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class LLMKeyAssignment(SQLModel, table=True):
    """Links a global LLMKey to a User permitted to use it."""

    __tablename__ = "llm_key_assignments"
    __table_args__ = (UniqueConstraint("llm_key_id", "user_id", name="uq_llm_key_user"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    llm_key_id: UUID = Field(
        sa_column=Column(
            ForeignKey("llm_keys.id", ondelete="CASCADE"), nullable=False, index=True
        ),
    )
    user_id: UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        ),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
