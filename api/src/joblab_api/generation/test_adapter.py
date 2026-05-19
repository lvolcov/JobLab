"""Deterministic stub adapter used when JOBLAB_TEST_MODE=1.

Returns a short, under-the-limit canned response so end-to-end suites can run
without burning real LLM credits or depending on network reachability.
Created: 2026-05-19
"""

from __future__ import annotations


class EchoAdapter:
    provider_name = "test"

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.4,
    ) -> str:
        _ = (prompt, system, max_tokens, temperature)
        return (
            "Test generation output. Tailored to the role, "
            "highlighting strengths and motivation. Under limit."
        )
