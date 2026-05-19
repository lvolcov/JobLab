"""Password hashing and JWT helpers.

Purpose: bcrypt for password hashes; HS256 JWTs for session cookies.
Created: 2026-05-19
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from joblab_api.config import get_settings

SESSION_COOKIE_NAME = "joblab_session"
SESSION_TTL = timedelta(days=7)
_ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_session_token(user_id: UUID) -> str:
    """Encode a JWT carrying the user id and expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + SESSION_TTL).timestamp()),
    }
    secret = get_settings().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not configured")
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_session_token(token: str) -> UUID | None:
    """Decode a JWT and return the user id, or None on any failure."""
    secret = get_settings().jwt_secret
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
