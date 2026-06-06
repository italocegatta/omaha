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
  ``user_id`` in the session and *clear* ``active_profile_id`` so the
  user is forced to pick a profile. On failure, re-render the form
  with a generic error message and a 200 status (so the form is
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
from omaha.models import User

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
    """Verify credentials, set the session, redirect to ``/profiles``."""
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
    # Force a fresh profile pick on every login so a user can switch
    # profiles by logging out and back in, even if their previous
    # session still has an active_profile_id.
    request.session.pop("active_profile_id", None)
    return RedirectResponse("/profiles", status_code=303)


@router.post("/logout")
def logout(request: Request) -> RedirectResponse:
    """Clear the session and redirect to the login form."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


__all__ = ["router"]
