"""Unit tests for the LLM response parser used by wiki import."""

from __future__ import annotations

import json

import pytest

from joblab_api.wiki.import_schemas import ExtractedCV
from joblab_api.wiki.import_service import _extract_json, parse_with_llm


class _Adapter:
    def __init__(self, replies: list[str]) -> None:
        self.replies = replies
        self.calls = 0

    async def generate(self, prompt: str, *, system: str = "", **kw) -> str:
        reply = self.replies[self.calls]
        self.calls += 1
        return reply


def test_extract_json_strips_code_fence() -> None:
    raw = "```json\n{\"cvs\": []}\n```"
    assert json.loads(_extract_json(raw)) == {"cvs": []}


def test_extract_json_handles_prose_prefix() -> None:
    raw = 'Sure! Here is the JSON:\n{"cvs": [{"title": "x", "body_md": ""}]}'
    assert json.loads(_extract_json(raw)) == {
        "cvs": [{"title": "x", "body_md": ""}]
    }


async def test_parse_with_llm_succeeds_first_try() -> None:
    payload = json.dumps({"skills": [{"name": "Python"}]})
    adapter = _Adapter([payload])
    result = await parse_with_llm(adapter, "ignored")
    assert isinstance(result, ExtractedCV)
    assert result.skills[0].name == "Python"
    assert adapter.calls == 1


async def test_parse_with_llm_retries_on_malformed_json() -> None:
    adapter = _Adapter(
        ["not json at all", json.dumps({"skills": [{"name": "Rust"}]})]
    )
    result = await parse_with_llm(adapter, "ignored")
    assert result.skills[0].name == "Rust"
    assert adapter.calls == 2


async def test_parse_with_llm_raises_after_max_attempts() -> None:
    adapter = _Adapter(["nope", "still nope"])
    with pytest.raises(ValueError):
        await parse_with_llm(adapter, "ignored")
