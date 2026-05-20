"""Applications CRUD + artifact listing."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from joblab_api.applications.models import Application, ApplicationArtifact
from joblab_api.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    ArtifactRead,
)
from joblab_api.auth.deps import CurrentUser
from joblab_api.db import SessionDep

router = APIRouter(prefix="/applications", tags=["applications"])


def _to_read(a: Application) -> ApplicationRead:
    return ApplicationRead(
        id=a.id,
        role_title=a.role_title,
        company=a.company,
        jd_text=a.jd_text,
        status=a.status,
        applied_at=a.applied_at,
        feedback=a.feedback,
        notes=a.notes,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


async def _get_owned_or_404(session, user_id: UUID, app_id: UUID) -> Application:
    app = (
        await session.execute(
            select(Application).where(Application.id == app_id, Application.user_id == user_id)
        )
    ).scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return app


@router.get("", response_model=list[ApplicationRead])
async def list_(session: SessionDep, user: CurrentUser) -> list[ApplicationRead]:
    rows = (
        await session.execute(
            select(Application)
            .where(Application.user_id == user.id)
            .order_by(Application.created_at.desc())
        )
    ).scalars().all()
    return [_to_read(a) for a in rows]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ApplicationCreate, session: SessionDep, user: CurrentUser
) -> ApplicationRead:
    app = Application(user_id=user.id, **payload.model_dump())
    session.add(app)
    await session.commit()
    await session.refresh(app)
    return _to_read(app)


@router.get("/{app_id}", response_model=ApplicationRead)
async def get(app_id: UUID, session: SessionDep, user: CurrentUser) -> ApplicationRead:
    return _to_read(await _get_owned_or_404(session, user.id, app_id))


@router.patch("/{app_id}", response_model=ApplicationRead)
async def update(
    app_id: UUID,
    payload: ApplicationUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> ApplicationRead:
    app = await _get_owned_or_404(session, user.id, app_id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(app, k, v)
    app.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(app)
    return _to_read(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(app_id: UUID, session: SessionDep, user: CurrentUser):
    app = await _get_owned_or_404(session, user.id, app_id)
    await session.delete(app)
    await session.commit()


@router.get("/{app_id}/artifacts", response_model=list[ArtifactRead])
async def list_artifacts(
    app_id: UUID, session: SessionDep, user: CurrentUser
) -> list[ArtifactRead]:
    await _get_owned_or_404(session, user.id, app_id)
    rows = (
        await session.execute(
            select(ApplicationArtifact)
            .where(ApplicationArtifact.application_id == app_id)
            .order_by(ApplicationArtifact.created_at.desc())
        )
    ).scalars().all()
    return [ArtifactRead.model_validate(r, from_attributes=True) for r in rows]
