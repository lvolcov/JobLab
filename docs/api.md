# API reference

Base URL in local dev: `http://localhost:8010` (host port set by `API_PORT`).
Interactive docs (Swagger): `${BASE_URL}/docs`.

All authenticated endpoints require:

- **Session cookie** `joblab_session` (httpOnly, set by `POST /auth/login`).
- **CSRF header** `X-CSRF-Token` matching the `joblab_csrf` cookie on every
  `POST`, `PATCH`, `PUT`, `DELETE` (login is exempt).

The client at `web/src/lib/api.ts` does both automatically.

---

## Auth

| Method | Path           | Notes                                                 |
| ------ | -------------- | ----------------------------------------------------- |
| POST   | `/auth/login`  | `{email, password}` → sets session cookie. **10/min.** |
| POST   | `/auth/logout` | Clears the session cookie.                            |
| GET    | `/auth/me`     | Returns the current user.                             |

## Admin — users (`is_superuser` required)

| Method | Path                                  | Body                              |
| ------ | ------------------------------------- | --------------------------------- |
| GET    | `/admin/users`                        | —                                 |
| POST   | `/admin/users`                        | `{email, password, is_superuser}` |
| PATCH  | `/admin/users/{user_id}`              | `{email?, is_active?, is_superuser?}` |
| POST   | `/admin/users/{user_id}/reset-password` | `{new_password}` (min 8 chars)  |
| DELETE | `/admin/users/{user_id}`              | Cannot delete self.               |

## Admin — global LLM keys

| Method | Path                                                | Body                              |
| ------ | --------------------------------------------------- | --------------------------------- |
| GET    | `/admin/llm-keys`                                   | —                                 |
| POST   | `/admin/llm-keys`                                   | `{provider, label, api_key}`      |
| DELETE | `/admin/llm-keys/{key_id}`                          | —                                 |
| PATCH  | `/admin/llm-keys/{key_id}`                          | `{is_premium_only?, label?}`      |
| POST   | `/admin/llm-keys/test`                              | `{provider, api_key}` — 1-token probe. |

Responses never include the raw or encrypted key — only `masked_key: "****"`.

## User — personal LLM keys

| Method | Path                       | Body                          |
| ------ | -------------------------- | ----------------------------- |
| GET    | `/me/llm-keys`             | Lists own keys + visible globals (filtered by `is_premium_only` vs `users.is_premium`). |
| POST   | `/me/llm-keys`             | `{provider, label, api_key}`  |
| POST   | `/me/llm-keys/test`        | `{provider, api_key}` — 1-token probe; returns `{ok, error?}`. |
| DELETE | `/me/llm-keys/{key_id}`    | Owner only.                   |
| GET    | `/me/llm-keys/providers`   | Lists supported provider enum values. |

`provider ∈ {openai, anthropic, gemini}`.

## Wiki

Each entity is a parallel REST resource at `/wiki/{cvs|experiences|projects|skills|qualifications|education}`.

| Method | Path                            | Body / notes                        |
| ------ | ------------------------------- | ----------------------------------- |
| GET    | `/wiki/{entity}`                | Lists current user's entries.       |
| POST   | `/wiki/{entity}`                | Entity-specific create payload.     |
| GET    | `/wiki/{entity}/{id}`           | 404 across users.                   |
| PATCH  | `/wiki/{entity}/{id}`           | Partial update.                     |
| DELETE | `/wiki/{entity}/{id}`           | —                                   |
| POST   | `/wiki/import`                  | `multipart/form-data`; `file` of PDF. Extracts CV via the user's default AI provider and populates all six entity tables. Returns `ImportResult` with per-entity `{inserted, skipped_exact, flagged_duplicate}` counts. Exact-signature matches are skipped; high-similarity matches are inserted with `possible_duplicate_of_id` set. Requires `default_provider` set in Settings and a working key for that provider. |

Every wiki row also carries `possible_duplicate_of_id`: nullable self-FK populated by the importer when an inserted item closely resembles an existing one. The UI renders an amber "possible duplicate" badge whenever it is non-null.

### Settings

| Method | Path                  | Body / notes                                                |
| ------ | --------------------- | ----------------------------------------------------------- |
| PATCH  | `/auth/me/settings`   | `{default_provider: "openai"|"anthropic"|"gemini"|null}`. Rejected (400) unless the user has a working key for that provider. |

`GET /auth/me` returns `default_provider` and `is_premium` alongside the existing fields.

### Premium tiering

Global LLM keys can be marked `is_premium_only=True` (admin-only field on `POST /admin/llm-keys` and `PATCH /admin/llm-keys/{id}`). Users with `is_premium=True` see all global keys; non-premium users only see globals where `is_premium_only=False`. Per-user assignment (`/admin/llm-keys/{id}/assign`) was removed in favour of this flag.

| Method | Path                              | Body                                              |
| ------ | --------------------------------- | ------------------------------------------------- |
| PATCH  | `/admin/llm-keys/{id}`            | `{is_premium_only?: bool, label?: string}`        |
| PATCH  | `/admin/users/{id}`               | now also accepts `is_premium: bool`               |
| POST   | `/admin/llm-keys/test`            | Same shape as `/me/llm-keys/test`; admin-only.    |

## Documents

| Method | Path                       | Body                                                       |
| ------ | -------------------------- | ---------------------------------------------------------- |
| POST   | `/documents/upload`        | `multipart/form-data`; `file` of pdf/docx/txt/md; ≤ 5 MB.  |
| GET    | `/documents`               | —                                                          |
| GET    | `/documents/{doc_id}`      | —                                                          |
| DELETE | `/documents/{doc_id}`      | —                                                          |

Returns `415` on disallowed MIME, `413` on oversize, `400` on parser failure.

## Applications

| Method | Path                              | Body                                                                  |
| ------ | --------------------------------- | --------------------------------------------------------------------- |
| GET    | `/applications`                   | —                                                                     |
| POST   | `/applications`                   | `{role_title, company?, jd_text?, status?, applied_at?, feedback?, notes?}` |
| GET    | `/applications/{app_id}`          | —                                                                     |
| PATCH  | `/applications/{app_id}`          | Partial update.                                                       |
| DELETE | `/applications/{app_id}`          | Cascades to artifacts.                                                |
| GET    | `/applications/{app_id}/artifacts` | Lists past generations, newest first.                                 |

`status ∈ {applied, screening, interview, offer, rejected, withdrawn}`.

## Generation

```
POST /applications/{app_id}/generate
```

```jsonc
{
  "type": "cv | cover_letter | blind_cv | behaviour",
  "provider": "openai | anthropic | gemini",
  "word_limit": 250,             // optional; defaults: cv 800, cover_letter 400, blind_cv 800, behaviour 250
  "extra_instructions": "",      // optional; forwarded into the prompt
  "behaviour_name": "Leadership" // required when type=behaviour, else null
}
```

Rate limited to **20 per hour** per remote IP. Returns `400` if the user has
no own or assigned key for the chosen provider. Persists an
`application_artifacts` row with `attempts`, `final_word_count`, and
`warning_flag`. After 3 attempts above the limit, returns the shortest with
`warning_flag=true`.

## Error format

All errors use FastAPI's default shape:

```json
{ "detail": "human-readable message" }
```

Validation errors (`422`) surface a list:

```json
{ "detail": [{"loc": ["body", "email"], "msg": "field required", "type": "missing"}] }
```
