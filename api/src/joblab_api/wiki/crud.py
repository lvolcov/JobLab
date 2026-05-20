"""Generic CRUD router factory for owner-scoped wiki entities.

Purpose: avoid hand-writing six near-identical CRUD modules.
Each generated router enforces user_id == current_user.id on every query.
Created: 2026-05-19
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import SQLModel, select

from joblab_api.auth.deps import CurrentUser
from joblab_api.db import SessionDep


def make_owner_router(
    *,
    prefix: str,
    tag: str,
    Model: type[SQLModel],
    CreateSchema: type[BaseModel],
    UpdateSchema: type[BaseModel],
    ReadSchema: type[BaseModel],
    order_by_field: str | None = None,
) -> APIRouter:
    """Build an APIRouter with list/create/get/update/delete bound to current user.

    order_by_field: if set, sort by that column descending (nulls last), then created_at desc.
    """
    router = APIRouter(prefix=prefix, tags=[tag])

    async def _get_owned_or_404(session, user_id: UUID, item_id: UUID) -> Any:
        item = (
            await session.execute(
                select(Model).where(Model.id == item_id, Model.user_id == user_id)
            )
        ).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        return item

    @router.get("", response_model=list[ReadSchema])
    async def list_(session: SessionDep, user: CurrentUser):  # type: ignore[no-untyped-def]
        stmt = select(Model).where(Model.user_id == user.id)
        if order_by_field and hasattr(Model, order_by_field):
            col = getattr(Model, order_by_field)
            stmt = stmt.order_by(col.desc().nulls_last(), Model.created_at.desc())
        else:
            stmt = stmt.order_by(Model.created_at.desc())
        rows = (await session.execute(stmt)).scalars().all()
        return rows

    @router.post("", response_model=ReadSchema, status_code=status.HTTP_201_CREATED)
    async def create(  # type: ignore[no-untyped-def]
        payload: CreateSchema, session: SessionDep, user: CurrentUser
    ):
        obj = Model(user_id=user.id, **payload.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.get("/{item_id}", response_model=ReadSchema)
    async def get(item_id: UUID, session: SessionDep, user: CurrentUser):  # type: ignore[no-untyped-def]
        return await _get_owned_or_404(session, user.id, item_id)

    @router.patch("/{item_id}", response_model=ReadSchema)
    async def update(  # type: ignore[no-untyped-def]
        item_id: UUID,
        payload: UpdateSchema,
        session: SessionDep,
        user: CurrentUser,
    ):
        obj = await _get_owned_or_404(session, user.id, item_id)
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(obj, k, v)
        obj.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(item_id: UUID, session: SessionDep, user: CurrentUser):  # type: ignore[no-untyped-def]
        obj = await _get_owned_or_404(session, user.id, item_id)
        await session.delete(obj)
        await session.commit()

    return router
