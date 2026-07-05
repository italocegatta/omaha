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
- ``request.session["active_profile_id"]`` is set on successful login
  (to the logged-in user's first profile by ``display_order``) and
  re-bound by ``POST /profiles/{id}/select`` (the header chip). It
  is *not* cleared on re-login — a fresh login replaces it with the
  new landing profile. Pages that need a profile (the dashboard)
  call :func:`require_active_profile`; the helper raises ``404`` if
  no profile is selected.

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

    Returns ``None`` when:

    * ``active_profile_id`` is missing,
    * the recorded id no longer maps to a real row (the profile was
      deleted out from under an active session), or
    * (F07) the bound row is the Família sentinel
      (``Profile.is_family_sentinel=True``). The sentinel is the
      canonical cross-User family aggregate (peer of real profiles
      in the profile-switcher chip — see design D-F07.1); it owns
      zero ``AssetClass`` rows, so the routes that consume this
      helper (``get_active_profile``, ``require_active_profile``,
      the ``?view=family`` querystring path) need a clean
      "not-a-real-profile" signal. Routes that render the family
      aggregate detect the sentinel themselves via the
      ``Profile.is_family_sentinel`` flag on the row they get back
      from the session — see :func:`omaha.routes.pages._render_patrimonio`.

    The prior per-user ownership check (``profile.user_id != user_id``)
    was removed when cross-profile viewing became the explicit
    contract: any logged-in user can bind any real profile via the
    header chip, and the active profile is whatever
    ``active_profile_id`` points to. The Família sentinel is the
    only Profile row that gets short-circuited here — its presence
    in the session is a feature, not a stale binding.
    """
    profile_id = request.session.get("active_profile_id")
    if profile_id is None:
        return None
    profile = db.get(Profile, profile_id)
    if profile is None:
        return None
    if profile.is_family_sentinel:
        return None
    return profile


def require_active_profile(request: Request, db: DbSession) -> Profile:
    """Return the active :class:`Profile`, or raise ``404``.

    Pages that need a profile (the dashboard) call this; the protected
    pages route (``/``) instead *redirects* to ``/login`` when the
    user has no active profile, so the only way to land here without a
    profile is a stale cookie. A 404 is the right response for a stale
    cookie — the user picked nothing valid.
    """
    profile = get_active_profile(request, db)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return profile


class HouseholdReadOnlyError(Exception):
    """Raised by :func:`require_profile_writable` when household mode is on.

    Carries the exact wire shape the
    ``cross-profile-sharing`` ADDED Requirement "household mode is
    read-only" requires. ``HouseholdReadOnlyError`` is converted
    into a 409 ``{"reason": "household_read_only"}`` JSON body by
    the handler registered in :func:`register_exception_handlers`.

    A custom exception is preferred over :class:`HTTPException`
    because FastAPI's default handler wraps the body in
    ``{"detail": ...}``. The spec's wire shape is exactly
    ``{"reason": "household_read_only"}`` — no outer wrapper.
    """

    def __init__(self) -> None:
        super().__init__("household_read_only")
        self.reason = "household_read_only"


def register_exception_handlers(app) -> None:
    """Install the :class:`HouseholdReadOnlyError` handler on ``app``.

    Called once during app construction (``omaha.main``). Tests that
    build their own app via ``fastapi.testclient.TestClient`` against
    the production module are covered by the same handler — the
    module-level :func:`require_profile_writable` import only ever
    fires inside a registered route, so the handler must exist on
    the app that hosts the route.
    """
    from starlette.responses import JSONResponse

    @app.exception_handler(HouseholdReadOnlyError)
    async def _household_read_only_handler(
        request: Request, exc: HouseholdReadOnlyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"reason": exc.reason},
        )


def require_profile_writable(request: Request):
    """Gate mutation endpoints against the family read-only mode (F01 / F06).

    F01 — the :class:`User` activates the household aggregate view
    by visiting ``GET /patrimonio?view=household``. The route
    handler sets ``request.session["view_mode"] = "household"`` so
    the dependency can be evaluated against the session rather than
    the querystring (the querystring would be lost on a JSON POST
    from a modal fetch). The session key is cleared the moment the
    operator returns to ``view=profile``.

    F06 — the internal session flag is renamed to ``"family"`` to
    match the renamed family aggregate. The dependency accepts
    BOTH ``"family"`` (new) and ``"household"`` (legacy) during the
    cutover so any stale session cookie or in-flight request from
    a previous deploy does not silently bypass the gate. The wire
    shape of the 409 body stays exactly
    ``{"reason": "household_read_only"}`` for backward compatibility
    (F01 wire contract); F06 deliberately does not rename the JSON
    reason because every consumer (tests, e2e selectors, future
    audit pipeline) already keys on that string.

    Returns ``None`` when the session is in the default mode so
    the dependency is a no-op for the common path. Raises
    :class:`HouseholdReadOnlyError` when either flag is active —
    the handler registered in :func:`register_exception_handlers`
    converts the exception into the 409 body.

    Audit logging is a deliberate no-op: 409s on a UI-driven
    toggle are not actionable audit signal (the operator can
    see they clicked the toggle). If a downstream route ever
    needs audit, it should call :func:`require_profile_writable`
    and emit its own log line with the user id and endpoint.
    """
    view_mode = request.session.get("view_mode")
    if view_mode in ("family", "household"):
        raise HouseholdReadOnlyError()
    return None


__all__ = [
    "hash_password",
    "verify_password",
    "get_current_user",
    "require_user",
    "get_active_profile",
    "require_active_profile",
    "require_profile_writable",
    "HouseholdReadOnlyError",
    "register_exception_handlers",
]
