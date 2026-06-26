"""Login / logout routes.

The login form is a single shared-password form (no per-user account
typeahead), since the family-portfolio model is one operator account
with multiple profiles. The ``username`` field is collected for the
audit log / future per-user expansion; today it is matched against the
``family`` row created by the seed.

Session lifecycle
-----------------
- ``GET /login`` — render the form, or redirect to ``/`` if the user
  is already authenticated.
- ``POST /login`` — verify the shared password. On success, set
  ``user_id`` in the session AND bind ``active_profile_id`` to the
  logged-in user's first profile (by ``display_order``). The user
  lands directly on their own dashboard at ``/`` — there is no
  intermediate profile picker. On failure, re-render the form with
  a generic error message and a 200 status (so the form is
  re-submittable).
- ``POST /logout`` — clear the entire session and redirect to
  ``/login``. Using POST (rather than GET) for logout prevents
  prefetchers and link-preview bots from logging the user out.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from omaha.auth import DbSession, get_current_user, verify_password
from omaha.models import Profile, User

router = APIRouter(tags=["auth"])


def _templates(request: Request) -> Jinja2Templates:
    """Return the application-wide Jinja2 templates instance.

    Bound to :attr:`app.state.templates` in :mod:`omaha.main` so a
    single :class:`~fastapi.templating.Jinja2Templates` object is
    shared across every request.
    """
    return request.app.state.templates


@router.get("/login", response_class=HTMLResponse, response_model=None)
def login_form(
    request: Request,
    db: DbSession,
) -> Response:
    """Render the login form, or redirect to ``/`` if already logged in."""
    if get_current_user(request, db) is not None:
        return RedirectResponse("/", status_code=303)
    return _templates(request).TemplateResponse(
        request,
        "login.html",
        {"error": None, "username": ""},
    )


@router.post("/login", response_class=HTMLResponse, response_model=None)
def login_submit(
    request: Request,
    db: DbSession,
    username: str = Form(""),
    password: str = Form(""),
) -> Response:
    """Verify credentials, bind the landing profile, redirect to ``/``.

    On success the session gets both ``user_id`` and
    ``active_profile_id`` (the logged-in user's own first profile by
    ``display_order``). Any prior ``active_profile_id`` in the session
    is replaced — a re-login never inherits a stale binding from the
    previous account.
    """
    user = db.query(User).filter_by(username=username.strip()).first()
    if user is None or not verify_password(password, user.password_hash):
        # Re-render the form with a generic error. Using a single
        # message ("invalid credentials") avoids leaking whether the
        # username exists.
        return _templates(request).TemplateResponse(
            request,
            "login.html",
            {
                "error": "Usuário ou senha inválidos.",
                "username": username,
            },
            status_code=200,
        )

    request.session["user_id"] = user.id
    # Bind the landing profile: the logged-in user's own first
    # profile by display_order. user_id (not username/name) is the
    # stable key — survives profile renames. Profile.user_id is
    # ordered by display_order via the relationship default.
    landing = (
        db.query(Profile).filter(Profile.user_id == user.id).order_by(Profile.display_order).first()
    )
    if landing is not None:
        request.session["active_profile_id"] = landing.id
    else:
        # No profile for this user (shouldn't happen post-seed —
        # the seed creates one profile per user). Fall through to
        # the dashboard; GET / will redirect to /login if it can't
        # resolve a profile.
        request.session.pop("active_profile_id", None)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    """Clear the session and redirect to the login form."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


__all__ = ["router"]
