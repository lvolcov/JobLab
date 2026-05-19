"""Google Gemini (generativelanguage) adapter."""

from __future__ import annotations

import httpx

from joblab_api.llm.provider import LLMError

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiAdapter:
    provider_name = "gemini"

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
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }
        if system:
            body["systemInstruction"] = {"role": "system", "parts": [{"text": system}]}

        url = f"{GEMINI_BASE}/{self._model}:generateContent"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(url, params={"key": self._api_key}, json=body)
        if r.status_code >= 400:
            raise LLMError(f"gemini HTTP {r.status_code}: {r.text[:300]}")
        try:
            data = r.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"gemini: malformed response ({exc})") from exc
