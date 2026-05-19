"""Admin user management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from joblab_api.auth.deps import CurrentAdmin
from joblab_api.auth.security import hash_password
from joblab_api.db import SessionDep
from joblab_api.users.models import User
from joblab_api.users.schemas import PasswordReset, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/admin/users", tags=["admin:users"])


def _to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        is_premium=user.is_premium,
    )


async def _get_or_404(session, user_id: UUID) -> User:
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


@router.get("", response_model=list[UserRead])
async def list_users(session: SessionDep, _admin: CurrentAdmin) -> list[UserRead]:
    rows = (await session.execute(select(User).order_by(User.email))).scalars().all()
    return [_to_read(u) for u in rows]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate, session: SessionDep, _admin: CurrentAdmin
) -> UserRead:
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_superuser=payload.is_superuser,
        is_premium=payload.is_premium,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
    await session.refresh(user)
    return _to_read(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID, payload: UserUpdate, session: SessionDep, admin: CurrentAdmin
) -> UserRead:
    user = await _get_or_404(session, user_id)
    data = payload.model_dump(exclude_unset=True)

    # Self-lockout guards.
    if user.id == admin.id:
        if data.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot deactivate yourself",
            )
        if data.get("is_superuser") is False:
            other_admins = (
                await session.execute(
                    select(func.count())
                    .select_from(User)
                    .where(
                        User.is_superuser.is_(True),
                        User.is_active.is_(True),
                        User.id != admin.id,
                    )
                )
            ).scalar_one()
            if other_admins == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="cannot remove admin from the last active admin",
                )

    for k, v in data.items():
        setattr(user, k, v)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
    await session.refresh(user)
    return _to_read(user)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: UUID, payload: PasswordReset, session: SessionDep, _admin: CurrentAdmin
):
    user = await _get_or_404(session, user_id)
    user.hashed_password = hash_password(payload.new_password)
    await session.commit()


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID, session: SessionDep, admin: CurrentAdmin
):
    user = await _get_or_404(session, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot delete self")
    await session.delete(user)
    await session.commit()
