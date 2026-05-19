"""User schemas for admin endpoints."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class UserRead(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    is_verified: bool


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)
