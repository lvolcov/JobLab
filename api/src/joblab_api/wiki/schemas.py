"""Wiki request/response schemas.

Each entity has Create / Update / Read variants. Update fields are optional
to support PATCH semantics.
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


# ---------- CV ----------
class CVBase(BaseModel):
    title: str
    body_md: str = ""


class CVCreate(CVBase):
    pass


class CVUpdate(BaseModel):
    title: str | None = None
    body_md: str | None = None


class CVRead(CVBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Education ----------
class EducationBase(BaseModel):
    institution: str
    qualification: str
    start: date | None = None
    end: date | None = None
    details: str = ""


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = None
    qualification: str | None = None
    start: date | None = None
    end: date | None = None
    details: str | None = None


class EducationRead(EducationBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Qualification ----------
class QualificationBase(BaseModel):
    name: str
    issuer: str = ""
    date_awarded: date | None = None
    details: str = ""


class QualificationCreate(QualificationBase):
    pass


class QualificationUpdate(BaseModel):
    name: str | None = None
    issuer: str | None = None
    date_awarded: date | None = None
    details: str | None = None


class QualificationRead(QualificationBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Skill ----------
class SkillBase(BaseModel):
    name: str
    level: str = ""
    notes: str = ""


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    level: str | None = None
    notes: str | None = None


class SkillRead(SkillBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Project ----------
class ProjectBase(BaseModel):
    name: str
    role: str = ""
    start: date | None = None
    end: date | None = None
    summary: str = ""
    achievements: str = ""


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    start: date | None = None
    end: date | None = None
    summary: str | None = None
    achievements: str | None = None


class ProjectRead(ProjectBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ---------- Experience ----------
class ExperienceBase(BaseModel):
    employer: str
    title: str
    start: date | None = None
    end: date | None = None
    summary: str = ""
    achievements: str = ""


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    employer: str | None = None
    title: str | None = None
    start: date | None = None
    end: date | None = None
    summary: str | None = None
    achievements: str | None = None


class ExperienceRead(ExperienceBase):
    id: UUID
    possible_duplicate_of_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
