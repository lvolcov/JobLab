"""Import projects from 'Extra info for projects example.txt'.

Parses a Personal Statement text to extract structured project entries.
Run inside the container:
  python3 /app/scripts/import_projects_text.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys

sys.path.insert(0, "/app/src")
os.environ["JOBLAB_TEST_MODE"] = "0"

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from joblab_api.crypto import decrypt_str as decrypt_key
from joblab_api.llm.factory import build_adapter
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User
from joblab_api.wiki.dedup import classify
from joblab_api.wiki.models import WikiProject


def _empty_to_none(v):
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


class _ExtractedProject(BaseModel):
    name: str
    role: str = ""
    start: str | None = None
    end: str | None = None
    summary: str = ""
    achievements: str = ""

    @field_validator("start", "end", mode="before")
    @classmethod
    def coerce_dates(cls, v):
        return _empty_to_none(v)


class _ExtractedProjects(BaseModel):
    projects: list[_ExtractedProject] = Field(default_factory=list)


SCHEMA_HINT = """{
  "projects": [
    {
      "name": "string — concise project name",
      "role": "string — the candidate's role (e.g. 'Lead Developer', 'Project Lead')",
      "start": "YYYY-MM-DD or null",
      "end": "YYYY-MM-DD or null",
      "summary": "string — 2-4 sentences describing what the project was and its purpose",
      "achievements": "string — Markdown bullet list (- item) of quantified outcomes and impact"
    }
  ]
}"""

SYSTEM = (
    "You are a career data extractor. Read the personal statement / project description text "
    "and extract ALL distinct projects mentioned as structured JSON. "
    "Return ONLY a single JSON object — no prose, no code fences.\n\n"
    f"Schema:\n{SCHEMA_HINT}\n\n"
    "Rules:\n"
    "1. Extract EVERY distinct project, tool, or initiative mentioned, even if briefly described.\n"
    "2. Give each a concise, descriptive name based on the project's purpose or acronym.\n"
    "3. 'summary': 2-4 sentences about what the project did and why it mattered.\n"
    "4. 'achievements': Markdown bullet list of concrete outcomes — include numbers/£ values where mentioned.\n"
    "5. Dates: ISO 8601 (YYYY-MM-DD). If only a year is mentioned, use YYYY-01-01. null if unknown.\n"
    "6. The 'role' field should reflect what the candidate did on this project.\n"
    "7. All string fields present — use '' for unknown strings, null only for dates.\n"
)


_JSON_OBJ = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(raw: str) -> str:
    cleaned = raw.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:]
    match = _JSON_OBJ.search(cleaned)
    return match.group(0) if match else cleaned


async def main() -> None:
    text_path = "/tmp/example/Extra info for projects example.txt"
    with open(text_path, "r") as f:
        text_content = f.read()
    print(f"Read {len(text_content)} chars from text file")

    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, echo=False)
    SessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionFactory() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.email == "lucas.volcov@hotmail.com")
        )
        user = result.scalars().first()
        print(f"User: {user.email} (id={user.id})")

        # Get OpenAI key
        result = await session.execute(
            select(LLMKey).where(LLMKey.is_global == True, LLMKey.provider == LLMProvider.OPENAI)
        )
        key_row = result.scalars().first()
        api_key = decrypt_key(key_row.encrypted_key)
        print("API key loaded")

        # Call LLM to extract projects
        adapter = build_adapter(LLMProvider.OPENAI, api_key)
        user_prompt = (
            f"Personal statement text:\n\n{text_content.strip()}\n\n"
            "Extract all projects and return the JSON object now."
        )
        print("Calling LLM to extract projects...")
        raw = await adapter.generate(user_prompt, system=SYSTEM, max_tokens=3000, temperature=0.1)
        print(f"LLM response ({len(raw)} chars):")
        print(raw[:500])

        # Parse response
        data = json.loads(_extract_json(raw))
        extracted = _ExtractedProjects.model_validate(data)
        print(f"\nExtracted {len(extracted.projects)} projects")

        # Load existing projects for dedup
        existing_result = await session.execute(
            select(WikiProject).where(WikiProject.user_id == user.id)
        )
        existing = existing_result.scalars().all()
        print(f"Existing projects in DB: {len(existing)}")

        # Insert with dedup
        inserted = skipped = flagged = 0
        for proj in extracted.projects:
            verdict, match_id = classify("projects", proj, existing)
            if verdict == "exact":
                print(f"  SKIP (exact): {proj.name}")
                skipped += 1
                continue

            # Convert to WikiProject
            import datetime
            def parse_date(d):
                if not d:
                    return None
                try:
                    return datetime.date.fromisoformat(d)
                except (ValueError, TypeError):
                    return None

            obj = WikiProject(
                user_id=user.id,
                name=proj.name,
                role=proj.role,
                start=parse_date(proj.start),
                end=parse_date(proj.end),
                summary=proj.summary,
                achievements=proj.achievements,
            )
            if verdict == "duplicate":
                obj.possible_duplicate_of_id = match_id
                print(f"  FLAG (fuzzy): {proj.name}")
                flagged += 1
            else:
                print(f"  INSERT: {proj.name}")
                inserted += 1
            session.add(obj)
            existing.append(obj)

        await session.commit()
        print(f"\nResult: inserted={inserted}, skipped_exact={skipped}, flagged={flagged}")

    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
