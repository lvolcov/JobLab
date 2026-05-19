# CLAUDE.md — joblab project instructions for Claude Code sessions

> Read this in any new conversation about this repo. It's a project-specific
> companion to your global `~/.claude/CLAUDE.md`. Anything here overrides
> defaults; anything not here defers to global.

## What this project is

**joblab** is a self-hosted job-application workbench. One developer, a handful
of users, runs entirely in Docker Compose on a laptop or small server.

A user (after admin invites them) builds a **structured wiki** of their career
— CVs, experiences, projects, skills, qualifications, education, plus uploaded
documents (pdf/docx/txt/md, parsed to text). They then create an **application**
record for a role they want to apply for, paste the JD, and the app generates
**one of four document types** with their choice of LLM provider:

- `cv` — tailored CV in markdown
- `cover_letter` — concise letter
- `blind_cv` — UK Civil Service style: name, age, gender, institutions stripped
- `behaviour` — UK Civil Service STAR response (defaults to 250 words)

The generation pipeline counts words, retries up to **3 times** if over the
limit, and persists the result as an `application_artifact` with `attempts`,
`final_word_count`, and a `warning_flag` if the cap couldn't be met.

LLM keys are Fernet-encrypted at rest. Admins can supply **global keys** and
assign them to specific users; users can also bring their **own keys**.
Resolution is "own key first, otherwise an assigned global, otherwise 400".

## What this project is **not**

- Not a SaaS. No public sign-up. Admins create accounts.
- Not multi-tenant. Single-instance, single-database.
- Not a hosted offering for someone else's job-search. Built for the
  developer's own use first, with the option of inviting a few collaborators.

## Tech stack

| Layer    | Choice                                                              |
| -------- | ------------------------------------------------------------------- |
| Backend  | Python 3.12, FastAPI 0.115, SQLModel, Alembic, async psycopg3       |
| DB       | Postgres 16                                                         |
| Auth     | bcrypt + PyJWT in an httpOnly SameSite=Lax cookie (7-day TTL)       |
| Crypto   | `cryptography.Fernet` for at-rest LLM keys                          |
| Limiter  | `slowapi` (10/min on login, 20/hour on generate)                    |
| LLM      | Custom protocol + adapters for OpenAI, Anthropic, Gemini            |
| Frontend | React 18 + Vite 5 + TypeScript + TailwindCSS 3 + TanStack Query     |
| Icons    | `lucide-react` (no emojis as UI icons — ever)                       |
| E2E      | Playwright 1.49 + screenshot baselines per route × theme            |
| Compose  | Three services: `db`, `api`, `web`                                  |

## Repo layout

