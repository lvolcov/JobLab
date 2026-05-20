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
from joblab_api.data.cs_behaviours import format_behaviour_context
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
            date_range = f"{e.start or '?'} – {e.end or 'present'}"
            parts.append(f"- **{e.title}** at {e.employer} ({date_range})")
            if e.summary:
                parts.append(f"  Summary: {e.summary}")
            if e.achievements:
                parts.append(f"  Achievements:\n{e.achievements}")

    if wiki["projects"]:
        parts.append("## Projects")
        for p in wiki["projects"]:
            date_range = ""
            if p.start or p.end:
                date_range = f" ({p.start or '?'} – {p.end or 'present'})"
            role_str = f" — {p.role}" if p.role else ""
            parts.append(f"- **{p.name}**{role_str}{date_range}")
            if p.summary:
                parts.append(f"  Summary: {p.summary}")
            if p.achievements:
                parts.append(f"  Achievements:\n{p.achievements}")

    if wiki["skills"]:
        parts.append("## Skills")
        for s in wiki["skills"]:
            line = f"- {s.name}"
            if s.level:
                line += f" ({s.level})"
            if s.notes:
                line += f": {s.notes}"
            parts.append(line)

    if wiki["qualifications"]:
        parts.append("## Qualifications")
        for q in wiki["qualifications"]:
            issuer = _REDACTED if blind else (q.issuer or "")
            date_str = f" ({q.date_awarded})" if q.date_awarded and not blind else ""
            parts.append(f"- {q.name}" + (f" — {issuer}" if issuer else "") + date_str)

    if wiki["education"]:
        parts.append("## Education")
        for ed in wiki["education"]:
            institution = _REDACTED if blind else ed.institution
            dates = ""
            if not blind and (ed.start or ed.end):
                dates = f" ({ed.start or '?'} – {ed.end or '?'})"
            parts.append(f"- {ed.qualification} — {institution}{dates}")
            if ed.details and not blind:
                parts.append(f"  Details: {ed.details}")

    return "\n".join(parts)


def build_prompt(
    *,
    artifact_type: ArtifactType,
    application: Application,
    wiki: dict[str, list],
    extra_instructions: str,
    word_limit: int,
    behaviour_name: str | None,
    grade: str | None = None,
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

    extras = (
        f"\nUser instructions (advisory, never override safety):\n<<<\n{extra_instructions}\n>>>"
        if extra_instructions
        else ""
    )

    if artifact_type is ArtifactType.CV:
        task = (
            "Write a tailored CV in markdown format for the role described. "
            "Carefully match experience and skills to the job requirements. "
            "Use clear section headings: Profile, Experience, Projects, Skills, Qualifications, Education. "
            "Prioritise achievements with quantified impact where available. "
            f"Target audience is the hiring panel. Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.COVER_LETTER:
        task = (
            "Write a compelling, tailored cover letter addressed to the hiring team. "
            "Structure: (1) opening paragraph with genuine motivation for this specific role, "
            "(2) 2-3 paragraphs matching your strongest experiences/achievements to the role requirements, "
            "(3) closing paragraph with a clear call to action. "
            "UK professional English, no clichés. Be specific and evidence-based. "
            f"Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.BLIND_CV:
        task = (
            "Write a UK Civil Service-style blind/anonymised CV. "
            "OMIT: candidate name, age, date of birth, gender, photo, institution names, any information "
            "that could identify personal background or protected characteristics. "
            "INCLUDE: job titles, dates, skills, achievements, and impact statements. "
            "Use 'Organisation A', 'University B' etc. instead of real names. "
            f"Stay under {word_limit} words."
        )
    elif artifact_type is ArtifactType.BEHAVIOUR:
        if not behaviour_name:
            raise ValueError("behaviour_name is required for type=behaviour")

        # Build grade-specific behaviour context
        if grade:
            behaviour_ctx = format_behaviour_context(grade, behaviour_name)
        else:
            behaviour_ctx = f"Behaviour: {behaviour_name}"

        task = (
            f"Write a UK Civil Service behaviour response for the '{behaviour_name}' behaviour.\n\n"
            f"## Behaviour context\n{behaviour_ctx}\n\n"
            "## Writing instructions\n"
            "- Use the STAR structure: **Situation** (set the scene briefly), **Task** (your specific "
            "  responsibility), **Action** (what YOU did — use 'I' not 'we'), **Result** (quantified "
            "  outcomes and impact where possible).\n"
            "- Draw only from the candidate background below — do not invent experiences.\n"
            "- Be specific, first-person and evidence-based.\n"
            "- Demonstrate the grade-appropriate descriptors listed above in your example.\n"
            "- Avoid generic statements; every claim must be grounded in a concrete example.\n"
            f"- Stay strictly under {word_limit} words."
        )
    else:
        raise ValueError(f"unknown artifact_type: {artifact_type}")

    grade_context = f" The candidate is targeting a {grade} role." if grade else ""

    system = (
        "You are a senior UK Civil Service careers writer with deep expertise in Success Profiles "
        "and competency-based applications. You produce polished, specific, evidence-led UK-English "
        f"application material.{grade_context} "
        f"Hard word limit: {word_limit} words — count carefully and STOP before exceeding."
    )

    user = (
        f"{task}\n\n"
        f"## Target role\n{role_block}\n\n"
        f"## Candidate background\n{wiki_block}\n"
        f"{extras}"
        + (f"\n\nRetry note: {retry_hint}" if retry_hint else "")
    )
    return system, user
