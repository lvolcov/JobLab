"""Server-side LLM key lookup.

Purpose: pick an active key for (user, provider). Used by the generation engine.
Created: 2026-05-19
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.crypto import decrypt_str
from joblab_api.llm.models import LLMKey, LLMKeyAssignment, LLMProvider


async def resolve_api_key(
    session: AsyncSession, user_id: UUID, provider: LLMProvider
) -> str | None:
    """Return a decrypted API key for the user+provider, or None.

    Resolution order:
    1. The user's own key for that provider (most recent).
    2. A global key for that provider that has been assigned to the user.
    """
    own = (
        await session.execute(
            select(LLMKey)
            .where(
                LLMKey.owner_user_id == user_id,
                LLMKey.provider == provider,
                LLMKey.is_global.is_(False),
            )
            .order_by(LLMKey.created_at.desc())
        )
    ).scalar_one_or_none()
    if own is not None:
        return decrypt_str(own.encrypted_key)

    assigned = (
        await session.execute(
            select(LLMKey)
            .join(LLMKeyAssignment, LLMKeyAssignment.llm_key_id == LLMKey.id)
            .where(
                LLMKey.is_global.is_(True),
                LLMKey.provider == provider,
                LLMKeyAssignment.user_id == user_id,
            )
            .order_by(LLMKey.created_at.desc())
        )
    ).scalar_one_or_none()
    if assigned is not None:
        return decrypt_str(assigned.encrypted_key)

    return None
