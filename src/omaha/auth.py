"""Authentication helpers: password hashing and verification.

The seed script (and later the login route) use :func:`hash_password` /
:func:`verify_password` to handle the shared family password. Both
functions are bcrypt-backed; the hash format includes a per-call salt,
so equal passwords produce different hashes across runs.

Slice T03 adds session-cookie signing and the login/logout route handlers
on top of these primitives.
"""

from __future__ import annotations

import bcrypt


def hash_password(plaintext: str) -> str:
    """Hash ``plaintext`` with bcrypt and return a UTF-8 hash string.

    The salt is generated automatically by :func:`bcrypt.hashpw`. The
    returned value is safe to store in a ``String(255)`` column.
    """
    if not plaintext:
        raise ValueError("password must be a non-empty string")
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, password_hash: str) -> bool:
    """Return True if ``plaintext`` matches ``password_hash``."""
    if not plaintext or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed hash strings raise from bcrypt; treat as "no match"
        # rather than crashing the auth path.
        return False


__all__ = ["hash_password", "verify_password"]
