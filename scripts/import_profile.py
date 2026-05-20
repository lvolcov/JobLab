"""Import Profile.pdf into the wiki for lucas.volcov@hotmail.com.

Run inside the container:
  python3 /app/scripts/import_profile.py

Uses the existing import pipeline: PDF -> LLM -> dedup -> wiki rows.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, "/app/src")

# Force real LLM usage (not stub)
os.environ["JOBLAB_TEST_MODE"] = "0"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from joblab_api.crypto import decrypt_str as decrypt_key
from joblab_api.documents.parsing import extract_text
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User
from joblab_api.wiki.import_service import import_cv_for_user


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url, echo=False)
    SessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionFactory() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.email == "lucas.volcov@hotmail.com")
        )
        user = result.scalars().first()
        if not user:
            print("ERROR: User lucas.volcov@hotmail.com not found")
            return
        print(f"User: {user.email} (id={user.id})")

        # Get global OpenAI key
        result = await session.execute(
            select(LLMKey).where(
                LLMKey.is_global == True,
                LLMKey.provider == LLMProvider.OPENAI,
            )
        )
        key_row = result.scalars().first()
        if not key_row:
            print("ERROR: No global OpenAI key found")
            return
        api_key = decrypt_key(key_row.encrypted_key)
        print(f"Using key: {key_row.id} ({key_row.provider})")

        # Extract text from PDF
        pdf_path = "/tmp/example/Profile.pdf"
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        cv_text = extract_text("pdf", pdf_bytes)
        print(f"Extracted {len(cv_text)} chars from Profile.pdf")
        print("First 300 chars:", cv_text[:300])

        # Run import
        print("\nRunning CV import (calling LLM)...")
        result = await import_cv_for_user(
            session=session,
            user_id=user.id,
            provider=LLMProvider.OPENAI,
            api_key=api_key,
            cv_text=cv_text,
        )
        print("\n=== Import Result ===")
        print(f"CVs:            inserted={result.cvs.inserted}, skipped={result.cvs.skipped_exact}, flagged={result.cvs.flagged_duplicate}")
        print(f"Experiences:    inserted={result.experiences.inserted}, skipped={result.experiences.skipped_exact}, flagged={result.experiences.flagged_duplicate}")
        print(f"Projects:       inserted={result.projects.inserted}, skipped={result.projects.skipped_exact}, flagged={result.projects.flagged_duplicate}")
        print(f"Skills:         inserted={result.skills.inserted}, skipped={result.skills.skipped_exact}, flagged={result.skills.flagged_duplicate}")
        print(f"Qualifications: inserted={result.qualifications.inserted}, skipped={result.qualifications.skipped_exact}, flagged={result.qualifications.flagged_duplicate}")
        print(f"Education:      inserted={result.education.inserted}, skipped={result.education.skipped_exact}, flagged={result.education.flagged_duplicate}")
        print(f"Provider: {result.provider}")

    await engine.dispose()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
