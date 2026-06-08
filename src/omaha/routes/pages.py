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

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import selectinload

from omaha.auth import DbSession, get_active_profile, require_user
from omaha.models import Asset, AssetClass, Profile, User

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
        .options(
            selectinload(AssetClass.assets).selectinload(Asset.positions),
        )
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )
    aggregates = portfolio_aggregates(asset_classes)
    return _templates(request).TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "profile": profile,
            "asset_classes": asset_classes,
            "portfolio": aggregates["portfolio"],
            "class_aggregates": aggregates["classes"],
        },
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


__all__ = ["router", "portfolio_aggregates"]


# Eight visually-distinct hex colors assigned to classes in
# insertion order (class index in the loop, not the DB id, so
# reordering via display_order reshuffles colors predictably). More
# than 8 classes wraps around. AssetClass has no ``color`` column;
# this is the dashboard's deterministic-per-position palette.
_CLASS_COLORS: tuple[str, ...] = (
    "#0a66c2",  # blue
    "#2e7d32",  # green
    "#c62828",  # red
    "#ef6c00",  # orange
    "#6a1b9a",  # purple
    "#00838f",  # teal
    "#5d4037",  # brown
    "#455a64",  # slate
)


def portfolio_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]:
    """Compute portfolio-level + per-class + per-asset aggregates for the dashboard.

    Pure function — operates on already-loaded ORM objects. The caller
    is responsible for eager-loading ``AssetClass.assets[*].positions``
    (the dashboard route uses ``selectinload`` to avoid N+1).

    Returns a dict with two top-level keys:

    * ``portfolio``: portfolio-wide ``total_invested``, ``current_value``,
      ``gain``, and ``gain_pct`` (``None`` when ``total_invested == 0``
      so the template can render a neutral dash).
    * ``classes``: list of per-class dicts in the same order as
      ``asset_classes``. Each dict carries ``id``, ``name``,
      ``target_pct``, a deterministic ``color`` hex string from the
      module-level palette, the class's own ``invested`` /
      ``current_value``, the class's ``current_pct`` of the whole
      portfolio (0.0 when the portfolio is empty), and the list of
      ``assets`` with their ``qty``, ``current_value``, and
      ``asset_pct`` (share of the *class's* current_value, 0.0 when
      the class is empty).

    All percentages are stored as ``Decimal`` values in the 0-100
    range so the template can format them with Jinja's ``|round(2)``.
    """
    ZERO = Decimal("0")
    HUNDRED = Decimal("100")

    # First pass: per-asset totals and per-class totals, in one walk.
    class_rows: list[dict[str, Any]] = []
    portfolio_invested = ZERO
    portfolio_current = ZERO

    for index, klass in enumerate(asset_classes):
        class_invested = ZERO
        class_current = ZERO
        asset_rows: list[dict[str, Any]] = []
        for asset in klass.assets:
            asset_invested = ZERO
            asset_current = ZERO
            asset_qty = ZERO
            for pos in asset.positions:
                qty = pos.qty or ZERO
                avg = pos.avg_price or ZERO
                cur = pos.current_price or ZERO
                asset_qty += qty
                asset_invested += qty * avg
                asset_current += qty * cur
            class_invested += asset_invested
            class_current += asset_current
            asset_rows.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "position_count": len(asset.positions),
                    "qty": asset_qty,
                    "invested": asset_invested,
                    "current_value": asset_current,
                }
            )
        portfolio_invested += class_invested
        portfolio_current += class_current
        class_rows.append(
            {
                "id": klass.id,
                "name": klass.name,
                "target_pct": klass.target_pct,
                "color": _CLASS_COLORS[index % len(_CLASS_COLORS)],
                "invested": class_invested,
                "current_value": class_current,
                "_assets": asset_rows,
            }
        )

    portfolio_gain = portfolio_current - portfolio_invested
    if portfolio_invested == ZERO:
        # Empty portfolio: surface a neutral None for gain_pct so the
        # template renders a dash, and force current_pcts to 0.0 so
        # the progress bars are empty (not 100% from div-by-zero).
        portfolio_gain_pct: Decimal | None = None
        for row in class_rows:
            row["current_pct"] = ZERO
            for asset in row["_assets"]:
                asset["asset_pct"] = ZERO
    else:
        portfolio_gain_pct = (portfolio_gain / portfolio_invested) * HUNDRED
        for row in class_rows:
            row["current_pct"] = (
                (row["current_value"] / portfolio_current) * HUNDRED
                if portfolio_current > ZERO
                else ZERO
            )
            class_current = row["current_value"]
            for asset in row["_assets"]:
                asset["asset_pct"] = (
                    (asset["current_value"] / class_current) * HUNDRED
                    if class_current > ZERO
                    else ZERO
                )

    # Flatten: drop the temporary ``_assets`` underscore and move
    # ``assets`` to the final position, in the order expected by the
    # template.
    classes_out: list[dict[str, Any]] = []
    for row in class_rows:
        assets = row.pop("_assets")
        row["assets"] = assets
        classes_out.append(row)

    return {
        "portfolio": {
            "total_invested": portfolio_invested,
            "current_value": portfolio_current,
            "gain": portfolio_gain,
            "gain_pct": portfolio_gain_pct,
        },
        "classes": classes_out,
    }
