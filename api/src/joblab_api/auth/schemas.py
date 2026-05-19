"""Auth request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from joblab_api.llm.models import LLMProvider


class LoginRequest(BaseModel):
    email: str
    password: str


class MeResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    is_premium: bool = False
    default_provider: LLMProvider | None = None


class SettingsUpdate(BaseModel):
    default_provider: LLMProvider | None = None
