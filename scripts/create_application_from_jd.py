"""Create an application record from 'Job Description Example.pdf'.

Uses LLM to extract role title, company, and job description text.
Run inside the container:
  python3 /app/scripts/create_application_from_jd.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys

sys.path.insert(0, "/app/src")
os.environ["JOBLAB_TEST_MODE"] = "0"

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from joblab_api.applications.models import Application, ApplicationStatus
from joblab_api.crypto import decrypt_str as decrypt_key
from joblab_api.documents.parsing import extract_text
from joblab_api.llm.factory import build_adapter
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User


class _ExtractedJD(BaseModel):
    role_title: str
    company: str = ""
    grade: str = ""
    jd_text: str = ""


SYSTEM = (
    "You are a job description parser. Read the text and extract the key fields as JSON. "
    "Return ONLY a JSON object — no prose, no code fences.\n\n"
    'Schema: {"role_title": str, "company": str, "grade": str, "jd_text": str}\n\n'
    "Rules:\n"
    "1. role_title: the official job title from the vacancy.\n"
    "2. company: the department/organisation name.\n"
    "3. grade: the Civil Service grade if mentioned (e.g. 'Grade 7', 'SEO').\n"
    "4. jd_text: the FULL job description text, including all requirements, responsibilities, "
    "   essential criteria, behaviours, and any other relevant content. Preserve all important detail.\n"
)

_JSON_OBJ = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(raw: str) -> str:
    cleaned = raw.strip().strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:]
    match = _JSON_OBJ.search(cleaned)
    return match.group(0) if match else cleaned


async def main() -> None:
    pdf_path = "/tmp/example/Job Description Example.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    raw_text = extract_text("pdf", pdf_bytes)
    print(f"Extracted {len(raw_text)} chars from JD PDF")

    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, echo=False)
    SessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionFactory() as session:
        result = await session.execute(
            select(User).where(User.email == "lucas.volcov@hotmail.com")
        )
        user = result.scalars().first()
        print(f"User: {user.email}")

        result = await session.execute(
            select(LLMKey).where(LLMKey.is_global == True, LLMKey.provider == LLMProvider.OPENAI)
        )
        key_row = result.scalars().first()
        api_key = decrypt_key(key_row.encrypted_key)

        adapter = build_adapter(LLMProvider.OPENAI, api_key)
        user_prompt = (
            f"Job description text:\n\n{raw_text.strip()}\n\n"
            "Extract the fields and return JSON now."
        )
        print("Calling LLM to parse JD...")
        raw_response = await adapter.generate(
            user_prompt, system=SYSTEM, max_tokens=4000, temperature=0.1
        )
        print(f"LLM response ({len(raw_response)} chars)")

        data = json.loads(_extract_json(raw_response))
        extracted = _ExtractedJD.model_validate(data)
        print(f"Role: {extracted.role_title}")
        print(f"Company: {extracted.company}")
        print(f"Grade: {extracted.grade}")
        print(f"JD text length: {len(extracted.jd_text)}")

        # Check for existing application
        existing_result = await session.execute(
            select(Application).where(
                Application.user_id == user.id,
                Application.role_title == extracted.role_title,
            )
        )
        existing = existing_result.scalars().first()
        if existing:
            print(f"\nApplication already exists: {existing.id}")
            # Update the JD text to ensure it's complete
            existing.jd_text = extracted.jd_text
            await session.commit()
            print("Updated JD text.")
        else:
            app = Application(
                user_id=user.id,
                role_title=extracted.role_title,
                company=extracted.company,
                jd_text=extracted.jd_text,
                status=ApplicationStatus.APPLIED,
            )
            session.add(app)
            await session.commit()
            await session.refresh(app)
            print(f"\nCreated application: {app.id}")
            print(f"Role: {app.role_title}")
            print(f"Company: {app.company}")

    await engine.dispose()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
