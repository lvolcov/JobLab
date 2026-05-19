"""OpenAI Chat Completions adapter."""

from __future__ import annotations

import httpx

from joblab_api.llm.provider import LLMError

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIAdapter:
    provider_name = "openai"

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
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
        if r.status_code >= 400:
            raise LLMError(f"openai HTTP {r.status_code}: {r.text[:300]}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"openai: malformed response ({exc})") from exc
