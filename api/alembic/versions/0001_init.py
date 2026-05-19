"""init: users + llm_keys

Revision ID: 0001_init
Revises:
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "llm_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "provider",
            sa.Enum("openai", "anthropic", "gemini", name="llmprovider"),
            nullable=False,
        ),
        sa.Column("encrypted_key", sa.String(length=4096), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_llm_keys_owner_user_id", "llm_keys", ["owner_user_id"])
    op.create_index("ix_llm_keys_provider", "llm_keys", ["provider"])
    op.create_index("ix_llm_keys_is_global", "llm_keys", ["is_global"])


def downgrade() -> None:
    op.drop_index("ix_llm_keys_is_global", table_name="llm_keys")
    op.drop_index("ix_llm_keys_provider", table_name="llm_keys")
    op.drop_index("ix_llm_keys_owner_user_id", table_name="llm_keys")
    op.drop_table("llm_keys")
    op.execute("DROP TYPE IF EXISTS llmprovider")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
