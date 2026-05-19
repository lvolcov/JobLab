# joblab

[![Repo](https://img.shields.io/badge/github-lvolcov%2FJobLab-181717?logo=github)](https://github.com/lvolcov/JobLab)

Self-hosted job-application workbench. Store your career history as a structured
wiki, paste job descriptions, and generate tailored CVs, cover letters, blind
CVs, and UK Civil Service behaviours via OpenAI, Anthropic, or Gemini —
swappable per request, with a word-count guard and a 3-attempt retry loop.

Everything runs in Docker Compose: FastAPI + Postgres + React/Vite.

> Designed for one to a few users, self-hosted on a laptop or a small server.
> Not a SaaS — there is no sign-up; admins create accounts.

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Python 3.12 on the host (only for `scripts/gen_fernet_key.py`)
- (Optional) Node 20 + pnpm 9 on the host if you want to run Playwright e2e

## First-time setup

```bash
git clone https://github.com/lvolcov/JobLab.git joblab
cd joblab

cp .env.example .env

# Generate the at-rest encryption key for LLM API keys and a JWT secret.
python3 scripts/gen_fernet_key.py >> .env
python3 -c 'import secrets; print("JWT_SECRET=" + secrets.token_urlsafe(48))' >> .env

# Edit .env: change ADMIN_EMAIL and ADMIN_PASSWORD before bringing the stack up.
$EDITOR .env

docker compose build
```

## Run

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python /app/scripts/seed_admin.py
```

- API:   <http://localhost:8000/health> → `{"ok": true}` (override with `API_PORT`)
- Swagger: <http://localhost:8000/docs>
- Web:   <http://localhost:5173>

Sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`. **Change the password
immediately** via `Users → reset-password` (or by editing `.env` and re-running
`seed_admin.py`).

To stop:

```bash
docker compose down            # keeps the DB volume
docker compose down --volumes  # wipes everything
```

## Test

Backend (pytest, runs against an ephemeral Postgres schema per test):

```bash
docker compose exec api pytest -q
```

Frontend end-to-end + screenshots (Playwright on the host, against the running
stack):

```bash
cd web
pnpm install
pnpm test:e2e:install           # one-off: downloads chromium + system deps

# Reset DB to a known state and turn on the LLM stub adapter.
JOBLAB_TEST_MODE=1 docker compose up -d
../scripts/reset_db.sh

# First run captures baselines (one per route × theme); subsequent runs verify.
pnpm test:e2e:update
pnpm test:e2e
```

Screenshot tolerance is set to `maxDiffPixelRatio: 0.02` in `playwright.config.ts`
so committed baselines survive small font-rendering differences across machines.

## Daily operations

- **Reset the dev DB:** `scripts/reset_db.sh` (drops `public`, re-runs migrations,
  re-seeds the admin).
- **Rotate the Fernet key:** generate a new one, update `.env`, restart `api`,
  then have each user re-enter their keys (old ciphertexts won't decrypt).
- **Add a new user:** sign in as admin → `Users` → `New user`.
- **Hand out a shared LLM key:** admin → `Global keys` → add → use the per-row
  Assign-to-user picker.

## Layout

```
joblab/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── ui-spec.md
├── scripts/
│   ├── gen_fernet_key.py
│   ├── seed_admin.py
│   └── reset_db.sh
├── api/                       # FastAPI + SQLModel + Alembic
└── web/                       # React + Vite + Tailwind + Playwright
```

## What lives where

- **Architecture overview:** [`docs/architecture.md`](docs/architecture.md)
- **API reference:** [`docs/api.md`](docs/api.md)
- **UI conventions and design tokens:** [`docs/ui-spec.md`](docs/ui-spec.md)

## Security defaults

- LLM API keys are Fernet-encrypted at rest; the API never returns either the
  plaintext or the ciphertext.
- Sessions use httpOnly, SameSite=Lax JWT cookies (7-day TTL).
- CSRF: double-submit cookie + `X-CSRF-Token` header required on every unsafe
  request (login is exempt).
- `POST /auth/login` is rate-limited to 10/min/IP.
- `POST /applications/{id}/generate` is rate-limited to 20/hour/IP.
- Uploads are capped at `MAX_UPLOAD_MB` (default 5 MB); oversized requests are
  rejected at the middleware before reaching any parser.
- All owner-scoped queries filter by `user_id = current_user.id`; the cross-user
  isolation test matrix asserts this for every resource.

## Licence

Private project. Not for redistribution.
