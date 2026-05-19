"""Deterministic JSON-emitting stub used when JOBLAB_TEST_MODE=1.

The shape mirrors ExtractedCV. The Playwright suite uses this so importing a
PDF in tests produces predictable rows without hitting a real LLM.

Created: 2026-05-19
"""

from __future__ import annotations

import json

_FIXTURE = {
    "cvs": [
        {"title": "Imported CV", "body_md": "# Imported CV\n\nExtracted from PDF."}
    ],
    "experiences": [
        {
            "employer": "Acme Ltd",
            "title": "Senior Engineer",
            "start": "2020-01-01",
            "end": "2023-06-01",
            "summary": "Led a small team building data pipelines.",
            "achievements": "- Cut latency 40%\n- Mentored 3 engineers",
        }
    ],
    "projects": [
        {
            "name": "Internal analytics platform",
            "role": "Tech lead",
            "start": "2021-03-01",
            "end": "2022-09-01",
            "summary": "Self-serve dashboards for ops teams.",
            "achievements": "- Adopted by 50+ users",
        }
    ],
    "skills": [
        {"name": "Python", "level": "expert", "notes": ""},
        {"name": "FastAPI", "level": "advanced", "notes": ""},
    ],
    "qualifications": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "date_awarded": "2022-04-15",
            "details": "",
        }
    ],
    "education": [
        {
            "institution": "University of Edinburgh",
            "qualification": "MSc Data Science",
            "start": "2017-09-01",
            "end": "2018-09-01",
            "details": "Distinction.",
        }
    ],
}


class JsonStubAdapter:
    provider_name = "test-json"

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.4,
    ) -> str:
        _ = (prompt, system, max_tokens, temperature)
        return json.dumps(_FIXTURE)
