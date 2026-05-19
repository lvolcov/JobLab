"""CV import pipeline: PDF -> LLM -> structured wiki rows.

Created: 2026-05-19
"""

from __future__ import annotations

import json
import os
import re
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.llm.factory import build_adapter
from joblab_api.llm.models import LLMProvider
from joblab_api.wiki.dedup import classify
from joblab_api.wiki.import_schemas import (
    JSON_SCHEMA_HINT,
    ExtractedCV,
    ImportResult,
    ImportSummary,
)
from joblab_api.wiki.models import (
    WikiCV,
    WikiEducation,
    WikiExperience,
    WikiProject,
    WikiQualification,
    WikiSkill,
)

IMPORT_PROMPT_TAG = "[joblab-cv-import-v1]"

MAX_ATTEMPTS = 2

_ENTITY_MAP = {
    "cvs": WikiCV,
    "experiences": WikiExperience,
    "projects": WikiProject,
    "skills": WikiSkill,
    "qualifications": WikiQualification,
    "education": WikiEducation,
}


def adapter_for_import(provider: LLMProvider, api_key: str):
    """Indirection so tests can swap the adapter. Mirrors generation.service."""
    if os.getenv("JOBLAB_TEST_MODE") == "1":
        from joblab_api.wiki.import_stub_adapter import JsonStubAdapter

        return JsonStubAdapter()
    return build_adapter(provider, api_key)


def build_import_prompt(cv_text: str) -> tuple[str, str]:
    """Return (system, user) prompts for the structured extraction call."""
    system = (
        f"{IMPORT_PROMPT_TAG} You are a CV parser. Read the user's CV and return "
        "ONLY a single JSON object that matches the schema below. No prose, no "
        "code fences, no commentary — JSON only.\n\n"
        f"Schema:\n{JSON_SCHEMA_HINT}\n\n"
        "Rules:\n"
        "- Omit entries you are not confident about.\n"
        "- Dates: ISO 8601 (YYYY-MM-DD). If only a year is known, use the first "
        "  day of that year (e.g. 2021 -> 2021-01-01). Use null when unknown.\n"
        "- 'cvs': include one entry whose title summarises the CV (e.g. 'General CV') "
        "  and whose body_md is a clean Markdown rendering of the whole CV.\n"
        "- 'achievements' should be a Markdown bullet list when present.\n"
        "- All string fields must be present; use empty strings rather than null.\n"
    )
    user = f"CV text:\n\n{cv_text.strip()}\n\nReturn JSON now."
    return system, user


_JSON_OBJ = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(raw: str) -> str:
    """Return the first {...} block from the LLM response, stripped of fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    match = _JSON_OBJ.search(cleaned)
    return match.group(0) if match else cleaned


async def _existing(session: AsyncSession, model, user_id: UUID) -> list:
    return (
        (await session.execute(select(model).where(model.user_id == user_id)))
        .scalars()
        .all()
    )


def _summarise() -> ImportSummary:
    return ImportSummary()


async def parse_with_llm(adapter, cv_text: str) -> ExtractedCV:
    """Call the adapter with up to one retry on parse/validation failure."""
    system, user_prompt = build_import_prompt(cv_text)
    last_error: str = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = user_prompt
        if attempt > 1 and last_error:
            prompt = (
                f"{user_prompt}\n\n"
                f"Your previous reply failed validation: {last_error}. "
                "Return ONLY a single JSON object matching the schema."
            )
        raw = await adapter.generate(prompt, system=system, max_tokens=4000, temperature=0.1)
        try:
            data = json.loads(_extract_json(raw))
            return ExtractedCV.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:300]
            continue
    raise ValueError(f"LLM did not return valid JSON after {MAX_ATTEMPTS} attempts: {last_error}")


async def apply_extracted(
    session: AsyncSession,
    user_id: UUID,
    extracted: ExtractedCV,
) -> dict[str, ImportSummary]:
    """Insert extracted rows with exact-skip + fuzzy-tag dedup."""
    summaries: dict[str, ImportSummary] = {k: _summarise() for k in _ENTITY_MAP}

    payload = {
        "cvs": extracted.cvs,
        "experiences": extracted.experiences,
        "projects": extracted.projects,
        "skills": extracted.skills,
        "qualifications": extracted.qualifications,
        "education": extracted.education,
    }

    for entity, items in payload.items():
        model = _ENTITY_MAP[entity]
        existing = await _existing(session, model, user_id)
        for item in items:
            verdict, match_id = classify(entity, item, existing)
            if verdict == "exact":
                summaries[entity].skipped_exact += 1
                continue
            data = item.model_dump()
            obj = model(user_id=user_id, **data)
            if verdict == "duplicate":
                obj.possible_duplicate_of_id = match_id
                summaries[entity].flagged_duplicate += 1
            else:
                summaries[entity].inserted += 1
            session.add(obj)
            existing.append(obj)
    await session.commit()
    return summaries


async def import_cv_for_user(
    *,
    session: AsyncSession,
    user_id: UUID,
    provider: LLMProvider,
    api_key: str,
    cv_text: str,
) -> ImportResult:
    """End-to-end: text -> LLM -> validated -> persisted -> ImportResult."""
    adapter = adapter_for_import(provider, api_key)
    extracted = await parse_with_llm(adapter, cv_text)
    summaries = await apply_extracted(session, user_id, extracted)
    return ImportResult(
        cvs=summaries["cvs"],
        experiences=summaries["experiences"],
        projects=summaries["projects"],
        skills=summaries["skills"],
        qualifications=summaries["qualifications"],
        education=summaries["education"],
        provider=provider.value,
        attempts=1,
    )
