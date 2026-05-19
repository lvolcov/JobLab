"""Auth routes: login, logout, me."""

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlmodel import select

from joblab_api.auth.deps import CurrentUser
from joblab_api.auth.schemas import LoginRequest, MeResponse, SettingsUpdate
from joblab_api.auth.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL,
    issue_session_token,
    verify_password,
)
from joblab_api.db import SessionDep
from joblab_api.llm.service import resolve_api_key
from joblab_api.rate_limit import LOGIN_LIMIT, limiter
from joblab_api.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MeResponse)
@limiter.limit(LOGIN_LIMIT)
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    session: SessionDep,
) -> MeResponse:
    _ = request  # slowapi needs the Request param even though we don't use it directly.
    user = (
        await session.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    token = issue_session_token(user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return MeResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_premium=user.is_premium,
        default_provider=user.default_provider,
    )


@router.post("/logout", status_code=204)
async def logout(response: Response) -> Response:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_premium=user.is_premium,
        default_provider=user.default_provider,
    )


@router.patch("/me/settings", response_model=MeResponse)
async def update_settings(
    payload: SettingsUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> MeResponse:
    if payload.default_provider is not None:
        key = await resolve_api_key(session, user.id, payload.default_provider)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no working key for that provider",
            )
    user.default_provider = payload.default_provider
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return MeResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_premium=user.is_premium,
        default_provider=user.default_provider,
    )
