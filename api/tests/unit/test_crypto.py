"""Unit tests for crypto.py."""

import pytest

from joblab_api.crypto import InvalidToken, decrypt_str, encrypt_str


def test_roundtrip_preserves_plaintext() -> None:
    assert decrypt_str(encrypt_str("sk-test-12345")) == "sk-test-12345"


def test_ciphertext_differs_per_call() -> None:
    a = encrypt_str("same-input")
    b = encrypt_str("same-input")
    assert a != b
    assert decrypt_str(a) == decrypt_str(b) == "same-input"


def test_empty_plaintext_rejected() -> None:
    with pytest.raises(ValueError):
        encrypt_str("")


def test_tampered_token_rejected() -> None:
    ct = encrypt_str("secret")
    tampered = ct[:-2] + ("AA" if ct[-2:] != "AA" else "BB")
    with pytest.raises(InvalidToken):
        decrypt_str(tampered)
