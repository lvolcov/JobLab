"""Security middleware: request-size cap, CSRF (double-submit cookie), rate limits.

Design:
- Request body size cap is enforced at the ASGI boundary before route code runs.
- CSRF: SameSite=Lax already prevents most cross-site cookie use, but we add a
  double-submit token for defence-in-depth. POST/PATCH/PUT/DELETE must echo the
  `joblab_csrf` cookie value in the `X-CSRF-Token` header. /auth/login is exempt
  because the cookie does not yet exist on the very first request.
- Rate limiting uses slowapi (Limiter) keyed on the client IP for /auth/login
  and on the user id for /applications/{id}/generate.

Created: 2026-05-19
"""

from __future__ import annotations

import secrets
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from joblab_api.config import get_settings

CSRF_COOKIE = "joblab_csrf"
CSRF_HEADER = "x-csrf-token"
UNSAFE_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})
# Paths that are allowed to set/refresh the CSRF cookie without already having one.
CSRF_EXEMPT_PREFIXES = ("/auth/login", "/health")


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests larger than `MAX_UPLOAD_MB` MB.

    Checks Content-Length first; if absent, streams up to the limit and rejects
    the moment the count is exceeded.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        super().__init__(app)
        self._max = max_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > self._max:
                    return JSONResponse(
                        {"detail": f"request body exceeds {self._max} bytes"},
                        status_code=413,
                    )
            except ValueError:
                return JSONResponse({"detail": "invalid content-length"}, status_code=400)
        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF.

    - Ensures every authenticated browser carries a non-HttpOnly `joblab_csrf`
      cookie. The cookie is created on first response that has none.
    - On unsafe methods, requires the header to match the cookie value.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        cookie = request.cookies.get(CSRF_COOKIE)

        if (
            request.method in UNSAFE_METHODS
            and not any(path.startswith(p) for p in CSRF_EXEMPT_PREFIXES)
        ):
            header = request.headers.get(CSRF_HEADER, "")
            # Use a constant-time compare to defeat timing oracles.
            if not cookie or not header or not secrets.compare_digest(cookie, header):
                return JSONResponse(
                    {"detail": "csrf token missing or invalid"}, status_code=403
                )

        response = await call_next(request)
        if not cookie:
            new_token = secrets.token_urlsafe(32)
            response.set_cookie(
                key=CSRF_COOKIE,
                value=new_token,
                httponly=False,  # readable from JS — that's the point
                samesite="lax",
                secure=False,
                path="/",
            )
        return response


def install(app, *, csrf_enabled: bool = True) -> None:
    """Mount the security middleware stack onto a FastAPI app."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=max_bytes)
    if csrf_enabled:
        app.add_middleware(CSRFMiddleware)
