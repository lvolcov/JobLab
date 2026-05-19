"""Word-count utilities for the generation engine.

A "word" is any whitespace-separated run of non-whitespace characters
(after stripping markdown headings / bullets). Good enough for civil-
service-style behaviour limits.
Created: 2026-05-19
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"\S+")


def count_words(text: str) -> int:
    """Return the number of whitespace-separated words in `text`."""
    if not text:
        return 0
    return sum(1 for _ in _WORD_RE.finditer(text))


def is_within_limit(text: str, limit: int) -> bool:
    """Return True if `text` is at or below `limit` words."""
    return count_words(text) <= limit
