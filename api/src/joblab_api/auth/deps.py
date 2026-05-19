"""FastAPI dependencies for resolving the current user from the cookie."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlmodel import select

from joblab_api.auth.security import SESSION_COOKIE_NAME, decode_session_token
from joblab_api.db import SessionDep
from joblab_api.users.models import User


async def _current_user(
    session: SessionDep,
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> User:
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    user_id = decode_session_token(session_cookie)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")
    return user


async def _current_admin(user: Annotated[User, Depends(_current_user)]) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user


CurrentUser = Annotated[User, Depends(_current_user)]
CurrentAdmin = Annotated[User, Depends(_current_admin)]
