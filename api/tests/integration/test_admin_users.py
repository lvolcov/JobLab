"""Admin /admin/users tests: RBAC + CRUD + password reset."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie
from joblab_api.users.models import User


async def test_non_admin_forbidden(client: AsyncClient, regular_user: User) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.get("/admin/users")
    assert r.status_code == 403


async def test_unauthenticated_unauthorised(client: AsyncClient) -> None:
    assert (await client.get("/admin/users")).status_code == 401


async def test_admin_can_create_list_reset_and_new_user_logs_in(
    client: AsyncClient, admin_user: User
) -> None:
    client.cookies.update(auth_cookie(admin_user))

    # Create
    create = await client.post(
        "/admin/users",
        json={"email": "newbie@test.local", "password": "initial-pw-12345"},
    )
    assert create.status_code == 201, create.text
    new_id = create.json()["id"]

    # List should now include both admin + new user
    listing = await client.get("/admin/users")
    assert listing.status_code == 200
    emails = {u["email"] for u in listing.json()}
    assert {"admin@test.local", "newbie@test.local"} <= emails

    # New user can log in with initial password
    client.cookies.clear()
    r = await client.post(
        "/auth/login", json={"email": "newbie@test.local", "password": "initial-pw-12345"}
    )
    assert r.status_code == 200

    # Admin resets password
    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    reset = await client.post(
        f"/admin/users/{new_id}/reset-password", json={"new_password": "rotated-pw-67890"}
    )
    assert reset.status_code == 204

    # Old password fails; new one works
    client.cookies.clear()
    r_old = await client.post(
        "/auth/login", json={"email": "newbie@test.local", "password": "initial-pw-12345"}
    )
    assert r_old.status_code == 401
    r_new = await client.post(
        "/auth/login", json={"email": "newbie@test.local", "password": "rotated-pw-67890"}
    )
    assert r_new.status_code == 200


async def test_create_user_with_duplicate_email_conflicts(
    client: AsyncClient, admin_user: User
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    first = await client.post(
        "/admin/users", json={"email": "dup@test.local", "password": "password1234"}
    )
    assert first.status_code == 201
    again = await client.post(
        "/admin/users", json={"email": "dup@test.local", "password": "password1234"}
    )
    assert again.status_code == 409


async def test_admin_cannot_delete_self(client: AsyncClient, admin_user: User) -> None:
    client.cookies.update(auth_cookie(admin_user))
    r = await client.delete(f"/admin/users/{admin_user.id}")
    assert r.status_code == 400


async def test_admin_cannot_deactivate_self(client: AsyncClient, admin_user: User) -> None:
    client.cookies.update(auth_cookie(admin_user))
    r = await client.patch(
        f"/admin/users/{admin_user.id}", json={"is_active": False}
    )
    assert r.status_code == 400
    assert "deactivate" in r.json()["detail"].lower()


async def test_last_admin_cannot_demote_self(client: AsyncClient, admin_user: User) -> None:
    client.cookies.update(auth_cookie(admin_user))
    r = await client.patch(
        f"/admin/users/{admin_user.id}", json={"is_superuser": False}
    )
    assert r.status_code == 400
    assert "last active admin" in r.json()["detail"].lower()


async def test_admin_can_demote_self_when_another_admin_exists(
    client: AsyncClient, admin_user: User
) -> None:
    client.cookies.update(auth_cookie(admin_user))
    # Create a second admin so the original is no longer the last one.
    r = await client.post(
        "/admin/users",
        json={
            "email": "second-admin@test.local",
            "password": "another-admin-1234",
            "is_superuser": True,
        },
    )
    assert r.status_code == 201

    # Now self-demotion should be allowed.
    r2 = await client.patch(
        f"/admin/users/{admin_user.id}", json={"is_superuser": False}
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["is_superuser"] is False
