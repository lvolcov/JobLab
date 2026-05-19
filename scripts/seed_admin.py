#!/usr/bin/env python3
"""Seed the initial admin user from ADMIN_EMAIL / ADMIN_PASSWORD.

Purpose: idempotent first-boot helper. Run via:
    docker compose exec api python /app/scripts/seed_admin.py

Behaviour:
- If a user with ADMIN_EMAIL exists: ensure it is active + superuser; do not change password.
- Otherwise: create it as admin with the given password.

Created: 2026-05-19
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running this script directly inside the container (PYTHONPATH already includes /app/src).
SRC = Path(__file__).resolve().parents[1] / "api" / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlmodel import select  # noqa: E402

from joblab_api.auth.security import hash_password  # noqa: E402
from joblab_api.config import get_settings  # noqa: E402
from joblab_api.users.models import User  # noqa: E402


async def main() -> int:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set", file=sys.stderr)
        return 2

    engine = create_async_engine(settings.async_database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            existing = (
                await session.execute(select(User).where(User.email == settings.admin_email))
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    User(
                        email=settings.admin_email,
                        hashed_password=hash_password(settings.admin_password),
                        is_superuser=True,
                        is_active=True,
                        is_verified=True,
                    )
                )
                await session.commit()
                print(f"created admin {settings.admin_email}")
            else:
                changed = False
                if not existing.is_superuser:
                    existing.is_superuser = True
                    changed = True
                if not existing.is_active:
                    existing.is_active = True
                    changed = True
                if changed:
                    await session.commit()
                    print(f"promoted existing user {settings.admin_email} to admin")
                else:
                    print(f"admin {settings.admin_email} already present; no changes")
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
