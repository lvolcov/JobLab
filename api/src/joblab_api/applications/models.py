"""Application + ApplicationArtifact ORM."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel

from joblab_api.llm.models import LLMProvider


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ArtifactType(str, Enum):
    CV = "cv"
    COVER_LETTER = "cover_letter"
    BLIND_CV = "blind_cv"
    BEHAVIOUR = "behaviour"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    role_title: str = Field(max_length=300, nullable=False)
    company: str = Field(default="", max_length=300, nullable=False)
    jd_text: str = Field(default="", nullable=False)
    status: ApplicationStatus = Field(default=ApplicationStatus.APPLIED, nullable=False)
    applied_at: date | None = None
    feedback: str = Field(default="", nullable=False)
    notes: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class ApplicationArtifact(SQLModel, table=True):
    __tablename__ = "application_artifacts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    application_id: UUID = Field(
        sa_column=Column(
            ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    type: ArtifactType = Field(nullable=False)
    provider: LLMProvider = Field(nullable=False)
    word_limit: int = Field(nullable=False)
    attempts: int = Field(nullable=False)
    final_word_count: int = Field(nullable=False)
    warning_flag: bool = Field(default=False, nullable=False)
    content: str = Field(default="", nullable=False)
    extra_instructions: str = Field(default="", nullable=False)
    behaviour_name: str | None = None
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
