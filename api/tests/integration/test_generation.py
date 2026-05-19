"""Integration tests for the generation engine.

A stub adapter replaces the real one via monkeypatching `adapter_for`.
The stub:
- captures every prompt it received
- returns scripted strings in sequence (one per attempt)
"""

from __future__ import annotations

from typing import Iterable

import pytest
from httpx import AsyncClient

from joblab_api.applications.models import ArtifactType
from joblab_api.generation import service as gen_service
from joblab_api.users.models import User
from tests.conftest import auth_cookie


class _StubAdapter:
    provider_name = "stub"

    def __init__(self, responses: Iterable[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    async def generate(self, prompt: str, *, system: str = "", **_kwargs) -> str:  # type: ignore[no-untyped-def]
        idx = len(self.calls)
        self.calls.append({"prompt": prompt, "system": system})
        return self._responses[idx] if idx < len(self._responses) else self._responses[-1]


@pytest.fixture
def stub_adapter(monkeypatch):
    """Install a per-test stub adapter; return a factory to set responses."""
    holder: dict[str, _StubAdapter] = {}

    def _install(*responses: str) -> _StubAdapter:
        stub = _StubAdapter(responses)
        holder["stub"] = stub

        def _factory(_provider, _api_key):
            return stub

        monkeypatch.setattr(gen_service, "adapter_for", _factory)
        return stub

    return _install


async def _seed_user_with_key_and_app(
    client: AsyncClient, user: User, jd_text: str = "Senior Engineer wanted"
) -> str:
    """Login user, give them an OpenAI key, create one application — return app id."""
    client.cookies.update(auth_cookie(user))
    r = await client.post(
        "/me/llm-keys",
        json={"provider": "openai", "label": "test", "api_key": "sk-test"},
    )
    assert r.status_code == 201, r.text
    r = await client.post(
        "/applications",
        json={"role_title": "Senior Engineer", "company": "ACME", "jd_text": jd_text},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------------- behaviour defaults ----------------


async def test_behaviour_default_word_limit_is_250(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    stub = stub_adapter("Behaviour content under limit.")
    app_id = await _seed_user_with_key_and_app(client, regular_user)
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={
            "type": "behaviour",
            "provider": "openai",
            "behaviour_name": "Leadership",
            # No word_limit — should default to 250.
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["word_limit"] == 250
    assert body["attempts"] == 1
    assert body["warning_flag"] is False
    assert "250" in stub.calls[0]["system"]


# ---------------- happy path / retry behaviour ----------------


async def test_first_attempt_under_limit_stops_immediately(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    stub = stub_adapter("short result")
    app_id = await _seed_user_with_key_and_app(client, regular_user)
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cover_letter", "provider": "openai", "word_limit": 50},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["attempts"] == 1
    assert body["final_word_count"] == 2
    assert body["warning_flag"] is False
    assert len(stub.calls) == 1


async def test_over_limit_triggers_retries_and_warning_flag(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    over = " ".join(["word"] * 60)  # 60 words; limit 10
    stub = stub_adapter(over, over, over)  # never under limit
    app_id = await _seed_user_with_key_and_app(client, regular_user)
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cover_letter", "provider": "openai", "word_limit": 10},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["attempts"] == 3
    assert body["warning_flag"] is True
    assert body["final_word_count"] == 60
    assert len(stub.calls) == 3
    # Retries 2 and 3 must carry the "Retry note" reminding the model it was over.
    assert "Retry note:" in stub.calls[1]["prompt"]
    assert "Retry note:" in stub.calls[2]["prompt"]


async def test_retry_succeeds_resets_warning_flag(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    over = " ".join(["word"] * 60)
    stub = stub_adapter(over, "short ok")
    app_id = await _seed_user_with_key_and_app(client, regular_user)
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cover_letter", "provider": "openai", "word_limit": 10},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["attempts"] == 2
    assert body["warning_flag"] is False
    assert body["final_word_count"] == 2


# ---------------- 400 cases ----------------


async def test_user_without_key_gets_400(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    stub_adapter("doesn't matter")
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        "/applications",
        json={"role_title": "Engineer", "company": "X", "jd_text": "..."},
    )
    app_id = r.json()["id"]

    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cv", "provider": "openai"},
    )
    assert r.status_code == 400
    assert "no openai API key" in r.json()["detail"]


async def test_behaviour_without_name_returns_400(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    stub_adapter("ignored")
    app_id = await _seed_user_with_key_and_app(client, regular_user)
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "behaviour", "provider": "openai"},
    )
    assert r.status_code == 400
    assert "behaviour_name" in r.json()["detail"]


# ---------------- blind CV redaction ----------------


async def test_blind_cv_redacts_institution_from_wiki(
    client: AsyncClient, regular_user: User, stub_adapter
) -> None:
    stub = stub_adapter("redacted result")
    client.cookies.update(auth_cookie(regular_user))
    await client.post(
        "/me/llm-keys",
        json={"provider": "openai", "label": "k", "api_key": "sk"},
    )
    await client.post(
        "/wiki/education",
        json={"institution": "Hogwarts University", "qualification": "BSc Wizardry"},
    )
    app = await client.post(
        "/applications",
        json={"role_title": "Mage", "company": "Y", "jd_text": "magic role"},
    )
    app_id = app.json()["id"]

    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "blind_cv", "provider": "openai", "word_limit": 200},
    )
    assert r.status_code == 201, r.text

    sent_prompt = stub.calls[0]["prompt"]
    assert "Hogwarts" not in sent_prompt
    assert "[redacted]" in sent_prompt
    # Non-blind generation would NOT redact — verify with a CV regeneration.
    stub2 = stub_adapter("non-blind result")
    r2 = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cv", "provider": "openai", "word_limit": 200},
    )
    assert r2.status_code == 201
    assert "Hogwarts" in stub2.calls[0]["prompt"]


# ---------------- cross-user isolation ----------------


async def test_cannot_generate_against_other_users_application(
    client: AsyncClient, regular_user: User, admin_user: User, stub_adapter
) -> None:
    stub_adapter("anything")
    # Admin creates an app
    app_id = await _seed_user_with_key_and_app(client, admin_user)
    # Regular user tries to generate on it
    client.cookies.clear()
    client.cookies.update(auth_cookie(regular_user))
    r = await client.post(
        f"/applications/{app_id}/generate",
        json={"type": "cv", "provider": "openai"},
    )
    assert r.status_code == 404
