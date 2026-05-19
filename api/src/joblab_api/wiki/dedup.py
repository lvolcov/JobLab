"""Duplicate detection helpers for wiki imports.

Strategy:
- Build a canonical signature per entity (lowercased, whitespace-collapsed).
- Exact signature match against an existing row -> skip.
- rapidfuzz token_set_ratio >= FUZZY_THRESHOLD against any existing row -> insert
  with ``possible_duplicate_of_id`` pointing at the closest match.
- Otherwise -> insert clean.

Created: 2026-05-19
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from rapidfuzz import fuzz

FUZZY_THRESHOLD = 85.0

_WS = re.compile(r"\s+")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return _WS.sub(" ", str(value)).strip().lower()


def _join(*parts: Any) -> str:
    return " | ".join(p for p in (_norm(x) for x in parts) if p)


def signature(entity: str, row: Any) -> str:
    """Canonical short signature used for both exact and fuzzy comparison."""
    g = lambda k: getattr(row, k, None) if not isinstance(row, dict) else row.get(k)  # noqa: E731
    if entity == "cvs":
        return _join(g("title"))
    if entity == "experiences":
        return _join(g("employer"), g("title"))
    if entity == "projects":
        return _join(g("name"), g("role"))
    if entity == "skills":
        return _join(g("name"))
    if entity == "qualifications":
        return _join(g("name"), g("issuer"))
    if entity == "education":
        return _join(g("institution"), g("qualification"))
    raise ValueError(f"unknown entity: {entity}")


def classify(
    entity: str,
    candidate: Any,
    existing: list[Any],
) -> tuple[str, UUID | None]:
    """Return ('exact', id), ('duplicate', id), or ('new', None).

    - ``exact``: identical signature -> caller should skip.
    - ``duplicate``: fuzzy match >= threshold -> caller should insert + tag.
    - ``new``: nothing close enough.
    """
    sig = signature(entity, candidate)
    if not sig:
        return "new", None

    best_id: UUID | None = None
    best_score = 0.0
    for row in existing:
        other = signature(entity, row)
        if not other:
            continue
        if other == sig:
            return "exact", row.id
        score = fuzz.token_set_ratio(sig, other)
        if score > best_score:
            best_score = score
            best_id = row.id

    if best_score >= FUZZY_THRESHOLD:
        return "duplicate", best_id
    return "new", None
