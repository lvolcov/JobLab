"""Document upload + listing routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select

from joblab_api.auth.deps import CurrentUser
from joblab_api.config import get_settings
from joblab_api.db import SessionDep
from joblab_api.documents.models import Document
from joblab_api.documents.parsing import extract_text, resolve_kind

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    mime: str
    size_bytes: int
    parsed_text: str
    created_at: datetime


def _to_read(doc: Document) -> DocumentRead:
    return DocumentRead(
        id=doc.id,
        filename=doc.filename,
        mime=doc.mime,
        size_bytes=doc.size_bytes,
        parsed_text=doc.parsed_text,
        created_at=doc.created_at,
    )


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload(
    session: SessionDep,
    user: CurrentUser,
    file: UploadFile = File(...),
) -> DocumentRead:
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds {settings.max_upload_mb} MB limit",
        )

    kind = resolve_kind(file.content_type or "", file.filename or "")
    if kind is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="unsupported file type; allowed: pdf, docx, txt, md",
        )

    try:
        text = extract_text(kind, data)
    except Exception:  # parser failure → bad payload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="failed to parse file",
        )

    doc = Document(
        user_id=user.id,
        filename=file.filename or "upload",
        mime=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        parsed_text=text,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return _to_read(doc)


@router.get("", response_model=list[DocumentRead])
async def list_documents(session: SessionDep, user: CurrentUser) -> list[DocumentRead]:
    rows = (
        await session.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
        )
    ).scalars().all()
    return [_to_read(d) for d in rows]


@router.get("/{doc_id}", response_model=DocumentRead)
async def get_document(doc_id: UUID, session: SessionDep, user: CurrentUser) -> DocumentRead:
    doc = (
        await session.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user.id)
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return _to_read(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: UUID, session: SessionDep, user: CurrentUser):
    doc = (
        await session.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user.id)
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    await session.delete(doc)
    await session.commit()
