"""POST /applications/{id}/generate — kicks off a single generation run."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from joblab_api.applications.models import Application
from joblab_api.applications.schemas import ArtifactRead, GenerateRequest
from joblab_api.auth.deps import CurrentUser
from joblab_api.db import SessionDep
from joblab_api.generation.service import generate_for_application
from joblab_api.rate_limit import GENERATE_LIMIT, limiter

router = APIRouter(prefix="/applications", tags=["generation"])


@router.post(
    "/{app_id}/generate",
    response_model=ArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(GENERATE_LIMIT)
async def generate(
    request: Request,
    app_id: UUID,
    payload: GenerateRequest,
    session: SessionDep,
    user: CurrentUser,
) -> ArtifactRead:
    _ = request  # slowapi requires the Request param.
    app = (
        await session.execute(
            select(Application).where(Application.id == app_id, Application.user_id == user.id)
        )
    ).scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="application not found")

    try:
        artifact = await generate_for_application(
            session=session, user_id=user.id, application=app, request=payload
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"no {payload.provider.value} API key available — "
                "add one in settings or ask an admin to assign a global key"
            ),
        )

    return ArtifactRead.model_validate(artifact, from_attributes=True)
