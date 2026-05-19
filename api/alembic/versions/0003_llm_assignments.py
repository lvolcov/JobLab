"""llm key assignments

Revision ID: 0003_llm_assignments
Revises: 0002_wiki_documents
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_llm_assignments"
down_revision: str | None = "0002_wiki_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_key_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "llm_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("llm_keys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("llm_key_id", "user_id", name="uq_llm_key_user"),
    )
    op.create_index(
        "ix_llm_key_assignments_llm_key_id", "llm_key_assignments", ["llm_key_id"]
    )
    op.create_index(
        "ix_llm_key_assignments_user_id", "llm_key_assignments", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_llm_key_assignments_user_id", table_name="llm_key_assignments")
    op.drop_index("ix_llm_key_assignments_llm_key_id", table_name="llm_key_assignments")
    op.drop_table("llm_key_assignments")
