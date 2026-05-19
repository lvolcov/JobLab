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

    assert "encrypted_key" not in body
    assert "api_key" not in body
    assert body["masked_key"] == "****"
    assert body["is_global"] is True
    assert body["is_premium_only"] is False

    row = (
        await db_session.execute(select(LLMKey).where(LLMKey.id == body["id"]))
    ).scalar_one()
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


async def test_non_premium_user_sees_only_non_premium_globals(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    await client.post(
        "/admin/llm-keys",
        json={"provider": "openai", "label": "free pool", "api_key": "free"},
    )
    await client.post(
        "/admin/llm-keys",
        json={
            "provider": "anthropic",
            "label": "premium pool",
            "api_key": "prem",
            "is_premium_only": True,
        },
    )

    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    me = await client.get("/me/llm-keys")
    labels = {k["label"] for k in me.json()}
    assert "free pool" in labels
    assert "premium pool" not in labels


async def test_premium_user_sees_premium_global(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    await client.post(
        "/admin/llm-keys",
        json={
            "provider": "anthropic",
            "label": "premium pool",
            "api_key": "prem",
            "is_premium_only": True,
        },
    )

    regular_user.is_premium = True
    db_session.add(regular_user)
    await db_session.commit()

    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    me = await client.get("/me/llm-keys")
    labels = {k["label"] for k in me.json()}
    assert "premium pool" in labels


async def test_resolve_api_key_prefers_own_then_global(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    await client.post(
        "/admin/llm-keys",
        json={"provider": "gemini", "label": "g", "api_key": "G-GLOBAL"},
    )

    resolved = await resolve_api_key(db_session, regular_user.id, LLMProvider.GEMINI)
    assert resolved == "G-GLOBAL"

    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    await client.post(
        "/me/llm-keys",
        json={"provider": "gemini", "label": "mine", "api_key": "G-OWN"},
    )
    resolved2 = await resolve_api_key(db_session, regular_user.id, LLMProvider.GEMINI)
    assert resolved2 == "G-OWN"


async def test_resolve_api_key_skips_premium_only_for_non_premium(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    await client.post(
        "/admin/llm-keys",
        json={
            "provider": "openai",
            "label": "prem",
            "api_key": "PREM-ONLY",
            "is_premium_only": True,
        },
    )
    assert await resolve_api_key(db_session, regular_user.id, LLMProvider.OPENAI) is None


async def test_admin_can_toggle_global_key_premium(
    client: AsyncClient, admin_user: User
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    create = await client.post(
        "/admin/llm-keys",
        json={"provider": "openai", "label": "k", "api_key": "k"},
    )
    kid = create.json()["id"]
    r = await client.patch(f"/admin/llm-keys/{kid}", json={"is_premium_only": True})
    assert r.status_code == 200, r.text
    assert r.json()["is_premium_only"] is True


async def test_resolve_api_key_returns_none_when_user_has_nothing(
    regular_user: User, db_session: AsyncSession
) -> None:
    resolved = await resolve_api_key(db_session, regular_user.id, LLMProvider.OPENAI)
    assert resolved is None
