# Architecture

joblab is a single-tenant, self-hosted job-application workbench. Three services
in one Compose stack: a Postgres database, a FastAPI backend, and a React SPA.

## Runtime topology

```
                    ┌────────────────────┐
  Browser ────────► │  web (Vite, :5173) │
                    └────────┬───────────┘
                             │ fetch (cookie + CSRF header)
                             ▼
                    ┌────────────────────┐
                    │  api (FastAPI, 8000)│──── HTTPS ───► OpenAI / Anthropic / Gemini
                    └────────┬───────────┘
                             │ asyncpg / SQLAlchemy
                             ▼
                    ┌────────────────────┐
                    │  db (Postgres 16)  │
                    └────────────────────┘
```

All services share one Docker network. The host maps:

| Service | Host port | Container port |
| ------- | --------- | -------------- |
| db      | 5432      | 5432           |
| api     | `${API_PORT}` (default 8000; 8010 in local dev) | 8000 |
| web     | 5173      | 5173           |

The web service is intended for development. In production you would build a
static bundle (`pnpm build`) and serve it through nginx or similar, with the API
behind the same hostname so cookies travel without CORS quirks.

## Backend

The backend is a single FastAPI app composed of focused domain modules:

```
joblab_api/
├── main.py                 # FastAPI factory + middleware wiring
├── config.py               # Pydantic Settings (env-driven)
├── db.py                   # async engine, SessionFactory, SessionDep
├── crypto.py               # Fernet encrypt/decrypt for LLM keys
├── word_count.py
├── rate_limit.py           # slowapi limiter + handler
├── security_middleware.py  # request-size + CSRF middleware
├── auth/                   # cookie/JWT sessions, password hashing
├── users/                  # admin /admin/users CRUD
├── llm/                    # provider abstraction + adapters + key vault
├── wiki/                   # six entities behind one generic CRUD factory;
│                           # also CV-import pipeline (PDF → LLM JSON → dedup → rows)
│                           # lists sorted by date (start/date_awarded) desc, nulls last
├── documents/              # uploads + text extraction (pdf, docx, txt, md)
├── applications/           # per-role records + artifact persistence
├── generation/             # prompt assembly + retry loop
└── data/
    └── cs_behaviours.py    # Civil Service behaviour descriptors per grade (EO…Grade 6)
```

### CV-import pipeline (`wiki/import_*`)

1. `POST /wiki/import` accepts a PDF, extracts text via the existing parser.
2. Resolves the user's `default_provider` and a working key for it.
3. `import_service.parse_with_llm` builds a structured-JSON prompt (`JSON_SCHEMA_HINT`) and calls the adapter. One retry on `json.JSONDecodeError` / Pydantic `ValidationError`, with a corrective hint appended.
4. `apply_extracted` walks each of the six entity lists and runs `dedup.classify`: exact normalised-signature match → skip; rapidfuzz `token_set_ratio ≥ 85` → insert with `possible_duplicate_of_id` set; otherwise → insert clean.
5. Returns an `ImportResult` with per-entity `{inserted, skipped_exact, flagged_duplicate}` counts.

`JOBLAB_TEST_MODE=1` swaps the adapter for `JsonStubAdapter` (deterministic fixture) so the suite never hits a real provider.

### Why SQLModel + Alembic

SQLModel gives us a single declaration that satisfies both Pydantic and SQLAlchemy
without duplicate schemas. Alembic owns the migration story; the test fixture
recreates an ephemeral Postgres schema per test (`tests/conftest.py`).

### Why an `adapter_for()` indirection

The generation engine resolves an LLM key for `(user, provider)` then calls a
provider through a tiny `LLMAdapter` protocol. The factory is a single function
so two things are possible without code surgery:

1. **Tests** monkeypatch `adapter_for` to inject deterministic stubs.
2. **E2E** sets `JOBLAB_TEST_MODE=1`; the factory then returns `EchoAdapter`
   from `generation/test_adapter.py` so Playwright doesn't burn credits.

### Generation retry loop

`generation/service.py` runs up to **3** attempts. After each, we count words.
First under-limit response wins; if all three exceed the cap, the shortest is
persisted with `warning_flag=true` and a human-readable banner in the UI. The
prompt builder injects an explicit "Retry note: previous was N words…" string
on attempts 2 and 3 so the model knows what to fix.

## Security model

