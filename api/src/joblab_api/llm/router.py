"""LLM key management routes.

- /admin/llm-keys/*  : admin-only; CRUD on global keys.
- /me/llm-keys/*     : the current user's keys (own + visible globals).

Global key visibility is controlled by the per-key ``is_premium_only`` flag
and the per-user ``is_premium`` flag.

The encrypted_key column is never returned; responses include a ``masked_key``
placeholder only.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from joblab_api.auth.deps import CurrentAdmin, CurrentUser
from joblab_api.crypto import encrypt_str
from joblab_api.db import SessionDep
from joblab_api.llm.factory import build_adapter
from joblab_api.llm.models import LLMKey, LLMProvider
from joblab_api.llm.provider import LLMError
from joblab_api.llm.schemas import (
    GlobalKeyCreate,
    LLMKeyRead,
    TestKeyRequest,
    TestKeyResponse,
    UserKeyCreate,
)

admin_router = APIRouter(prefix="/admin/llm-keys", tags=["admin:llm-keys"])
user_router = APIRouter(prefix="/me/llm-keys", tags=["llm-keys"])


def _to_read(k: LLMKey) -> LLMKeyRead:
    return LLMKeyRead(
        id=k.id,
        provider=k.provider,
        label=k.label,
        is_global=k.is_global,
        is_premium_only=k.is_premium_only,
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
        is_premium_only=payload.is_premium_only,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)
    return _to_read(key)


@admin_router.patch("/{key_id}", response_model=LLMKeyRead)
async def update_global_key(
    key_id: UUID,
    payload: dict,
    session: SessionDep,
    _admin: CurrentAdmin,
) -> LLMKeyRead:
    """Currently supports toggling ``is_premium_only`` and editing ``label``."""
    key = (
        await session.execute(
            select(LLMKey).where(LLMKey.id == key_id, LLMKey.is_global.is_(True))
        )
    ).scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    if "is_premium_only" in payload:
        key.is_premium_only = bool(payload["is_premium_only"])
    if "label" in payload and isinstance(payload["label"], str) and payload["label"]:
        key.label = payload["label"]
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


# ---------- user: own + visible globals ----------

@user_router.get("", response_model=list[LLMKeyRead])
async def list_my_keys(session: SessionDep, user: CurrentUser) -> list[LLMKeyRead]:
    own = (
        await session.execute(
            select(LLMKey).where(LLMKey.owner_user_id == user.id, LLMKey.is_global.is_(False))
        )
    ).scalars().all()
    visible_globals_stmt = select(LLMKey).where(LLMKey.is_global.is_(True))
    if not user.is_premium:
        visible_globals_stmt = visible_globals_stmt.where(LLMKey.is_premium_only.is_(False))
    visible = (await session.execute(visible_globals_stmt)).scalars().all()
    seen: set[UUID] = set()
    result: list[LLMKeyRead] = []
    for k in [*own, *visible]:
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


@user_router.get("/providers", response_model=list[str])
async def list_providers(_user: CurrentUser) -> list[str]:
    return [p.value for p in LLMProvider]


def _test_key(provider: LLMProvider, api_key: str) -> TestKeyResponse:  # pragma: no cover
    raise NotImplementedError  # placeholder so test endpoint stays close to admin


async def _probe(provider: LLMProvider, api_key: str) -> TestKeyResponse:
    try:
        adapter = build_adapter(provider, api_key)
        await adapter.generate("ping", max_tokens=1, temperature=0.0)
    except LLMError as exc:
        return TestKeyResponse(ok=False, provider=provider, detail=str(exc)[:300])
    except Exception as exc:
        return TestKeyResponse(
            ok=False, provider=provider, detail=f"{type(exc).__name__}: {exc}"[:300]
        )
    return TestKeyResponse(ok=True, provider=provider, detail="ok")


@user_router.post("/test", response_model=TestKeyResponse)
async def test_my_key(payload: TestKeyRequest, _user: CurrentUser) -> TestKeyResponse:
    return await _probe(payload.provider, payload.api_key)


@admin_router.post("/test", response_model=TestKeyResponse)
async def test_global_key(payload: TestKeyRequest, _admin: CurrentAdmin) -> TestKeyResponse:
    return await _probe(payload.provider, payload.api_key)
