"""Application + generation schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from joblab_api.applications.models import ApplicationStatus, ArtifactType
from joblab_api.llm.models import LLMProvider


class ApplicationCreate(BaseModel):
    role_title: str
    company: str = ""
    jd_text: str = ""
    status: ApplicationStatus = ApplicationStatus.APPLIED
    applied_at: date | None = None
    feedback: str = ""
    notes: str = ""


class ApplicationUpdate(BaseModel):
    role_title: str | None = None
    company: str | None = None
    jd_text: str | None = None
    status: ApplicationStatus | None = None
    applied_at: date | None = None
    feedback: str | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: UUID
    role_title: str
    company: str
    jd_text: str
    status: ApplicationStatus
    applied_at: date | None
    feedback: str
    notes: str
    created_at: datetime
    updated_at: datetime


class GenerateRequest(BaseModel):
    type: ArtifactType
    provider: LLMProvider
    word_limit: int | None = Field(
        default=None, description="Per-document word cap. Defaults to 250 for behaviour."
    )
    extra_instructions: str = ""
    behaviour_name: str | None = Field(
        default=None,
        description="Required when type='behaviour' (e.g. 'Leadership').",
    )
    grade: str | None = Field(
        default=None,
        description="Civil Service grade for context (e.g. 'Grade 7', 'SEO'). Used to inject grade-appropriate behaviour descriptors.",
    )


class ArtifactRead(BaseModel):
    id: UUID
    application_id: UUID
    type: ArtifactType
    provider: LLMProvider
    word_limit: int
    attempts: int
    final_word_count: int
    warning_flag: bool
    content: str
    extra_instructions: str
    behaviour_name: str | None
    grade: str | None
    created_at: datetime
