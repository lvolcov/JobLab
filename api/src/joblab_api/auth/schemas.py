"""Auth request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class MeResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
