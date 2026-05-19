"""LLM provider abstraction.

Purpose: a single async `generate` interface so the rest of the app
doesn't care which provider it's talking to.
Created: 2026-05-19
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMAdapter(Protocol):
    """Common shape for OpenAI/Anthropic/Gemini adapters."""

    provider_name: str

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.4,
    ) -> str:
        """Return the model's text completion for the given prompt."""
        ...


class LLMError(RuntimeError):
    """Raised when an adapter call fails for a recoverable reason (HTTP error, parse)."""
