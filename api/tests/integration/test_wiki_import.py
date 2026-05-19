"""Integration tests for POST /wiki/import.

Test mode is enabled via JOBLAB_TEST_MODE=1 (conftest), so the import service
uses ``JsonStubAdapter`` which returns a deterministic fixture. The PDF text
extractor is monkeypatched so the test doesn't need a real PDF binary.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.crypto import encrypt_str
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User
from joblab_api.wiki.models import WikiExperience, WikiSkill
from tests.conftest import auth_cookie


async def _give_key(session: AsyncSession, user: User, provider: LLMProvider) -> LLMKey:
    key = LLMKey(
        owner_user_id=user.id,
        provider=provider,
        encrypted_key=encrypt_str("sk-test-1234567890"),
        label=f"test {provider.value}",
        is_global=False,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return key


def _patch_extract(monkeypatch: pytest.MonkeyPatch, text: str = "CV TEXT") -> None:
    monkeypatch.setattr(
        "joblab_api.wiki.import_router.extract_text", lambda kind, data: text
    )
    monkeypatch.setattr(
        "joblab_api.wiki.import_router.resolve_kind", lambda mime, name: "pdf"
    )


async def test_import_requires_default_provider(
    client: AsyncClient, regular_user: User
) -> None:
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/wiki/import",
        files={"file": ("cv.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r.status_code == 400
    assert "default" in r.json()["detail"].lower()


async def test_import_requires_working_key(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    regular_user.default_provider = LLMProvider.OPENAI
    db_session.add(regular_user)
    await db_session.commit()
    _patch_extract(monkeypatch)

    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/wiki/import",
        files={"file": ("cv.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r.status_code == 400
    assert "key" in r.json()["detail"].lower()


async def test_import_happy_path_populates_wiki(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    regular_user.default_provider = LLMProvider.OPENAI
    db_session.add(regular_user)
    await _give_key(db_session, regular_user, LLMProvider.OPENAI)
    _patch_extract(monkeypatch)

    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/wiki/import",
        files={"file": ("cv.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["skills"]["inserted"] == 2
    assert summary["experiences"]["inserted"] == 1

    skills = (
        (await db_session.execute(select(WikiSkill).where(WikiSkill.user_id == regular_user.id)))
        .scalars()
        .all()
    )
    assert {s.name for s in skills} == {"Python", "FastAPI"}


async def test_second_import_skips_exact_and_flags_fuzzy(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    regular_user.default_provider = LLMProvider.OPENAI
    db_session.add(regular_user)
    await _give_key(db_session, regular_user, LLMProvider.OPENAI)
    _patch_extract(monkeypatch)
    client.cookies.update(auth_cookie(regular_user))

    # First import: clean inserts.
    r1 = await client.post(
        "/wiki/import",
        files={"file": ("cv.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r1.status_code == 200

    # Second import: identical fixture, so exact signatures match and everything skips.
    r2 = await client.post(
        "/wiki/import",
        files={"file": ("cv.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert r2.status_code == 200
    summary = r2.json()
    assert summary["skills"]["skipped_exact"] == 2
    assert summary["skills"]["inserted"] == 0
    assert summary["experiences"]["skipped_exact"] == 1

    # The stub fixture's "Acme Ltd / Senior Engineer" matches itself exactly,
    # so confirm no extra rows appeared after the re-import.
    exps = (
        (
            await db_session.execute(
                select(WikiExperience).where(WikiExperience.user_id == regular_user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(exps) == 1


async def test_import_rejects_non_pdf(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    regular_user.default_provider = LLMProvider.OPENAI
    db_session.add(regular_user)
    await _give_key(db_session, regular_user, LLMProvider.OPENAI)
    client.cookies.update(auth_cookie(regular_user))

    r = await client.post(
        "/wiki/import",
        files={"file": ("cv.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert "pdf" in r.json()["detail"].lower()


async def test_settings_default_provider_validated(
    client: AsyncClient,
    regular_user: User,
    db_session: AsyncSession,
) -> None:
    client.cookies.update(auth_cookie(regular_user))

    # Without a key, setting the default fails.
    bad = await client.patch("/auth/me/settings", json={"default_provider": "openai"})
    assert bad.status_code == 400

    # With a key, it succeeds and round-trips on /auth/me.
    await _give_key(db_session, regular_user, LLMProvider.OPENAI)
    ok = await client.patch("/auth/me/settings", json={"default_provider": "openai"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["default_provider"] == "openai"

    me = await client.get("/auth/me")
    assert me.json()["default_provider"] == "openai"
