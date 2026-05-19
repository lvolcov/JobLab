"""Auth route tests: login success / failure, /auth/me, logout."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie
from joblab_api.users.models import User


async def test_login_with_wrong_password_returns_401(client: AsyncClient, regular_user: User) -> None:
    r = await client.post(
        "/auth/login", json={"email": regular_user.email, "password": "wrong"}
    )
    assert r.status_code == 401


async def test_login_success_sets_cookie_and_me_works(
    client: AsyncClient, regular_user: User
) -> None:
    r = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "user-pass-1234"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == regular_user.email
    assert "joblab_session" in r.cookies

    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == regular_user.email


async def test_me_without_cookie_returns_401(client: AsyncClient) -> None:
    r = await client.get("/auth/me")
    assert r.status_code == 401


async def test_logout_clears_cookie(client: AsyncClient, regular_user: User) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post("/auth/logout")
    assert r.status_code == 204
    # After logout the server has cleared the cookie; subsequent /me without cookie → 401.
    client.cookies.clear()
    assert (await client.get("/auth/me")).status_code == 401


async def test_inactive_user_cannot_login(client: AsyncClient, regular_user: User, db_session) -> None:
    regular_user.is_active = False
    db_session.add(regular_user)
    await db_session.commit()
    r = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "user-pass-1234"},
    )
    assert r.status_code == 401
