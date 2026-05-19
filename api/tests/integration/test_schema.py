"""Schema smoke tests for Prompt 2.

Verifies:
- The ephemeral-schema fixture brings up users + llm_keys.
- Running `alembic upgrade head` against a fresh schema creates both tables.
Created: 2026-05-19
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from joblab_api.config import get_settings


@pytest.mark.asyncio
async def test_fixture_creates_expected_tables(db_session: AsyncSession) -> None:
    """The fixture's ephemeral schema must contain users and llm_keys."""
    result = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() ORDER BY table_name"
        )
    )
    tables = {row[0] for row in result.all()}
    assert {"users", "llm_keys"}.issubset(tables), tables


def test_alembic_upgrade_head_creates_tables() -> None:
    """Run alembic upgrade head against a throwaway schema; assert tables exist."""
    settings = get_settings()
    sync_url = settings.sync_database_url
    schema_name = f"alembic_test_{uuid4().hex[:12]}"

    admin_engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    admin_engine.dispose()

    try:
        cfg = Config("alembic.ini")
        cfg.set_main_option("script_location", "alembic")
        cfg.set_main_option("sqlalchemy.url", sync_url)
        # env.py reads `-x schema=...` and applies SET search_path.
        cfg.cmd_opts = type("Opts", (), {"x": [f"schema={schema_name}"]})()
        command.upgrade(cfg, "head")

        engine = create_engine(sync_url)
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names(schema=schema_name))
        engine.dispose()
        assert "users" in tables, tables
        assert "llm_keys" in tables, tables
    finally:
        cleanup = create_engine(sync_url, isolation_level="AUTOCOMMIT")
        with cleanup.connect() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
        cleanup.dispose()
