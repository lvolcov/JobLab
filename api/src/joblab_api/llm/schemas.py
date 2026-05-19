"""Request/response schemas for LLM key management.

The raw API key is never echoed back to clients — only metadata.
Created: 2026-05-19
"""

from uuid import UUID

from pydantic import BaseModel, Field

from joblab_api.llm.models import LLMProvider


class LLMKeyRead(BaseModel):
    id: UUID
    provider: LLMProvider
    label: str
    is_global: bool
    owner_user_id: UUID | None
    masked_key: str = Field(
        default="****",
        description="Always '****'; the encrypted key is never exposed.",
    )


class GlobalKeyCreate(BaseModel):
    provider: LLMProvider
    label: str = Field(min_length=1, max_length=128)
    api_key: str = Field(min_length=1)


class UserKeyCreate(BaseModel):
    provider: LLMProvider
    label: str = Field(min_length=1, max_length=128)
    api_key: str = Field(min_length=1)


class AssignmentCreate(BaseModel):
    user_id: UUID