| Threat                                  | Mitigation                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| Credential leakage (LLM keys)           | Fernet-encrypted at rest; never returned by the API; ciphertext column only.                 |
| Auth bypass / privilege escalation      | httpOnly + SameSite=Lax JWT cookie; per-request `CurrentAdmin` dependency on `/admin/*`.     |
| CSRF on state-changing requests         | Double-submit token: `joblab_csrf` cookie (non-HttpOnly) + `X-CSRF-Token` header must match. |
| Brute-force login                       | `slowapi` 10 attempts/minute per remote IP on `POST /auth/login`.                            |
| LLM cost abuse                          | `slowapi` 20 generations/hour per remote IP on `POST /applications/{id}/generate`.           |
| Oversized requests / DoS via uploads    | Request-size middleware rejects bodies above `MAX_UPLOAD_MB` before any parser runs.         |
| Prompt injection from JD / docs         | User content is wrapped in `<<<…>>>` delimiters inside a system-defined frame.               |
| Data exfiltration across users          | Every owner-scoped query filters by `user_id = current_user.id`; integration tests assert.   |

CORS is allowlisted from `CORS_ORIGINS`. `credentials: "include"` is required on
the client to send cookies.

## Frontend

React 18 + Vite + TypeScript + TailwindCSS. State via TanStack Query for server
state; a tiny `AuthProvider` for session. No global store library — everything
that isn't server state is component-local.

Theme is keyed off a `.dark` class on `<html>`. The choice is read from
`localStorage` (`joblab.theme`) before first paint to avoid a flash of wrong
theme. CSS variables (`--bg`, `--surface`, `--text`, …) switch on `.dark`.

Routing is a flat tree under two protected layouts (one user, one admin):

```
/login                              public
/                                   dashboard
/wiki/:entity                       cvs | experiences | projects | skills | qualifications | education
/applications                       list
/applications/:id                   detail + generator + artifacts
/settings                           default AI provider + personal LLM keys + visible globals
/admin/users                        admin-only — CRUD + reset password + admin/premium toggles
/admin/llm-keys                     admin-only — global keys with premium-only flag
```

A site-wide amber banner appears on every protected route (except `/settings`) while the current user has no `default_provider` set — AI features (CV import, generation) are unavailable until that's fixed.

## Database schema (current head: `0006_premium_flag`)

```
users(id PK, email UNIQUE, hashed_password, is_active, is_superuser, is_verified,
      is_premium, default_provider, created_at)

llm_keys(id PK, owner_user_id FK users.id NULL, provider, encrypted_key, label,
         is_global, is_premium_only, created_at)

# llm_key_assignments was removed in 0006 — per-user assignment was replaced by
# the (users.is_premium × llm_keys.is_premium_only) tier model.

wiki_cvs / wiki_experiences / wiki_projects / wiki_skills /
wiki_qualifications / wiki_education
    (id PK, user_id FK users.id, created_at, updated_at, … entity fields,
     possible_duplicate_of_id FK self NULL)

documents(id PK, user_id FK users.id, filename, mime, size_bytes, parsed_text, created_at)

applications(id PK, user_id FK users.id, role_title, company, jd_text, status,
             applied_at, feedback, notes, created_at, updated_at)

application_artifacts(id PK, application_id FK applications.id, type, provider,
                      word_limit, attempts, final_word_count, warning_flag,
                      content, extra_instructions, behaviour_name, grade, created_at)
```

All foreign keys are `ON DELETE CASCADE` so deleting a user wipes their wiki,
documents, applications, artifacts, and personal keys.

## Testing strategy

- **Unit (`tests/unit/`):** crypto round-trips, adapter HTTP shapes (mocked
  transport), word counting.
- **Integration (`tests/integration/`):** schema migrations, auth, admin RBAC,
  wiki CRUD, document parsing/upload, LLM key vault + resolver, generation
  retry loop, **cross-user isolation matrix**, security middleware (CSRF, size,
  rate limit).
- **E2E (`web/tests/e2e/`):** login + reload-persistence, wiki create flow,
  document upload via API with browser cookies, generator end-to-end against the
  stub adapter, application feedback round-trip, screenshot baselines for every
  top-level route in light + dark.

Tests use an **ephemeral Postgres schema per test** (`tests/conftest.py`),
created with `CREATE SCHEMA test_<uuid>` and dropped at teardown, so they neither
collide with each other nor with whatever is in `public`.
