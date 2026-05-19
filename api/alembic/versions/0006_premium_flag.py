"""premium tiering: users.is_premium + llm_keys.is_premium_only; drop assignments

Revision ID: 0006_premium_flag
Revises: 0005_default_provider_dup
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_premium_flag"
down_revision: str | None = "0005_default_provider_dup"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "llm_keys",
        sa.Column(
            "is_premium_only", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    # Per-user assignment is replaced by the premium flag.
    op.drop_table("llm_key_assignments")


def downgrade() -> None:
    op.create_table(
        "llm_key_assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "llm_key_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("llm_keys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("llm_key_id", "user_id", name="uq_llm_key_user"),
    )
    op.drop_column("llm_keys", "is_premium_only")
    op.drop_column("users", "is_premium")
