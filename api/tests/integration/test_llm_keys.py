"""Integration tests for LLM key management + key resolution."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.crypto import decrypt_str
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.llm.service import resolve_api_key
from joblab_api.users.models import User
from tests.conftest import auth_cookie


async def test_admin_creates_global_key_encrypted_in_db(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    r = await client.post(
        "/admin/llm-keys",
        json={"provider": "openai", "label": "shared openai", "api_key": "sk-RAW-SECRET-1234"},
    )
    assert r.status_code == 201, r.text
    body = r.json()

    # Response never includes the raw key
    assert "encrypted_key" not in body
    assert "api_key" not in body
    assert body["masked_key"] == "****"
    assert body["is_global"] is True

    # DB row stores ciphertext, not plaintext
    row = (
        await db_session.execute(select(LLMKey).where(LLMKey.id == body["id"]))
    ).scalar_one()
    assert row.encrypted_key != "sk-RAW-SECRET-1234"
    assert "sk-RAW-SECRET-1234" not in row.encrypted_key
    assert decrypt_str(row.encrypted_key) == "sk-RAW-SECRET-1234"


async def test_non_admin_cannot_manage_global_keys(
    client: AsyncClient, regular_user: User
) -> None:
    client.cookies.update(auth_cookie(regular_user))
    assert (await client.get("/admin/llm-keys")).status_code == 403
    r = await client.post(
        "/admin/llm-keys",
        json={"provider": "openai", "label": "x", "api_key": "x"},
    )
    assert r.status_code == 403


async def test_user_creates_own_key_and_lists_it(
    client: AsyncClient, regular_user: User
) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/me/llm-keys",
        json={"provider": "anthropic", "label": "my anthropic", "api_key": "ant-secret"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["owner_user_id"] == str(regular_user.id)

    listing = await client.get("/me/llm-keys")
    assert listing.status_code == 200
    assert len(listing.json()) == 1


async def test_admin_assigns_global_key_to_user_and_user_sees_it(
    client: AsyncClient, admin_user: User, regular_user: User
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    create = await client.post(
        "/admin/llm-keys",
        json={"provider": "gemini", "label": "team gemini", "api_key": "g-secret"},
    )
    key_id = create.json()["id"]
    r = await client.post(
        f"/admin/llm-keys/{key_id}/assign", json={"user_id": str(regular_user.id)}
    )
    assert r.status_code == 201

    # Idempotent reassignment
    r2 = await client.post(
        f"/admin/llm-keys/{key_id}/assign", json={"user_id": str(regular_user.id)}
    )
    assert r2.status_code == 201

    # The user now sees the assigned key in /me/llm-keys
    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    me = await client.get("/me/llm-keys")
    assert me.status_code == 200
    assert any(k["id"] == key_id and k["is_global"] for k in me.json())


async def test_resolve_api_key_prefers_own_then_assigned(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    # Admin creates + assigns a global gemini key
    client.cookies.update(auth_cookie(admin_user))
    create = await client.post(
        "/admin/llm-keys",
        json={"provider": "gemini", "label": "g", "api_key": "G-GLOBAL"},
    )
    gid = create.json()["id"]
    await client.post(
        f"/admin/llm-keys/{gid}/assign", json={"user_id": str(regular_user.id)}
    )

    # User has no own gemini key → resolves to assigned
    resolved = await resolve_api_key(db_session, regular_user.id, LLMProvider.GEMINI)
    assert resolved == "G-GLOBAL"

    # User adds their own gemini key → resolution prefers own
    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    await client.post(
        "/me/llm-keys",
        json={"provider": "gemini", "label": "mine", "api_key": "G-OWN"},
    )
    resolved2 = await resolve_api_key(db_session, regular_user.id, LLMProvider.GEMINI)
    assert resolved2 == "G-OWN"


async def test_resolve_api_key_returns_none_when_user_has_nothing(
    regular_user: User, db_session: AsyncSession
) -> None:
    resolved = await resolve_api_key(db_session, regular_user.id, LLMProvider.OPENAI)
    assert resolved is None
