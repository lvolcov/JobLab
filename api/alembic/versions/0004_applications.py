"""applications + artifacts

Revision ID: 0004_applications
Revises: 0003_llm_assignments
Create Date: 2026-05-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_applications"
down_revision: str | None = "0003_llm_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    application_status = sa.Enum(
        "applied",
        "screening",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
        name="applicationstatus",
    )
    artifact_type = sa.Enum(
        "cv", "cover_letter", "blind_cv", "behaviour", name="artifacttype"
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role_title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("jd_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", application_status, nullable=False, server_default="applied"),
        sa.Column("applied_at", sa.Date(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])

    op.create_table(
        "application_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", artifact_type, nullable=False),
        sa.Column(
            "provider",
            postgresql.ENUM(
                "openai", "anthropic", "gemini", name="llmprovider", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("word_limit", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("final_word_count", sa.Integer(), nullable=False),
        sa.Column("warning_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("extra_instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("behaviour_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_application_artifacts_application_id",
        "application_artifacts",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_artifacts_application_id", table_name="application_artifacts"
    )
    op.drop_table("application_artifacts")
    op.drop_index("ix_applications_user_id", table_name="applications")
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS artifacttype")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
