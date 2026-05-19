"""wiki entities + documents

Revision ID: 0002_wiki_documents
Revises: 0001_init
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_wiki_documents"
down_revision: str | None = "0001_init"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common_cols() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "wiki_cvs",
        *_common_cols(),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_cvs_user_id", "wiki_cvs", ["user_id"])

    op.create_table(
        "wiki_education",
        *_common_cols(),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("qualification", sa.String(length=200), nullable=False),
        sa.Column("start", sa.Date(), nullable=True),
        sa.Column("end", sa.Date(), nullable=True),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_education_user_id", "wiki_education", ["user_id"])

    op.create_table(
        "wiki_qualifications",
        *_common_cols(),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("issuer", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("date_awarded", sa.Date(), nullable=True),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_qualifications_user_id", "wiki_qualifications", ["user_id"])

    op.create_table(
        "wiki_skills",
        *_common_cols(),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("level", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_skills_user_id", "wiki_skills", ["user_id"])

    op.create_table(
        "wiki_projects",
        *_common_cols(),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("start", sa.Date(), nullable=True),
        sa.Column("end", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("achievements", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_projects_user_id", "wiki_projects", ["user_id"])

    op.create_table(
        "wiki_experiences",
        *_common_cols(),
        sa.Column("employer", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("start", sa.Date(), nullable=True),
        sa.Column("end", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("achievements", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_wiki_experiences_user_id", "wiki_experiences", ["user_id"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("mime", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])


def downgrade() -> None:
    for tbl in (
        "documents",
        "wiki_experiences",
        "wiki_projects",
        "wiki_skills",
        "wiki_qualifications",
        "wiki_education",
        "wiki_cvs",
    ):
        op.drop_index(f"ix_{tbl}_user_id", table_name=tbl)
        op.drop_table(tbl)
