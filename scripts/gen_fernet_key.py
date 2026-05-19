#!/usr/bin/env python3
"""Generate a new Fernet key and print it as `FERNET_KEY=...`.

Purpose: bootstrap or rotate the at-rest encryption key for LLM API secrets.
Usage: `python scripts/gen_fernet_key.py >> .env`
Created: 2026-05-19
"""

from __future__ import annotations

from cryptography.fernet import Fernet


def main() -> None:
    print(f"FERNET_KEY={Fernet.generate_key().decode()}")


if __name__ == "__main__":
    main()
