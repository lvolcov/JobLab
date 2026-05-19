"""Pydantic models for the AI's structured CV-extraction response.

The same shape is described to the LLM in the prompt and validated on receipt.
A failure on validation triggers one retry with a corrective hint.

Created: 2026-05-19
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


def _empty_to_none(v: object) -> object:
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


class _CV(BaseModel):
    title: str
    body_md: str = ""


class _Experience(BaseModel):
    employer: str
    title: str
    start: date | None = None
    end: date | None = None
    summary: str = ""
    achievements: str = ""

    _coerce_dates = field_validator("start", "end", mode="before")(_empty_to_none)


class _Project(BaseModel):
    name: str
    role: str = ""
    start: date | None = None
    end: date | None = None
    summary: str = ""
    achievements: str = ""

    _coerce_dates = field_validator("start", "end", mode="before")(_empty_to_none)


class _Skill(BaseModel):
    name: str
    level: str = ""
    notes: str = ""


class _Qualification(BaseModel):
    name: str
    issuer: str = ""
    date_awarded: date | None = None
    details: str = ""

    _coerce_dates = field_validator("date_awarded", mode="before")(_empty_to_none)


class _Education(BaseModel):
    institution: str
    qualification: str
    start: date | None = None
    end: date | None = None
    details: str = ""

    _coerce_dates = field_validator("start", "end", mode="before")(_empty_to_none)


class ExtractedCV(BaseModel):
    """Top-level shape the LLM must return."""

    cvs: list[_CV] = Field(default_factory=list)
    experiences: list[_Experience] = Field(default_factory=list)
    projects: list[_Project] = Field(default_factory=list)
    skills: list[_Skill] = Field(default_factory=list)
    qualifications: list[_Qualification] = Field(default_factory=list)
    education: list[_Education] = Field(default_factory=list)


# Schema description embedded in the prompt verbatim so the LLM knows the shape.
JSON_SCHEMA_HINT = """{
  "cvs":            [{"title": str, "body_md": str}],
  "experiences":    [{"employer": str, "title": str, "start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null, "summary": str, "achievements": str}],
  "projects":       [{"name": str, "role": str, "start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null, "summary": str, "achievements": str}],
  "skills":         [{"name": str, "level": str, "notes": str}],
  "qualifications": [{"name": str, "issuer": str, "date_awarded": "YYYY-MM-DD"|null, "details": str}],
  "education":      [{"institution": str, "qualification": str, "start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null, "details": str}]
}"""


class ImportSummary(BaseModel):
    """Per-entity summary returned to the client."""

    inserted: int = 0
    skipped_exact: int = 0
    flagged_duplicate: int = 0


class ImportResult(BaseModel):
    cvs: ImportSummary
    experiences: ImportSummary
    projects: ImportSummary
    skills: ImportSummary
    qualifications: ImportSummary
    education: ImportSummary
    provider: str
    attempts: int
