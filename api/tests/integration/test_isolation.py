"""Cross-user isolation matrix.

Every owner-scoped resource must return 404 (not 403) when a different user
tries to access it. We assert this exhaustively across wiki + documents +
applications + artifacts so a future regression on a single endpoint cannot
slip through.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from joblab_api.users.models import User
from tests.conftest import auth_cookie

WIKI_PATHS = [
    "/wiki/cvs",
    "/wiki/experiences",
    "/wiki/projects",
    "/wiki/skills",
    "/wiki/qualifications",
    "/wiki/education",
]

WIKI_PAYLOADS = {
    "/wiki/cvs": {"title": "private CV"},
    "/wiki/experiences": {"employer": "Acme", "title": "Engineer"},
    "/wiki/projects": {"name": "private project"},
    "/wiki/skills": {"name": "private skill"},
    "/wiki/qualifications": {"name": "private qual"},
    "/wiki/education": {"institution": "Acme U", "qualification": "BSc"},
}


@pytest.mark.parametrize("path", WIKI_PATHS)
async def test_wiki_resource_returns_404_for_other_user(
    client: AsyncClient, regular_user: User, admin_user: User, path: str
) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(path, json=WIKI_PAYLOADS[path])
    assert r.status_code == 201, r.text
    rid = r.json()["id"]

    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    assert (await client.get(f"{path}/{rid}")).status_code == 404
    assert (await client.patch(f"{path}/{rid}", json={})).status_code == 404
    assert (await client.delete(f"{path}/{rid}")).status_code == 404
    # List endpoint must not leak the foreign row either.
    others = (await client.get(path)).json()
    assert all(x["id"] != rid for x in others)


async def test_document_returns_404_for_other_user(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/documents/upload",
        files={"file": ("note.txt", b"private", "text/plain")},
    )
    assert r.status_code == 201
    doc_id = r.json()["id"]

    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    assert (await client.get(f"/documents/{doc_id}")).status_code == 404
    assert (await client.delete(f"/documents/{doc_id}")).status_code == 404
    listed = (await client.get("/documents")).json()
    assert all(d["id"] != doc_id for d in listed)


async def test_application_and_artifacts_return_404_for_other_user(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    # User A creates an application + generates an artifact (TEST_MODE flips on
    # the EchoAdapter so we don't need real LLM keys here — but the resolver
    # still requires a key entry, so we add one).
    client.cookies.update(auth_cookie(regular_user))
    await client.post(
        "/me/llm-keys",
        json={"provider": "openai", "label": "k", "api_key": "sk-fake"},
    )
    app = await client.post(
        "/applications",
        json={"role_title": "Private", "company": "X", "jd_text": "secret"},
    )
    assert app.status_code == 201
    app_id = app.json()["id"]

    # User B cannot see the application
    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    assert (await client.get(f"/applications/{app_id}")).status_code == 404
    assert (await client.patch(f"/applications/{app_id}", json={})).status_code == 404
    assert (await client.delete(f"/applications/{app_id}")).status_code == 404
    assert (await client.get(f"/applications/{app_id}/artifacts")).status_code == 404
    listed = (await client.get("/applications")).json()
    assert all(a["id"] != app_id for a in listed)

    # And cannot generate against it.
    gen = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cv", "provider": "openai"},
    )
    assert gen.status_code == 404


async def test_user_llm_key_isolation(
    client: AsyncClient, regular_user: User, admin_user: User
) -> None:
    """A user must not see or delete another user's personal LLM keys."""
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/me/llm-keys",
        json={"provider": "openai", "label": "personal", "api_key": "sk-private"},
    )
    assert r.status_code == 201
    kid = r.json()["id"]

    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    # Admin's /me/llm-keys must not include the other user's personal key.
    mine = (await client.get("/me/llm-keys")).json()
    assert all(k["id"] != kid for k in mine)
    # And admin cannot delete it via /me/llm-keys (only the owner can).
    assert (await client.delete(f"/me/llm-keys/{kid}")).status_code == 404
