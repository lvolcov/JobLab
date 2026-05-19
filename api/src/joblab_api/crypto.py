"""Fernet-based encrypt/decrypt for at-rest secrets (e.g. LLM API keys).

Purpose: thin wrapper around cryptography.fernet keyed off settings.FERNET_KEY.
Created: 2026-05-19
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from joblab_api.config import get_settings


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    key = get_settings().fernet_key
    if not key:
        raise RuntimeError("FERNET_KEY is not configured")
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_str(plaintext: str) -> str:
    """Return a Fernet ciphertext (urlsafe base64) for the given string."""
    if not plaintext:
        raise ValueError("plaintext is empty")
    return _cipher().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_str(token: str) -> str:
    """Reverse of encrypt_str. Raises InvalidToken on tampering / wrong key."""
    return _cipher().decrypt(token.encode("utf-8")).decode("utf-8")


def reset_cache_for_tests() -> None:
    """Drop the cached Fernet so tests can swap FERNET_KEY mid-process."""
    _cipher.cache_clear()


__all__ = ["encrypt_str", "decrypt_str", "InvalidToken", "reset_cache_for_tests"]
