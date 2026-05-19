"""users.default_provider + wiki.possible_duplicate_of_id

Revision ID: 0005_default_provider_dup
Revises: 0004_applications
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_default_provider_dup"
down_revision: str | None = "0004_applications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_WIKI_TABLES = (
    "wiki_cvs",
    "wiki_education",
    "wiki_qualifications",
    "wiki_skills",
    "wiki_projects",
    "wiki_experiences",
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "default_provider",
            postgresql.ENUM(
                "openai", "anthropic", "gemini", name="llmprovider", create_type=False
            ),
            nullable=True,
        ),
    )

    for table in _WIKI_TABLES:
        op.add_column(
            table,
            sa.Column(
                "possible_duplicate_of_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey(f"{table}.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for table in _WIKI_TABLES:
        op.drop_column(table, "possible_duplicate_of_id")
    op.drop_column("users", "default_provider")
