"""Protected pages: dashboard, profile selection.

Routing contract
----------------
- ``GET /`` — requires a logged-in user. If no profile resolves
  (``active_profile_id`` missing, deleted, or pointing to another
  user's profile), clear the stale key and redirect to ``/login`` so
  the user can re-authenticate and land on their own dashboard.
  Otherwise render the dashboard for the active profile.
- ``POST /profiles/{profile_id}/select`` — requires a logged-in user
  but accepts ANY profile id (any user can view any profile — the
  prior ``profile.user_id != user.id`` 404 check is gone). Sets
  ``active_profile_id`` in the session and redirects to ``/``.

The header chip (base.html) drives the select endpoint via a native
``<select>``: when the operator picks a different profile, the form's
``action`` is rewritten client-side to ``/profiles/{value}/select``
and the form submits.

The dashboard template inherits a Jinja context that always carries
``profiles`` (every profile in the DB, in ``display_order`` order),
``viewer`` (the logged-in ``User``), and ``owner`` (the active
``Profile``) so the header chip + viewer label can render without
any extra round-trip per route.
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


def _common_context(request: Request, db: DbSession, user: User, owner: Profile | None) -> dict[str, Any]:
    """Build the shared Jinja context for authenticated renders.

    Every authenticated template (the dashboard, and any future page
    that extends ``base.html``) gets the same trio of variables:

    * ``profiles`` — every ``Profile`` row in the DB, in
      ``display_order`` ascending. Powers the header chip's
      ``<select>`` options.
    * ``viewer`` — the logged-in :class:`User`. The header renders a
      muted label with ``viewer.username`` when viewer ≠ owner.
    * ``owner`` — the active :class:`Profile` (``active_profile_id``
      resolved to a row), or ``None`` if no profile is active. The
      chip marks this profile as ``selected`` (the browser renders
      the active row with its own selection state; no extra glyph
      needed).
    """
    all_profiles = db.query(Profile).order_by(Profile.display_order).all()
    return {
        "user": user,
        "viewer": user,
        "owner": owner,
        "profile": owner,  # legacy alias — some templates still read `profile`
        "profiles": all_profiles,
    }


@router.get("/", response_class=HTMLResponse, response_model=None)
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the dashboard for the active profile.

    Stale ``active_profile_id`` (missing / deleted / pointing to
    another user's profile) is cleared and the user is bounced to
    ``/login`` — the post-login route binds a fresh landing profile,
    so re-logging-in is the recovery path. There is no
    intermediate picker page; the change is direct landing.
    """
    profile = get_active_profile(request, db)
    if profile is None:
        # Either no profile was ever picked, the cookie is stale
        # (profile deleted, profile belongs to a different user),
        # or the user has yet to log in. Clear the stale key so the
        # next /login → POST flow starts clean.
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)

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
    context = _common_context(request, db, user, profile)
    context.update(
        {
            "asset_classes": asset_classes,
            "portfolio": aggregates["portfolio"],
            "class_aggregates": aggregates["classes"],
        }
    )
    return _templates(request).TemplateResponse(request, "dashboard.html", context)


@router.post("/profiles/{profile_id}/select")
def select_profile(
    profile_id: int,
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> RedirectResponse:
    """Bind ``active_profile_id`` to the session and redirect to the dashboard.

    The prior per-user ownership check
    (``profile.user_id != user.id`` → 404) is gone: any logged-in
    user can switch to any profile. The viewer-vs-owner distinction
    is still rendered in the header (muted label), but it no longer
    gates access. A non-existent id still 404s so a hand-crafted
    POST never silently no-ops.
    """
    profile = db.get(Profile, profile_id)
    if profile is None:
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
      ``assets`` with their ``qty``, ``current_value``, and the four
      percentages the M002 dashboard renders: ``target_pct_class``
      (the stored :attr:`Asset.target_pct`), ``current_pct_class``
      (the asset's share of its class's ``current_value`` — same
      as ``asset_pct``), ``target_pct_total``
      (``target_pct_class * class.target_pct / 100``), and
      ``current_pct_total`` (the asset's share of the portfolio's
      ``current_value``, 0.0 when the portfolio is empty).

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
            # ``target_pct_total`` only depends on the asset's stored
            # target_pct and the class's stored target_pct, both of
            # which are constant for the request — compute it now
            # alongside the per-row dict so the second pass doesn't
            # have to re-walk the loop. The Alpine inline editor in
            # the dashboard template uses this field as the
            # ``target % total`` column.
            target_pct_total = (asset.target_pct or ZERO) * (klass.target_pct or ZERO) / HUNDRED
            asset_rows.append(
                {
                    "id": asset.id,
                    "name": asset.name,
                    "position_count": len(asset.positions),
                    "qty": asset_qty,
                    "invested": asset_invested,
                    "current_value": asset_current,
                    "target_pct_class": asset.target_pct or ZERO,
                    "target_pct_total": target_pct_total,
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
                # ``current_pct_class`` mirrors ``asset_pct`` (the
                # share of the class's current_value) — when the
                # class has no current_value, both are 0.
                asset["current_pct_class"] = ZERO
                # ``current_pct_total`` is the share of the
                # portfolio's current_value — 0 when the portfolio
                # is empty (matches the S05 "empty bars" rule).
                asset["current_pct_total"] = ZERO
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
                # ``asset_pct`` (legacy S05 field) and
                # ``current_pct_class`` (M002 S01/T03 field) carry
                # the same value: the asset's share of its class's
                # current_value. The M002 dashboard renders
                # ``current_pct_class`` in the 4-cell grid; the S05
                # test ``test_aggregates_per_asset_pct_is_share_of_class``
                # still asserts ``asset_pct`` so we keep both in
                # sync. ``current_pct_total`` is the share of the
                # whole portfolio.
                asset_pct = (
                    (asset["current_value"] / class_current) * HUNDRED
                    if class_current > ZERO
                    else ZERO
                )
                asset["asset_pct"] = asset_pct
                asset["current_pct_class"] = asset_pct
                asset["current_pct_total"] = (
                    (asset["current_value"] / portfolio_current) * HUNDRED
                    if portfolio_current > ZERO
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
