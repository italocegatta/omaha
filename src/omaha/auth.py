"""Authentication helpers: password hashing, session-cookie readers.

The seed script (and the login route) use :func:`hash_password` /
:func:`verify_password` to handle the shared family password. The session
helpers (:func:`get_current_user`, :func:`require_user`,
:func:`get_active_profile`, :func:`require_active_profile`) are
cookie-backed via Starlette's :class:`SessionMiddleware` and read the
``user_id`` and ``active_profile_id`` keys out of ``request.session``.

Cookie contract
---------------
- ``request.session["user_id"]`` is set on successful login and cleared
  on logout. Routes that need an authenticated user call
  :func:`require_user`; the helper raises an ``HTTPException(303)``
  pointing at ``/login`` so a bare ``GET /`` from an unauthenticated
  browser follows the redirect chain ``/`` -> ``/login`` -> form.
- ``request.session["active_profile_id"]`` is set on profile selection
  and *cleared* on login so the user is forced to pick a profile each
  session. Pages that need a profile (the dashboard) call
  :func:`require_active_profile`; the helper raises ``404`` if no
  profile is selected.

Bcrypt's 72-byte ceiling is enforced inside :func:`verify_password`
(it returns ``False`` instead of raising ``ValueError``), so a
malformed or over-long input from a client never crashes the login
route.
"""

from __future__ import annotations

from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from omaha.db import get_db
from omaha.models import Profile, User

# FastAPI's idiomatic dependency-injection signature. ``Annotated``
# avoids the ``B008`` lint warning about ``Depends`` in argument
# defaults and is the recommended style in FastAPI ≥ 0.95.
DbSession = Annotated[Session, Depends(get_db)]


def hash_password(plaintext: str) -> str:
    """Hash ``plaintext`` with bcrypt and return a UTF-8 hash string.

    The salt is generated automatically by :func:`bcrypt.hashpw`. The
    returned value is safe to store in a ``String(255)`` column.
    """
    if not plaintext:
        raise ValueError("password must be a non-empty string")
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plaintext: str, password_hash: str) -> bool:
    """Return True if ``plaintext`` matches ``password_hash``.

    Returns ``False`` rather than raising for the two common error
    cases: empty input and malformed/over-long input (bcrypt raises
    ``ValueError`` for inputs above 72 bytes).
    """
    if not plaintext or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed hash strings or over-long plaintext raise from
        # bcrypt; treat as "no match" rather than crashing the auth path.
        return False


def get_current_user(request: Request, db: DbSession) -> User | None:
    """Return the :class:`User` recorded in the session, or ``None``.

    ``None`` is returned both when no ``user_id`` is in the session and
    when the recorded id no longer maps to a real row (e.g. the user was
    deleted while a session cookie was still valid). Routes that
    *require* a user should call :func:`require_user` instead.

    ``db`` is wired through :func:`omaha.db.get_db` so this function is
    usable both as a plain helper (passing a session explicitly) and as
    a FastAPI dependency (``Depends(get_current_user)``).
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(request: Request, db: DbSession) -> User:
    """Return the current :class:`User`, or raise a redirect to ``/login``.

    The raised :class:`HTTPException` uses status ``303`` with a
    ``Location`` header, which produces a real HTTP redirect when the
    browser or the test client receives the response. The status code
    matches the in-app redirects so the *appearance* of "you bounced off
    a protected page" is uniform across the app.
    """
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user


def get_active_profile(request: Request, db: DbSession) -> Profile | None:
    """Return the :class:`Profile` recorded in the session, or ``None``.

    The profile is also rejected if it doesn't belong to the current
    user (e.g. a session cookie from a previous account, or a profile
    that was deleted out from under an active session).
    """
    profile_id = request.session.get("active_profile_id")
    if profile_id is None:
        return None
    profile = db.get(Profile, profile_id)
    if profile is None:
        return None
    user_id = request.session.get("user_id")
    if user_id is not None and profile.user_id != user_id:
        return None
    return profile


def require_active_profile(request: Request, db: DbSession) -> Profile:
    """Return the active :class:`Profile`, or raise ``404``.

    Pages that need a profile (the dashboard) call this; the protected
    pages route (``/``) instead *redirects* to ``/profiles`` when the
    user has no active profile, so the only way to land here without a
    profile is a stale cookie. A 404 is the right response for a stale
    cookie — the user picked nothing valid.
    """
    profile = get_active_profile(request, db)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return profile


__all__ = [
    "hash_password",
    "verify_password",
    "get_current_user",
    "require_user",
    "get_active_profile",
    "require_active_profile",
]
