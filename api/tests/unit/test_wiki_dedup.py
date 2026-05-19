"""Unit tests for the wiki dedup classifier."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from joblab_api.wiki.dedup import FUZZY_THRESHOLD, classify, signature


def _row(**kwargs):
    kwargs.setdefault("id", uuid4())
    return SimpleNamespace(**kwargs)


def test_signature_skill_lowercase_strip() -> None:
    assert signature("skills", _row(name="  Python  ")) == "python"


def test_classify_new_on_empty() -> None:
    verdict, match = classify("skills", _row(name="Rust"), [])
    assert verdict == "new"
    assert match is None


def test_classify_exact_match_skipped() -> None:
    existing = _row(name="Python")
    verdict, match = classify("skills", _row(name="python"), [existing])
    assert verdict == "exact"
    assert match == existing.id


def test_classify_fuzzy_near_match() -> None:
    existing = _row(employer="Acme Limited", title="Senior Engineer")
    candidate = _row(employer="Acme Ltd", title="Senior Engineer")
    verdict, match = classify("experiences", candidate, [existing])
    assert verdict == "duplicate"
    assert match == existing.id


def test_classify_unrelated_is_new() -> None:
    existing = _row(employer="Acme Ltd", title="Senior Engineer")
    candidate = _row(employer="Globex", title="Marketing Manager")
    verdict, _ = classify("experiences", candidate, [existing])
    assert verdict == "new"


def test_fuzzy_threshold_constant_is_in_range() -> None:
    assert 50 < FUZZY_THRESHOLD <= 100
