"""Adapter tests against mocked HTTP transport."""

import json
from typing import Any

import httpx
import pytest

from joblab_api.llm.adapters.anthropic import AnthropicAdapter
from joblab_api.llm.adapters.gemini import GeminiAdapter
from joblab_api.llm.adapters.openai import OpenAIAdapter
from joblab_api.llm.provider import LLMError


def _mock_transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


@pytest.fixture
def patch_async_client(monkeypatch):
    """Return a function that monkey-patches httpx.AsyncClient to use a MockTransport."""
    captured: dict[str, Any] = {}

    def _install(response_factory):
        def handler(request: httpx.Request) -> httpx.Response:
            captured["request"] = request
            return response_factory(request)

        transport = _mock_transport(handler)
        original = httpx.AsyncClient

        class _Patched(original):  # type: ignore[misc, valid-type]
            def __init__(self, *args, **kwargs):
                kwargs["transport"] = transport
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", _Patched)
        return captured

    return _install


async def test_openai_adapter_parses_response(patch_async_client) -> None:
    captured = patch_async_client(
        lambda req: httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hello from openai"}}]},
        )
    )
    out = await OpenAIAdapter("sk-fake").generate("hi", system="be brief")
    assert out == "hello from openai"
    sent = json.loads(captured["request"].content)
    assert sent["messages"][0] == {"role": "system", "content": "be brief"}
    assert sent["messages"][1] == {"role": "user", "content": "hi"}
    assert captured["request"].headers["authorization"] == "Bearer sk-fake"


async def test_openai_adapter_raises_on_http_error(patch_async_client) -> None:
    patch_async_client(lambda req: httpx.Response(401, text="unauthorized"))
    with pytest.raises(LLMError):
        await OpenAIAdapter("sk-fake").generate("hi")


async def test_anthropic_adapter_parses_response(patch_async_client) -> None:
    captured = patch_async_client(
        lambda req: httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "hello from anthropic"}]},
        )
    )
    out = await AnthropicAdapter("anth-fake").generate("hi", system="sys")
    assert out == "hello from anthropic"
    assert captured["request"].headers["x-api-key"] == "anth-fake"
    assert captured["request"].headers["anthropic-version"]


async def test_anthropic_adapter_raises_on_http_error(patch_async_client) -> None:
    patch_async_client(lambda req: httpx.Response(500, text="boom"))
    with pytest.raises(LLMError):
        await AnthropicAdapter("anth").generate("hi")


async def test_gemini_adapter_parses_response(patch_async_client) -> None:
    captured = patch_async_client(
        lambda req: httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "hello from gemini"}]}}]},
        )
    )
    out = await GeminiAdapter("g-fake").generate("hi")
    assert out == "hello from gemini"
    # Gemini sends API key in query string, not header.
    assert "key=g-fake" in str(captured["request"].url)
