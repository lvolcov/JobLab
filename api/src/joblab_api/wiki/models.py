"""Wiki ORM models.

Purpose: structured per-user records that feed AI-generated documents.
All tables share (id, user_id FK, created_at, updated_at).
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _user_fk() -> Column:
    return Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)


class WikiCV(SQLModel, table=True):
    __tablename__ = "wiki_cvs"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    title: str = Field(max_length=200, nullable=False)
    body_md: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class WikiEducation(SQLModel, table=True):
    __tablename__ = "wiki_education"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    institution: str = Field(max_length=200, nullable=False)
    qualification: str = Field(max_length=200, nullable=False)
    start: date | None = None
    end: date | None = None
    details: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class WikiQualification(SQLModel, table=True):
    __tablename__ = "wiki_qualifications"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    name: str = Field(max_length=200, nullable=False)
    issuer: str = Field(default="", max_length=200, nullable=False)
    date_awarded: date | None = None
    details: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class WikiSkill(SQLModel, table=True):
    __tablename__ = "wiki_skills"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    name: str = Field(max_length=120, nullable=False)
    level: str = Field(default="", max_length=40, nullable=False)
    notes: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class WikiProject(SQLModel, table=True):
    __tablename__ = "wiki_projects"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    name: str = Field(max_length=200, nullable=False)
    role: str = Field(default="", max_length=200, nullable=False)
    start: date | None = None
    end: date | None = None
    summary: str = Field(default="", nullable=False)
    achievements: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class WikiExperience(SQLModel, table=True):
    __tablename__ = "wiki_experiences"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(sa_column=_user_fk())
    employer: str = Field(max_length=200, nullable=False)
    title: str = Field(max_length=200, nullable=False)
    start: date | None = None
    end: date | None = None
    summary: str = Field(default="", nullable=False)
    achievements: str = Field(default="", nullable=False)
    created_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=_utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
