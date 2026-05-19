"""joblab API entrypoint.

Purpose: FastAPI app composition + global middleware + rate-limit handler.
Created: 2026-05-19
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from joblab_api.applications.router import router as applications_router
from joblab_api.auth.router import router as auth_router
from joblab_api.config import get_settings
from joblab_api.documents.router import router as documents_router
from joblab_api.generation.router import router as generation_router
from joblab_api.llm.router import admin_router as llm_admin_router
from joblab_api.llm.router import user_router as llm_user_router
from joblab_api.rate_limit import limiter, rate_limit_handler
from joblab_api.security_middleware import install as install_security
from joblab_api.users.router import router as admin_users_router
from joblab_api.wiki.router import router as wiki_router

app = FastAPI(title="joblab API", version="0.1.0")

# Rate-limit registry + handler (slowapi).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

_settings = get_settings()
if _settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

install_security(app)


@app.get("/health")
def health() -> dict[str, bool]:
    """Liveness probe used by Docker and the frontend."""
    return {"ok": True}


app.include_router(auth_router)
app.include_router(admin_users_router)
app.include_router(llm_admin_router)
app.include_router(llm_user_router)
app.include_router(wiki_router)
app.include_router(documents_router)
app.include_router(applications_router)
app.include_router(generation_router)
