"""Test behaviour generation with grade context.

Run inside the container: python3 /app/scripts/test_behaviour_generation.py
"""

from __future__ import annotations

import asyncio
import os
import sys
sys.path.insert(0, "/app/src")
os.environ["JOBLAB_TEST_MODE"] = "0"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from joblab_api.applications.models import Application, ArtifactType
from joblab_api.applications.schemas import GenerateRequest
from joblab_api.crypto import decrypt_str as decrypt_key
from joblab_api.generation.service import generate_for_application
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User


async def main() -> None:
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
            select(Application).where(
                Application.user_id == user.id,
                Application.role_title == "Strategic Risk Analyst",
            )
        )
        app = result.scalars().first()
        if not app:
            print("ERROR: Strategic Risk Analyst application not found")
            return
        print(f"Application: {app.role_title} at {app.company}")
        print(f"JD length: {len(app.jd_text)} chars")

        request = GenerateRequest(
            type=ArtifactType.BEHAVIOUR,
            provider=LLMProvider.OPENAI,
            word_limit=250,
            behaviour_name="Making Effective Decisions",
            grade="Grade 7",
            extra_instructions="",
        )
        print(f"\nGenerating behaviour: {request.behaviour_name} at {request.grade}...")
        artifact = await generate_for_application(
            session=session,
            user_id=user.id,
            application=app,
            request=request,
        )
        if artifact is None:
            print("ERROR: No API key available")
            return
        print(f"\nGenerated! Word count: {artifact.final_word_count}/{artifact.word_limit}")
        print(f"Attempts: {artifact.attempts}")
        print(f"Warning flag: {artifact.warning_flag}")
        print(f"\n--- Content preview (first 500 chars) ---")
        print(artifact.content[:500])

    await engine.dispose()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
