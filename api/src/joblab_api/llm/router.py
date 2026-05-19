"""LLM key management routes.

- /admin/llm-keys/*  : admin-only; CRUD on global keys, plus user assignment
- /me/llm-keys/*     : user-owned keys

The encrypted_key column is never returned; responses include a `masked_key`
placeholder only.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from joblab_api.auth.deps import CurrentAdmin, CurrentUser
from joblab_api.crypto import encrypt_str
from joblab_api.db import SessionDep
from joblab_api.llm.models import LLMKey, LLMKeyAssignment, LLMProvider
from joblab_api.llm.schemas import (
    AssignmentCreate,
    GlobalKeyCreate,
    LLMKeyRead,
    UserKeyCreate,
)
from joblab_api.users.models import User

admin_router = APIRouter(prefix="/admin/llm-keys", tags=["admin:llm-keys"])
user_router = APIRouter(prefix="/me/llm-keys", tags=["llm-keys"])


def _to_read(k: LLMKey) -> LLMKeyRead:
    return LLMKeyRead(
        id=k.id,
        provider=k.provider,
        label=k.label,
        is_global=k.is_global,
        owner_user_id=k.owner_user_id,
    )


# ---------- admin: global keys ----------

@admin_router.get("", response_model=list[LLMKeyRead])
async def list_global_keys(session: SessionDep, _admin: CurrentAdmin) -> list[LLMKeyRead]:
    rows = (
        await session.execute(
            select(LLMKey).where(LLMKey.is_global.is_(True)).order_by(LLMKey.created_at.desc())
        )
    ).scalars().all()
    return [_to_read(k) for k in rows]


@admin_router.post("", response_model=LLMKeyRead, status_code=status.HTTP_201_CREATED)
async def create_global_key(
    payload: GlobalKeyCreate, session: SessionDep, _admin: CurrentAdmin
) -> LLMKeyRead:
    key = LLMKey(
        owner_user_id=None,
        provider=payload.provider,
        label=payload.label,
        encrypted_key=encrypt_str(payload.api_key),
        is_global=True,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return _to_read(key)


@admin_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_key(key_id: UUID, session: SessionDep, _admin: CurrentAdmin):
    key = (
        await session.execute(
            select(LLMKey).where(LLMKey.id == key_id, LLMKey.is_global.is_(True))
        )
    ).scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    await session.delete(key)
    await session.commit()


@admin_router.post(
    "/{key_id}/assign", response_model=LLMKeyRead, status_code=status.HTTP_201_CREATED
)
async def assign_key_to_user(
    key_id: UUID,
    payload: AssignmentCreate,
    session: SessionDep,
    _admin: CurrentAdmin,
) -> LLMKeyRead:
    key = (
        await session.execute(
            select(LLMKey).where(LLMKey.id == key_id, LLMKey.is_global.is_(True))
        )
    ).scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="global key not found")
    target = (
        await session.execute(select(User).where(User.id == payload.user_id))
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    # Idempotent: if already assigned, don't try to insert again (avoid rollback churn).
    existing = (
        await session.execute(
            select(LLMKeyAssignment).where(
                LLMKeyAssignment.llm_key_id == key_id,
                LLMKeyAssignment.user_id == payload.user_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(LLMKeyAssignment(llm_key_id=key_id, user_id=payload.user_id))
        await session.commit()
    return _to_read(key)


@admin_router.delete(
    "/{key_id}/assignments/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def unassign_key_from_user(
    key_id: UUID, user_id: UUID, session: SessionDep, _admin: CurrentAdmin
):
    row = (
        await session.execute(
            select(LLMKeyAssignment).where(
                LLMKeyAssignment.llm_key_id == key_id,
                LLMKeyAssignment.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not assigned")
    await session.delete(row)
    await session.commit()


# ---------- user: own + assigned keys ----------

@user_router.get("", response_model=list[LLMKeyRead])
async def list_my_keys(session: SessionDep, user: CurrentUser) -> list[LLMKeyRead]:
    own = (
        await session.execute(
            select(LLMKey).where(LLMKey.owner_user_id == user.id, LLMKey.is_global.is_(False))
        )
    ).scalars().all()
    assigned = (
        await session.execute(
            select(LLMKey)
            .join(LLMKeyAssignment, LLMKeyAssignment.llm_key_id == LLMKey.id)
            .where(LLMKey.is_global.is_(True), LLMKeyAssignment.user_id == user.id)
        )
    ).scalars().all()
    seen: set[UUID] = set()
    result: list[LLMKeyRead] = []
    for k in [*own, *assigned]:
        if k.id in seen:
            continue
        seen.add(k.id)
        result.append(_to_read(k))
    return result


@user_router.post("", response_model=LLMKeyRead, status_code=status.HTTP_201_CREATED)
async def create_my_key(
    payload: UserKeyCreate, session: SessionDep, user: CurrentUser
) -> LLMKeyRead:
    key = LLMKey(
        owner_user_id=user.id,
        provider=payload.provider,
        label=payload.label,
        encrypted_key=encrypt_str(payload.api_key),
        is_global=False,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return _to_read(key)


@user_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_key(key_id: UUID, session: SessionDep, user: CurrentUser):
    key = (
        await session.execute(
            select(LLMKey).where(
                LLMKey.id == key_id,
                LLMKey.owner_user_id == user.id,
                LLMKey.is_global.is_(False),
            )
        )
    ).scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    await session.delete(key)
    await session.commit()


def available_providers(_user: CurrentUser) -> list[str]:
    """Helper for the frontend: list provider enum values."""
    return [p.value for p in LLMProvider]


@user_router.get("/providers", response_model=list[str])
async def list_providers(_user: CurrentUser) -> list[str]:
    return [p.value for p in LLMProvider]
