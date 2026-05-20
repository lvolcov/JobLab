"""Add grade column to application_artifacts.

Revision ID: 0007_artifact_grade
Revises: 0006_premium_flag
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_artifact_grade"
down_revision = "0006_premium_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "application_artifacts",
        sa.Column("grade", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("application_artifacts", "grade")
