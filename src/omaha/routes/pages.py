"""Protected pages: dashboard, profile picker, profile selection.

Routing contract
----------------
- ``GET /`` — requires a logged-in user. If no profile is active,
  redirect to ``/profiles`` (the picker). If a stale ``active_profile_id``
  is in the session (profile was deleted, or belongs to a different
  user), clear it and redirect to ``/profiles`` so the user can pick a
  valid one. Otherwise render the dashboard for the active profile.
- ``GET /profiles`` — requires a logged-in user. Lists the user's
  profiles as form buttons.
- ``POST /profiles/{profile_id}/select`` — requires a logged-in user
  *and* that the profile belongs to the current user. Sets
  ``active_profile_id`` in the session and redirects to ``/``.

The dashboard and profile picker templates are intentionally
placeholder Jinja in T03 (no styling, no Alpine). T04 replaces them
with the production HTML + Alpine.js + static CSS; the route
contracts here don't change.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from omaha.auth import DbSession, get_active_profile, require_user
from omaha.models import AssetClass, Profile, User

router = APIRouter(tags=["pages"])


def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse, response_model=None)
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the dashboard for the active profile, or redirect to the picker."""
    profile = get_active_profile(request, db)
    if profile is None:
        # Either no profile was ever picked, or the cookie is stale
        # (profile deleted, profile belongs to a different user). Drop
        # the stale key so the next /profiles visit starts clean.
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/profiles", status_code=303)

    asset_classes = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )
    return _templates(request).TemplateResponse(
        request,
        "dashboard.html",
        {"user": user, "profile": profile, "asset_classes": asset_classes},
    )


@router.get("/profiles", response_class=HTMLResponse, response_model=None)
def profiles_list(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """List the user's profiles as form buttons for the picker page."""
    # ``user.profiles`` is configured with
    # ``order_by="Profile.display_order"`` in the model, so iteration
    # is already in the right order.
    profiles = list(user.profiles)
    return _templates(request).TemplateResponse(
        request,
        "profiles.html",
        {"user": user, "profiles": profiles},
    )


@router.post("/profiles/{profile_id}/select")
def select_profile(
    profile_id: int,
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> RedirectResponse:
    """Bind ``active_profile_id`` to the session and redirect to the dashboard."""
    profile = db.get(Profile, profile_id)
    if profile is None or profile.user_id != user.id:
        # Don't leak which case it was — a non-existent profile and
        # a profile belonging to someone else look the same to the
        # caller.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    request.session["active_profile_id"] = profile.id
    return RedirectResponse("/", status_code=303)


__all__ = ["router"]
