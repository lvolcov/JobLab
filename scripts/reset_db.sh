#!/usr/bin/env bash
# Reset the dev DB to a known state: drop public schema, re-run migrations,
# re-seed the admin from .env. Used before Playwright e2e runs.
#
# Usage: scripts/reset_db.sh
# Created: 2026-05-19

set -euo pipefail

# Locate the project root regardless of where the script is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

if ! docker compose ps db --status running -q | grep -q .; then
  echo "db is not running — start the stack first (docker compose up -d)" >&2
  exit 1
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

echo "→ dropping public schema in ${POSTGRES_DB}"
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SQL

echo "→ alembic upgrade head"
docker compose exec -T api alembic upgrade head >/dev/null

echo "→ seeding admin"
docker compose exec -T api python /app/scripts/seed_admin.py

echo "✓ db reset complete"
