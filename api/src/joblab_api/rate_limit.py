"""Rate limit configuration using slowapi.

- `/auth/login`: 10/min per remote IP (brute-force protection).
- `/applications/{id}/generate`: 20/hour per IP (LLM cost containment).

Both are disabled when JOBLAB_TEST_MODE=1 so test suites aren't throttled.
Created: 2026-05-19
"""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

# When set, all limiters become no-ops — used by Playwright e2e + pytest.
_DISABLED = os.getenv("JOBLAB_TEST_MODE") == "1"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[] if _DISABLED else [],
    enabled=not _DISABLED,
)

LOGIN_LIMIT = "10/minute"
GENERATE_LIMIT = "20/hour"


def rate_limit_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        {"detail": "too many requests; slow down"},
        status_code=429,
    )
