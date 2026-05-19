"""POST /wiki/import — extract a PDF CV and populate the wiki via the user's default LLM.

Created: 2026-05-19
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from joblab_api.auth.deps import CurrentUser
from joblab_api.config import get_settings
from joblab_api.db import SessionDep
from joblab_api.documents.parsing import extract_text, resolve_kind
from joblab_api.llm.service import resolve_api_key
from joblab_api.wiki.import_schemas import ImportResult
from joblab_api.wiki.import_service import import_cv_for_user

router = APIRouter(prefix="/wiki", tags=["wiki:import"])


@router.post("/import", response_model=ImportResult)
async def import_cv(
    user: CurrentUser,
    session: SessionDep,
    file: UploadFile = File(...),
) -> ImportResult:
    settings = get_settings()

    if user.default_provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="set a default AI provider in Settings before importing",
        )

    api_key = await resolve_api_key(session, user.id, user.default_provider)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no working key for your default provider",
        )

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="file too large",
        )

    kind = resolve_kind(file.content_type or "", file.filename or "")
    if kind != "pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only PDF uploads are supported for CV import",
        )

    try:
        cv_text = extract_text("pdf", data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"could not parse PDF: {exc}",
        ) from exc

    if not cv_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF appears to be empty or image-only (no text layer)",
        )

    try:
        return await import_cv_for_user(
            session=session,
            user_id=user.id,
            provider=user.default_provider,
            api_key=api_key,
            cv_text=cv_text,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