```
joblab/
├── docker-compose.yml             # db + api + web; the only orchestration in use
├── .env.example                   # copy to .env; never commit secrets
├── README.md
├── CLAUDE.md                      # this file
├── docs/
│   ├── architecture.md            # topology, modules, threat table, DB schema
│   ├── api.md                     # full endpoint reference
│   └── ui-spec.md                 # design tokens, components, page-by-page
├── scripts/
│   ├── gen_fernet_key.py          # generate FERNET_KEY for .env
│   ├── seed_admin.py              # create/promote/reactivate admin from .env
│   └── reset_db.sh                # drop public schema, re-migrate, re-seed
├── api/
│   ├── Dockerfile                 # python:3.12-slim, uv-managed deps, non-root user
│   ├── pyproject.toml             # runtime + dev deps
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                 # supports -x schema=... for test isolation
│   │   └── versions/
│   │       ├── 0001_init.py                  # users + llm_keys
│   │       ├── 0002_wiki_documents.py        # 6 wiki tables + documents
│   │       ├── 0003_llm_assignments.py       # global-key → user mapping
│   │       └── 0004_applications.py          # applications + artifacts
│   ├── src/joblab_api/
│   │   ├── main.py                # FastAPI app + middleware composition
│   │   ├── config.py              # Pydantic Settings
│   │   ├── db.py                  # async engine, SessionFactory, SessionDep
│   │   ├── crypto.py              # Fernet wrapper
│   │   ├── word_count.py
│   │   ├── rate_limit.py          # slowapi config
│   │   ├── security_middleware.py # CSRF + request-size cap
│   │   ├── models.py              # aggregate import; registers every table
│   │   ├── auth/                  # security, deps, schemas, router
│   │   ├── users/                 # admin user mgmt
│   │   ├── llm/                   # provider protocol + adapters + key vault
│   │   ├── wiki/                  # 6 entities behind a generic CRUD factory
│   │   ├── documents/             # uploads + pdf/docx/txt/md parsing
│   │   ├── applications/          # application records + artifacts
│   │   └── generation/            # prompt builder + retry loop + stub adapter
│   └── tests/
│       ├── conftest.py            # ephemeral-schema fixture, csrf-aware client
│       ├── unit/                  # crypto, word_count, adapters (mocked HTTP)
│       └── integration/           # auth, admin, wiki, documents, llm_keys,
│                                  # generation, isolation matrix, security
├── web/
│   ├── Dockerfile                 # node:20-alpine, pnpm via corepack
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts         # design tokens — Plus Jakarta Sans, teal+orange
│   ├── playwright.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx               # theme applied before render → providers → router
│   │   ├── app/router.tsx
│   │   ├── styles/globals.css     # Tailwind + CSS variables for light/dark
│   │   ├── lib/
│   │   │   ├── api.ts             # typed fetch client + shared types
│   │   │   ├── auth.tsx           # <AuthProvider> + useAuth
│   │   │   └── theme.ts           # localStorage-backed dark mode
│   │   ├── components/
│   │   │   ├── ui.tsx             # Button, Input, Field, Card, EmptyState, Spinner
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Topbar.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   └── ArtifactViewer.tsx
│   │   └── routes/
│   │       ├── layout.tsx         # protected layout (regular + adminOnly)
│   │       ├── login.tsx
│   │       ├── dashboard.tsx
│   │       ├── wiki/{index,entity}.tsx
│   │       ├── applications/{index,detail}.tsx
│   │       ├── settings/index.tsx
│   │       └── admin/{users,llm-keys}.tsx
│   └── tests/e2e/                 # auth, wiki, documents, generation, screenshots
```

## How to develop

```bash
# First time
cp .env.example .env
python3 scripts/gen_fernet_key.py >> .env
python3 -c 'import secrets; print("JWT_SECRET=" + secrets.token_urlsafe(48))' >> .env
$EDITOR .env                       # set ADMIN_EMAIL / ADMIN_PASSWORD
docker compose build

# Bring up
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python /app/scripts/seed_admin.py

# Run tests
docker compose exec api pytest -q        # backend (~77 tests, ~25s)
cd web && pnpm install && pnpm test:e2e  # frontend (after pnpm test:e2e:install one-off)
```

## Code conventions

### Backend (Python)

- **PEP 8**, type hints on every public signature, Google-style docstrings on
  modules and non-trivial functions only. Don't write a docstring for a
  three-line internal helper.
- `pathlib` over `os.path`. f-strings over `.format()`.
- `httpx` over `requests`. Always async in API code.
- Pydantic models for every request/response. Enums for any closed set
  (provider, status, artifact type).
- Dependency injection for shared logic — see `auth/deps.py`'s `CurrentUser` /
  `CurrentAdmin`.
- Every owner-scoped query MUST filter by `user_id == current_user.id`. The
  `test_isolation.py` matrix catches regressions; don't break it.
- **Migrations are source of truth.** When adding a table, hand-write the
  Alembic migration (don't rely on autogenerate — it doesn't handle our enums
  cleanly).
- **CSRF + slowapi quirk:** routes decorated with `@limiter.limit(...)` or
  living next to one must NOT use `from __future__ import annotations` —
  FastAPI body inference breaks because annotations stay as `ForwardRef`s
  through the wrapper. The same is true for routes whose body schemas are
  resolved via a factory function (e.g. `wiki/crud.py`).
- **`-> None` on 204 routes:** don't add it. FastAPI 0.115 treats `None` as a
  response body type and asserts. Just leave the return annotation off.

### Frontend (TypeScript / React)

