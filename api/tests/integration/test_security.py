"""Tests for the security middleware: size limits, CSRF, rate limits.

Rate-limit tests temporarily re-enable the limiter (the test suite turns it off
via JOBLAB_TEST_MODE) so they can verify the 429 path without being throttled
across the whole run.
"""

from __future__ import annotations

import importlib

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from joblab_api.security_middleware import CSRF_COOKIE, CSRF_HEADER
from joblab_api.users.models import User
from tests.conftest import auth_cookie


async def test_oversize_request_rejected(client: AsyncClient, regular_user: User) -> None:
    client.cookies.update(auth_cookie(regular_user))
    # MAX_UPLOAD_MB defaults to 5 — declare a content-length over the limit.
    r = await client.post(
        "/wiki/cvs",
        content=b"{}",
        headers={"content-length": str(10 * 1024 * 1024)},
    )
    assert r.status_code == 413, r.text


async def test_csrf_missing_token_rejected(client: AsyncClient, regular_user: User) -> None:
    client.cookies.update(auth_cookie(regular_user))
    # Strip any CSRF cookie that earlier fixtures may have established.
    client.cookies.delete(CSRF_COOKIE)
    r = await client.post("/wiki/cvs", json={"title": "no token"})
    assert r.status_code == 403
    assert "csrf" in r.json()["detail"].lower()


async def test_csrf_header_matches_cookie(client: AsyncClient, regular_user: User) -> None:
    client.cookies.update(auth_cookie(regular_user))
    client.cookies.set(CSRF_COOKIE, "abc-123")
    r = await client.post(
        "/wiki/cvs",
        json={"title": "with token"},
        headers={CSRF_HEADER: "abc-123"},
    )
    assert r.status_code == 201, r.text


async def test_login_is_exempt_from_csrf(client: AsyncClient, regular_user: User) -> None:
    """First-ever login cannot present a CSRF cookie — must be allowed through."""
    client.cookies.clear()
    r = await client.post(
        "/auth/login",
        json={"email": regular_user.email, "password": "user-pass-1234"},
    )
    # Login should succeed; importantly, NOT 403 from CSRF.
    assert r.status_code == 200, r.text


async def test_login_rate_limit_returns_429(monkeypatch, regular_user: User) -> None:
    """Re-enable the limiter for this single test and confirm brute-force is blocked."""
    monkeypatch.delenv("JOBLAB_TEST_MODE", raising=False)
    # Reload the modules that captured the env at import time.
    from joblab_api import rate_limit

    importlib.reload(rate_limit)

    from joblab_api.auth import router as auth_router_mod
    from joblab_api import main as main_mod

    importlib.reload(auth_router_mod)
    importlib.reload(main_mod)

    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Hammer login 12 times — limit is 10/min.
        statuses = []
        for _ in range(12):
            r = await ac.post(
                "/auth/login",
                json={"email": "noone@test.local", "password": "wrong"},
            )
            statuses.append(r.status_code)
        assert 429 in statuses, statuses

    # Reload again with the env removed-then-restored cycle so other tests see the no-op limiter.
    monkeypatch.setenv("JOBLAB_TEST_MODE", "1")
    importlib.reload(rate_limit)
    importlib.reload(auth_router_mod)
    importlib.reload(main_mod)
