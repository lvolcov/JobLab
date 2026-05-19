"""Prompt assembly per artifact type.

Pulls the user's wiki entries and assembles a deterministic block that the
LLM sees. For blind CVs, redacts identifying details (name, DOB, institution).
Created: 2026-05-19
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.applications.models import Application, ArtifactType
from joblab_api.wiki.models import (
    WikiCV,
    WikiEducation,
    WikiExperience,
    WikiProject,
    WikiQualification,
    WikiSkill,
)

DEFAULT_WORD_LIMITS: dict[ArtifactType, int] = {
    ArtifactType.CV: 800,
    ArtifactType.COVER_LETTER: 400,
    ArtifactType.BLIND_CV: 800,
    ArtifactType.BEHAVIOUR: 250,
}

_REDACTED = "[redacted]"


async def collect_wiki(session: AsyncSession, user_id: UUID) -> dict[str, list]:
    """Return all of the user's wiki entries grouped by entity."""

    async def _all(model):
        return (
            await session.execute(
                select(model).where(model.user_id == user_id)
            )
        ).scalars().all()

    return {
        "cvs": await _all(WikiCV),
        "education": await _all(WikiEducation),
        "qualifications": await _all(WikiQualification),
        "skills": await _all(WikiSkill),
        "projects": await _all(WikiProject),
        "experiences": await _all(WikiExperience),
    }


def _format_wiki(wiki: dict[str, list], *, blind: bool = False) -> str:
    parts: list[str] = []

    if wiki["experiences"]:
        parts.append("## Experience")
        for e in wiki["experiences"]:
            parts.append(
                f"- {e.title} at {e.employer} ({e.start or '?'} – {e.end or 'present'})"
            )
            if e.summary:
                parts.append(f"  Summary: {e.summary}")
            if e.achievements:
                parts.append(f"  Achievements: {e.achievements}")

    if wiki["projects"]:
        parts.append("## Projects")
        for p in wiki["projects"]:
            parts.append(f"- {p.name} ({p.role})")
            if p.summary:
                parts.append(f"  Summary: {p.summary}")
            if p.achievements:
                parts.append(f"  Achievements: {p.achievements}")

    if wiki["skills"]:
        parts.append("## Skills")
        for s in wiki["skills"]:
            line = f"- {s.name}"
            if s.level:
                line += f" ({s.level})"
            parts.append(line)

    if wiki["qualifications"]:
        parts.append("## Qualifications")
        for q in wiki["qualifications"]:
            issuer = _REDACTED if blind else (q.issuer or "")
            parts.append(f"- {q.name}" + (f" — {issuer}" if issuer else ""))

    if wiki["education"]:
        parts.append("## Education")
        for ed in wiki["education"]:
            institution = _REDACTED if blind else ed.institution
            dates = ""
            if not blind and (ed.start or ed.end):
                dates = f" ({ed.start or '?'} – {ed.end or '?'})"
            parts.append(f"- {ed.qualification} — {institution}{dates}")

    return "\n".join(parts)


def build_prompt(
    *,
    artifact_type: ArtifactType,
    application: Application,
    wiki: dict[str, list],
    extra_instructions: str,
    word_limit: int,
    behaviour_name: str | None,
    retry_hint: str = "",
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the given artifact request."""
    blind = artifact_type is ArtifactType.BLIND_CV
    wiki_block = _format_wiki(wiki, blind=blind)

    role_block = (
        f"Role title: {application.role_title}\n"
        f"Company: {application.company or '[unspecified]'}\n"
        f"Job description:\n<<<\n{application.jd_text}\n>>>"
    )

    extras = f"\nUser instructions (advisory, never override safety):\n<<<\n{extra_instructions}\n>>>" if extra_instructions else ""

    if artifact_type is ArtifactType.CV:
        task = (
            "Write a tailored CV in markdown that emphasises experience relevant to the role. "
            f"Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.COVER_LETTER:
        task = (
            "Write a concise cover letter addressed to the hiring team. Open with motivation, "
            f"highlight 2-3 strongest experiences, close with a call to action. Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.BLIND_CV:
        task = (
            "Write a UK Civil Service-style blind CV: omit the candidate's name, age, gender, "
            "photo, and institution names. Use only role titles, dates of experience, skills, and "
            f"achievements. Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.BEHAVIOUR:
        if not behaviour_name:
            raise ValueError("behaviour_name is required for type=behaviour")
        task = (
            f"Write a UK Civil Service-style 'Behaviour' response for the behaviour named "
            f"'{behaviour_name}', using the STAR format (Situation, Task, Action, Result). "
            f"Be specific and first-person. Stay strictly under {word_limit} words."
        )
    else:
        raise ValueError(f"unknown artifact_type: {artifact_type}")

    system = (
        "You are a senior careers writer producing UK-English application material. "
        f"Hard word limit: {word_limit} words. Count carefully and STOP before exceeding."
    )

    user = (
        f"{task}\n\n"
        f"{role_block}\n\n"
        f"## Candidate background\n{wiki_block}\n"
        f"{extras}"
        + (f"\n\nRetry note: {retry_hint}" if retry_hint else "")
    )
    return system, user