- **No emojis as UI icons.** Lucide React only, sized `h-4 w-4` by default.
- All clickable elements need `cursor-pointer`. Hover states must be smooth
  (`transition-colors duration-150`) and must NOT cause layout shift.
- Forms use `<Field label htmlFor>` from `components/ui.tsx`. Always pair
  labels with controls.
- TanStack Query for server state; component-local `useState` for UI state.
  Don't introduce a global store.
- Theme via the `.dark` class on `<html>` and CSS variables in `globals.css`.
  Don't hard-code colours; reference `bg-brand-600`, `text-muted`, etc.
- API calls go through `lib/api.ts`. It handles `credentials: "include"` and
  the CSRF header automatically — don't bypass it.

### Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`,
  `test:`.
- Don't commit to `main` directly except for the project owner's initial
  push. PR-based after that.
- Never commit `.env`, real API keys, or Playwright screenshot diffs.

### Tests

- Backend: pytest, one test file per domain module, ephemeral Postgres schema
  fixture in `conftest.py`. Integration tests use the `AsyncClient` fixture
  (already wired with CSRF cookie + header).
- Frontend: Playwright. `JOBLAB_TEST_MODE=1` makes `adapter_for()` return
  `EchoAdapter` so generation tests don't burn LLM credits.
- Screenshot baselines are host-dependent (font rendering). First run uses
  `pnpm test:e2e:update`; commit those baselines once and the diff tolerance
  (`maxDiffPixelRatio: 0.02`) absorbs minor drift.

## Things that will bite you

- **Anonymous `node_modules` volume.** `docker-compose.yml` mounts
  `/app/node_modules` as an anonymous volume so host bind doesn't clobber it.
  If you change `web/package.json`, you MUST recreate with `-V`:
  `docker compose up -d web --force-recreate -V`. Otherwise old deps stick.
- **Port 8000 sometimes taken on the host.** `.env.example` keeps `API_PORT=8000`;
  local `.env` may use `8010` or similar.
- **Admin self-lockout.** The backend now blocks self-deactivate and
  last-admin self-demote — don't remove those guards. Self-delete was always
  blocked.
- **Reset DB.** `scripts/reset_db.sh` drops the `public` schema and re-runs
  migrations. Use it before Playwright e2e to get a known state.
- **CSRF cookie domain.** Local dev uses `localhost` so cookies are visible
  across `:5173` ↔ `:8010`. In production, put api and web behind the same
  hostname (reverse proxy) so the SPA can read the CSRF cookie.

## When asked to add a new feature

1. Read `docs/architecture.md` for the threat model and module shape.
2. Read `docs/api.md` to see if the new endpoint fits an existing pattern
   (most owner-scoped CRUD goes via `wiki/crud.py`'s factory).
3. Backend first: model → migration → schema → router → tests. Run
   `docker compose exec api pytest -q` after each step.
4. Frontend: add types to `lib/api.ts`, then a route, then wire into
   `app/router.tsx`. Don't introduce new dependencies without confirming
   nothing in the existing stack already does the job.
5. Update docs: `architecture.md` if structural, `api.md` always, `ui-spec.md`
   if a new pattern was introduced.
6. Update `CLAUDE.md` (this file) only if a new convention or gotcha appears.

## When asked to debug

1. Reproduce against the running stack: `curl` the endpoint with a session
   cookie. Confirm the failure mode at the API layer first; don't chase a
   frontend symptom of a backend bug.
2. For 422s, ALWAYS print the response body — FastAPI's validation detail
   tells you exactly which field is in the wrong location (the
   `ForwardRef → query` symptom from earlier is a classic giveaway).
3. For 403s on unsafe methods, suspect CSRF: confirm both the cookie and the
   header exist and match.
4. For SQLAlchemy `MissingGreenlet`, suspect that a session-bound ORM instance
   had its attributes expired (rollback after IntegrityError is the common
   cause). Re-fetch, or restructure to avoid the rollback.

## How to ship

- One commit per logical change. PRs target `main`.
- CI is not configured yet (intentional — single-developer project). When
  added, it should run `docker compose build`, `pytest`, and the Playwright
  suite against a freshly-reset DB.
- Tag releases on `main` only after running both the backend and frontend
  suites locally.
