"""Generation orchestration: prompt → LLM → word-count retry → persist.

`adapter_for(provider, api_key)` is module-level so tests can monkeypatch it
to inject a deterministic stub adapter.
Created: 2026-05-19
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from joblab_api.applications.models import Application, ApplicationArtifact, ArtifactType
from joblab_api.applications.schemas import GenerateRequest
from joblab_api.generation.prompts import DEFAULT_WORD_LIMITS, build_prompt, collect_wiki
from joblab_api.generation.test_adapter import EchoAdapter
from joblab_api.llm.factory import build_adapter
from joblab_api.llm.service import resolve_api_key
from joblab_api.word_count import count_words

MAX_ATTEMPTS = 3


@dataclass
class GenerationResult:
    content: str
    attempts: int
    final_word_count: int
    warning_flag: bool


def adapter_for(provider, api_key: str):
    """Indirection point so tests can replace the real adapter factory.

    When JOBLAB_TEST_MODE=1, returns a deterministic stub that never touches the
    network. Used by Playwright e2e suites.
    """
    if os.getenv("JOBLAB_TEST_MODE") == "1":
        return EchoAdapter()
    return build_adapter(provider, api_key)


async def generate_for_application(
    *,
    session: AsyncSession,
    user_id: UUID,
    application: Application,
    request: GenerateRequest,
) -> ApplicationArtifact | None:
    """Run the generation pipeline; persist + return the artifact, or None if no key.

    Returns None when the user has neither own nor assigned key for the chosen provider —
    the caller turns that into a 400.
    """
    # Resolve API key — own first, then assigned global.
    api_key = await resolve_api_key(session, user_id, request.provider)
    if api_key is None:
        return None

    word_limit = request.word_limit or DEFAULT_WORD_LIMITS[request.type]
    if word_limit <= 0:
        raise ValueError("word_limit must be positive")

    if request.type is ArtifactType.BEHAVIOUR and not request.behaviour_name:
        raise ValueError("behaviour_name is required for type=behaviour")

    wiki = await collect_wiki(session, user_id)
    adapter = adapter_for(request.provider, api_key)

    best_content = ""
    best_count = 0
    attempts = 0
    warning_flag = False
    retry_hint = ""
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        system, user_prompt = build_prompt(
            artifact_type=request.type,
            application=application,
            wiki=wiki,
            extra_instructions=request.extra_instructions,
            word_limit=word_limit,
            behaviour_name=request.behaviour_name,
            retry_hint=retry_hint,
        )
        content = await adapter.generate(
            user_prompt,
            system=system,
            max_tokens=max(512, word_limit * 4),
            temperature=0.4,
        )
        wc = count_words(content)
        # Track the closest-to-limit non-over result; otherwise the latest.
        if wc <= word_limit:
            best_content, best_count = content, wc
            warning_flag = False
            break
        # Over the limit — keep this as fallback, ask for a shorter rewrite.
        if attempts == 1 or wc < best_count or best_count == 0:
            best_content, best_count = content, wc
        retry_hint = (
            f"Previous draft was {wc} words — that exceeds the {word_limit}-word limit by "
            f"{wc - word_limit}. Rewrite it strictly under {word_limit} words. "
            "Preserve the strongest points; cut redundancy."
        )
        warning_flag = True  # may flip back to False if a later attempt succeeds

    artifact = ApplicationArtifact(
        application_id=application.id,
        type=request.type,
        provider=request.provider,
        word_limit=word_limit,
        attempts=attempts,
        final_word_count=best_count,
        warning_flag=warning_flag,
        content=best_content,
        extra_instructions=request.extra_instructions,
        behaviour_name=request.behaviour_name,
    )
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)
    return artifact
