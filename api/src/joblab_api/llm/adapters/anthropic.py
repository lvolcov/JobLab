"""Anthropic Messages adapter."""

from __future__ import annotations

import httpx

from joblab_api.llm.provider import LLMError

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-7"


class AnthropicAdapter:
    provider_name = "anthropic"

    def __init__(self, api_key: str, *, model: str = DEFAULT_MODEL, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.4,
    ) -> str:
        body: dict[str, object] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json=body,
            )
        if r.status_code >= 400:
            raise LLMError(f"anthropic HTTP {r.status_code}: {r.text[:300]}")
        try:
            data = r.json()
            return "".join(
                block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
            )
        except (KeyError, ValueError) as exc:
            raise LLMError(f"anthropic: malformed response ({exc})") from exc
