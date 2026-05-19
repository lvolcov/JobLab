"""Aggregate import of all SQLModel tables.

Purpose: a single import that registers every model with SQLModel.metadata.
Imported by Alembic env.py and by the test fixture.
Created: 2026-05-19
"""

from __future__ import annotations

from joblab_api.applications.models import Application, ApplicationArtifact
from joblab_api.documents.models import Document
from joblab_api.llm.models import LLMKey, LLMKeyAssignment
from joblab_api.users.models import User
from joblab_api.wiki.models import (
    WikiCV,
    WikiEducation,
    WikiExperience,
    WikiProject,
    WikiQualification,
    WikiSkill,
)

__all__ = [
    "User",
    "LLMKey",
    "LLMKeyAssignment",
    "WikiCV",
    "WikiEducation",
    "WikiQualification",
    "WikiSkill",
    "WikiProject",
    "WikiExperience",
    "Document",
    "Application",
    "ApplicationArtifact",
]
