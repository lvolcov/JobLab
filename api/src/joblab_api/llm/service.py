"""Server-side LLM key lookup.

Resolution order for a given (user, provider):
1. The user's own key (most recent), if any.
2. A global key the user is allowed to see:
   - any global key if the user is premium; otherwise
   - only global keys with is_premium_only=False.

Created: 2026-05-19
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from joblab_api.crypto import decrypt_str
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.users.models import User


async def resolve_api_key(
    session: AsyncSession, user_id: UUID, provider: LLMProvider
) -> str | None:
    """Return a decrypted API key for the user+provider, or None."""
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

    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None:
        return None

    stmt = (
        select(LLMKey)
        .where(LLMKey.is_global.is_(True), LLMKey.provider == provider)
        .order_by(LLMKey.created_at.desc())
    )
    if not user.is_premium:
        stmt = stmt.where(LLMKey.is_premium_only.is_(False))

    available = (await session.execute(stmt)).scalar_one_or_none()
    if available is not None:
        return decrypt_str(available.encrypted_key)
    return None
