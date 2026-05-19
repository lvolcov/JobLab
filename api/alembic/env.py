"""Alembic environment.

Purpose: configure Alembic with our settings-derived URL and SQLModel metadata.
Created: 2026-05-19
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, engine_from_config, pool
from sqlmodel import SQLModel

# Register all models with SQLModel.metadata.
from joblab_api import models  # noqa: F401
from joblab_api.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve the database URL: env var → settings, with optional override via -x url=
x_args = context.get_x_argument(as_dictionary=True)
url = x_args.get("url") or get_settings().sync_database_url
config.set_main_option("sqlalchemy.url", url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations without a DB connection (emit SQL to stdout)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    target_schema = x_args.get("schema") or os.getenv("ALEMBIC_SCHEMA")

    if target_schema:
        # Pin search_path at connection time so all DDL lands in the test schema.
        connectable = create_engine(
            config.get_main_option("sqlalchemy.url"),
            poolclass=pool.NullPool,
            connect_args={"options": f"-csearch_path={target_schema}"},
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section) or {},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_schema,
            include_schemas=bool(target_schema),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
