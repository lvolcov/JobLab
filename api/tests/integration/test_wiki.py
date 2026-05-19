"""Wiki CRUD tests across all six entities + cross-user isolation."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import auth_cookie
from joblab_api.users.models import User

# (path, create_payload, update_payload, updated_field, updated_value)
RESOURCES = [
    (
        "/wiki/cvs",
        {"title": "My CV", "body_md": "# CV"},
        {"title": "My CV v2"},
        "title",
        "My CV v2",
    ),
    (
        "/wiki/education",
        {"institution": "U of X", "qualification": "BSc CS"},
        {"details": "First class"},
        "details",
        "First class",
    ),
    (
        "/wiki/qualifications",
        {"name": "PMP", "issuer": "PMI"},
        {"issuer": "Project Management Institute"},
        "issuer",
        "Project Management Institute",
    ),
    (
        "/wiki/skills",
        {"name": "Python", "level": "advanced"},
        {"level": "expert"},
        "level",
        "expert",
    ),
    (
        "/wiki/projects",
        {"name": "joblab", "role": "lead"},
        {"summary": "Built a thing"},
        "summary",
        "Built a thing",
    ),
    (
        "/wiki/experiences",
        {"employer": "ACME", "title": "Engineer"},
        {"summary": "Did stuff"},
        "summary",
        "Did stuff",
    ),
]


@pytest.mark.parametrize("path,create,update,field,expected", RESOURCES)
async def test_wiki_crud_roundtrip(
    client: AsyncClient,
    regular_user: User,
    path: str,
    create: dict,
    update: dict,
    field: str,
    expected: str,
) -> None:
    client.cookies.update(auth_cookie(regular_user))

    # Create
    r = await client.post(path, json=create)
    assert r.status_code == 201, r.text
    obj = r.json()
    item_id = obj["id"]

    # List
    r = await client.get(path)
    assert r.status_code == 200
    assert any(x["id"] == item_id for x in r.json())

    # Get
    r = await client.get(f"{path}/{item_id}")
    assert r.status_code == 200

    # Update
    r = await client.patch(f"{path}/{item_id}", json=update)
    assert r.status_code == 200, r.text
    assert r.json()[field] == expected

    # Delete
    r = await client.delete(f"{path}/{item_id}")
    assert r.status_code == 204

    r = await client.get(f"{path}/{item_id}")
    assert r.status_code == 404


@pytest.mark.parametrize("path,create,_u,_f,_v", RESOURCES)
async def test_cross_user_access_returns_404(
    client: AsyncClient,
    regular_user: User,
    admin_user: User,
    path: str,
    create: dict,
    _u: dict,
    _f: str,
    _v: str,
) -> None:
    # User A creates a record
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(path, json=create)
    assert r.status_code == 201
    item_id = r.json()["id"]

    # User B tries to access it
    client.cookies.clear()
    client.cookies.update(auth_cookie(admin_user))
    assert (await client.get(f"{path}/{item_id}")).status_code == 404
    assert (await client.patch(f"{path}/{item_id}", json={})).status_code == 404
    assert (await client.delete(f"{path}/{item_id}")).status_code == 404
    # User B's list does not contain the record.
    listed = (await client.get(path)).json()
    assert all(x["id"] != item_id for x in listed)


async def test_unauthenticated_wiki_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/wiki/cvs")).status_code == 401
