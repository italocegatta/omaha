"""Protected pages: dashboard, profile selection, rebalance.

Routing contract
----------------
- ``GET /`` — requires a logged-in user. If no profile resolves
  (``active_profile_id`` missing, deleted, or pointing to another
  user's profile), clear the stale key and redirect to ``/login`` so
  the user can re-authenticate and land on their own dashboard.
  Otherwise render the patrimonio page for the active profile.
  Mirrors ``GET /patrimonio`` byte-for-byte (root is the historical
  URL the app has shipped with since direct-landing; ``/patrimonio``
  is the F02 canonical URL going forward — see PRD §5.3 rewritten
  in F02).
- ``GET /patrimonio`` — canonical dashboard URL (F02, D1). Same
  render path as ``GET /``.
- ``POST /profiles/{profile_id}/select`` — requires a logged-in user
  but accepts ANY profile id (any user can view any profile — the
  prior ``profile.user_id != user.id`` 404 check is gone). Sets
  ``active_profile_id`` in the session and redirects to ``/``.
- ``GET /rebalanceamento`` — requires a logged-in user with an active
  profile. Renders the empty placeholder for the rebalance page
  (``rebalance.html``). When the active profile has zero classes, the
  main area renders the empty-state card; the in-body form is
  present but inert (form fields carry the ``disabled`` attribute).
  See ``rebalance.html`` for the layout.
- ``POST /rebalanceamento`` — same auth gate. Reads ``contribution``
  from the in-body form, runs ``rebalance.glue.run_rebalance``, and
  re-renders ``rebalance.html`` with the resulting plan in context.
  No JSON wire trip — the page is server-side rendered, the same
  URL is reused (no PRG redirect). Solver validation failures
  (``RebalanceValidationError``) re-render the page with an inline
  ``form_error``; the route never returns 400 for that case.
- ``GET /rentabilidade`` — stub page rendering "Em construção" body
  text (F02, D6). F03 replaces the stub with the real content.
- ``GET /proventos`` — stub page rendering "Em construção" body text
  (F02, D6). F04 replaces the stub with the real content.

Legacy routes (F02, breaking)
------------------------------
- ``GET /dashboard`` — returns HTTP 404. No alias, no redirect. Same
  for ``GET /rebalance``. Owner decision (D1 / D9): keep the break
  visible; e2e suite asserts the 404 explicitly.

The header chip (base.html) drives the select endpoint via a native
``<select>``: when the operator picks a different profile, the form's
``action`` is rewritten client-side to ``/profiles/{value}/select``
and the form submits. The top nav (F02, D2) drives the
``/patrimonio`` / ``/rebalanceamento`` / ``/rentabilidade`` /
``/proventos`` destinations server-side from ``request.url.path``.

The patrimonio template inherits a Jinja context that always carries
``profiles`` (every profile in the DB, in ``display_order`` order),
``viewer`` (the logged-in ``User``), and ``owner`` (the active
``Profile``) so the header chip + viewer label can render without
any extra round-trip per route. The rebalance page extends that
context with ``plan`` (the ``RebalancePlanResponse`` or ``None``),
``zero_classes`` (bool), and ``form_inert`` (bool — the form is
disabled when the profile has zero classes).
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import selectinload

from omaha.auth import DbSession, get_active_profile, require_profile_writable, require_user
from omaha.models import Asset, AssetClass, Profile, User
from omaha.rebalance.glue import run_rebalance
from omaha.rebalance.models import RebalanceValidationError
from omaha.rebalance.schemas import (
    DEFAULT_MIN_DEVIATION_PCT,
    DEFAULT_MIN_DEVIATION_VALUE,
    RebalancePlanResponse,
)

router = APIRouter(tags=["pages"])

_REBALANCE_SESSION_KEY = "rebalance_contributions"


def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


def _all_family_profiles(db: DbSession) -> list[Profile]:
    """Return every :class:`Profile` row in the database (F06 helper).

    F06 — the family aggregate is cross-User. The toggle visibility
    condition is therefore "the database contains ≥2 profiles",
    independent of which operator is logged in. The helper
    excludes any sentinel ``Profile.name == "system"`` row so a
    future system profile does not inflate the count.

    F07 — Família (the cross-User aggregate) is now a real Profile
    row with ``is_family_sentinel=True``. ``_all_family_profiles``
    still returns every row (sentinel included) so the
    profile-switcher renders Família as a peer; use
    :func:`_real_profiles` to get only the per-User portfolios.
    """
    return db.query(Profile).filter(Profile.name != "system").order_by(Profile.display_order).all()


def _real_profiles(db: DbSession) -> list[Profile]:
    """Return every real (non-sentinel) :class:`Profile` row.

    F07 — the Família sentinel (``is_family_sentinel=True``) lives
    in the same table as the per-User profiles; queries that need
    "per-User portfolios only" must filter it out so:

    * the profile-switcher renders the sentinel as a peer but the
      rest of the system never iterates the sentinel as if it were
      a portfolio,
    * the asset-class / position aggregations stay cross-User via
      :func:`family_asset_classes` (which deliberately walks every
      row) — the "real" helper is for UI / per-User flows only.
    """
    return (
        db.query(Profile)
        .filter(Profile.is_family_sentinel.is_(False))
        .order_by(Profile.display_order)
        .all()
    )


def _common_context(
    request: Request, db: DbSession, user: User, owner: Profile | None
) -> dict[str, Any]:
    """Build the shared Jinja context for authenticated renders.

    Every authenticated template (the patrimonio page, the rebalance
    page, the rentabilidade/proventos stubs, any future page that
    extends ``base.html``) gets the same trio of variables plus the
    F07 split:

    * ``profiles`` — every ``Profile`` row in the DB, in
      ``display_order`` ascending. Powers the header chip's
      ``<select>`` options (sentinel included — used by
      templates that need the full list, e.g. the legacy
      ``profile-switcher``).
    * ``real_profiles`` — F07 — only the per-User profiles
      (``is_family_sentinel=False``). Used by the profile-switcher
      template to render real options in display_order before the
      Família sentinel.
    * ``familia_sentinel`` — F07 — the Família sentinel Profile
      row, or ``None`` when missing (legacy databases pre-F07).
      ``base.html`` uses this to render the Família option as a
      peer of the real profiles inside an ``<optgroup>``.
    * ``viewer`` — the logged-in :class:`User`. The header renders a
      muted label with ``viewer.username`` when viewer ≠ owner.
    * ``owner`` — the active :class:`Profile`` (``active_profile_id``
      resolved to a row), or ``None`` if no profile is active or if
      the Família sentinel is bound. The chip marks this profile as
      ``selected`` (the browser renders the active row with its
      own selection state; no extra glyph needed). When the
      sentinel is bound, ``owner`` is ``None`` (the
      :func:`omaha.auth.get_active_profile` helper short-circuits)
      and the Família option is the selected one.
    """
    all_profiles = _all_family_profiles(db)
    real = _real_profiles(db)
    familia_sentinel: Profile | None = None
    for profile in all_profiles:
        if profile.is_family_sentinel:
            familia_sentinel = profile
            break
    is_household_view = request.query_params.get("view") == "household"
    return {
        "user": user,
        "viewer": user,
        "owner": owner,
        "profile": owner,  # legacy alias — some templates still read `profile`
        "profiles": all_profiles,
        "real_profiles": real,
        "familia_sentinel": familia_sentinel,
        # F06 legacy flags — kept for backward compat with templates
        # that still key on them (the chip switcher no longer reads
        # them). ``family_aggregate_visible`` is always True post-F07
        # when the sentinel exists; the sentinel itself is the chip
        # affordance, not a separate toggle.
        "family_aggregate_visible": familia_sentinel is not None,
        "viewer_owns_multiple_profiles": len(real) >= 2,
        # F06: legacy querystring flag, kept for templates that
        # still render the toggle alias. F07 removes the toggle
        # itself; the querystring continues to drive the family
        # view as a deep-link entry point.
        "is_household_view": is_household_view,
    }


def _render_patrimonio(
    request: Request,
    db: DbSession,
    user: User,
    profile: Profile | None,
    *,
    view: str = "profile",
) -> Response:
    """Render the patrimonio page (the dashboard, post-F02).

    Centralised so ``GET /`` and ``GET /patrimonio`` share the same
    render path (the old ``/`` route continues to work because the
    app has shipped with it since direct-landing; ``/patrimonio``
    is the F02 canonical URL — see roadmap §F02, D1 + D8).

    ``view`` switches between the per-profile default and the
    family aggregate (F01 — ``?view=household`` querystring; F07 —
    Família sentinel bound via the profile-switcher). Family mode
    is read-only: mutation buttons are hidden in the template and
    the dep :func:`require_profile_writable` raises 409 on any
    POST/PATCH/DELETE to a mutation endpoint while the session flag
    is set.

    ``profile`` is the per-User active profile, or ``None`` when
    the operator selected the Família sentinel. The sentinel path
    is family-only — callers detect it via
    :func:`_resolve_view_mode` and pass ``view="family"`` with a
    ``None`` profile. The :func:`omaha.auth.get_active_profile`
    helper also short-circuits the sentinel to ``None``; the routes
    re-resolve it from the session id so the helper's contract
    stays clean.
    """
    if view == "family":
        asset_classes = family_asset_classes(db)
        aggregates = family_aggregates(asset_classes)
        read_only = True
    else:
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
        read_only = False
    context = _common_context(request, db, user, profile)
    context.update(
        {
            "view": view,
            "read_only": read_only,
            "asset_classes": asset_classes,
            "portfolio": aggregates["portfolio"],
            "class_aggregates": aggregates["classes"],
        }
    )
    return _templates(request).TemplateResponse(request, "patrimonio.html", context)


def _resolve_view_mode(request: Request, db: DbSession, owner: Profile | None) -> str:
    """Resolve the family read-only flag from querystring OR sentinel.

    F01 Decision 1 — querystring is the canonical signal. The
    caller is responsible for also binding the value into
    ``request.session["view_mode"]`` so the
    :func:`require_profile_writable` dependency can gate mutations
    on the same flag (mutations don't carry the querystring).

    F06 — the URL keeps the historical ``?view=household`` shape
    (D-F06.4) but the internal context value is now ``"family"``
    (D-F06.5) to match the renamed family aggregate.

    F07 — Família is selectable via the profile-switcher (peer of
    real profiles). When the operator selects the sentinel row,
    ``active_profile_id`` points to the sentinel; the caller's
    :func:`omaha.auth.get_active_profile` returns ``None`` for
    sentinel rows, so we resolve the sentinel directly here (via
    the bound session id) and return ``"family"`` whenever either
    the querystring OR the sentinel match fires. Any other value
    falls back to ``"profile"`` so a typo or a stale client cannot
    accidentally toggle the read-only mode.
    """
    if request.query_params.get("view") == "household":
        return "family"
    sentinel_id = request.session.get("active_profile_id")
    if sentinel_id is not None:
        sentinel = db.get(Profile, sentinel_id)
        if sentinel is not None and sentinel.is_family_sentinel:
            return "family"
    return "profile"


def _resolve_patrimonio_target(request: Request, db: DbSession) -> Profile | None:
    """Resolve the active profile for the patrimonio / rebalance pages.

    Returns the active :class:`Profile` or ``None`` when the session
    has no resolvable active_profile_id (no user, no profile, or
    pointing at a deleted profile). Callers use the ``None`` signal
    to redirect to ``/login`` — except the patrimonio routes, which
    distinguish the Família sentinel case via
    :func:`_resolve_view_mode` and render the family aggregate
    instead.
    """
    return get_active_profile(request, db)


def _sentinel_redirect(request: Request, db: DbSession) -> RedirectResponse | None:
    """Return a redirect to the family-aggregate patrimonio when sentinel is bound.

    F07 — Família (the ``is_family_sentinel`` profile) has no
    ``AssetClass`` rows, so the non-patrimonio pages (rebalance,
    rentabilidade, proventos) cannot render meaningful per-profile
    content while the sentinel is active. Routes call this helper
    first; if it returns a :class:`RedirectResponse` the route
    short-circuits and bounces the operator to the canonical
    family-view entry point. Returns ``None`` when the sentinel
    is NOT active so the route can continue with the normal
    per-profile flow.
    """
    profile_id = request.session.get("active_profile_id")
    if profile_id is None:
        return None
    profile = db.get(Profile, profile_id)
    if profile is None or not profile.is_family_sentinel:
        return None
    request.session["view_mode"] = "family"
    return RedirectResponse("/patrimonio?view=household", status_code=303)


@router.get("/", response_class=HTMLResponse, response_model=None)
def index(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the patrimonio page for the active profile.

    ``/`` is the historical dashboard URL the app has shipped with
    since direct-landing. ``/patrimonio`` (F02, D1) is the new
    canonical URL; both routes render the same template with the
    same data. Stale ``active_profile_id`` (missing / deleted /
    pointing at another user's profile) is cleared and the user is
    bounced to ``/login`` — the post-login route binds a fresh
    landing profile, so re-logging-in is the recovery path.

    F07 — when the bound ``active_profile_id`` is the Família
    sentinel (the operator picked Família via the
    profile-switcher), ``get_active_profile`` short-circuits to
    ``None`` and :func:`_resolve_view_mode` returns ``"family"``
    (querystring-free entry point — D-F07.1). The page renders the
    family aggregate directly, with no redirect and no querystring.
    """
    profile = _resolve_patrimonio_target(request, db)
    view = _resolve_view_mode(request, db, profile)
    if profile is None and view != "family":
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)
    if view == "family":
        request.session["view_mode"] = "family"
    else:
        request.session.pop("view_mode", None)
    return _render_patrimonio(request, db, user, profile, view=view)


@router.get("/patrimonio", response_class=HTMLResponse, response_model=None)
def get_patrimonio(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the patrimonio page (F02 canonical URL).

    Same render path as ``GET /`` (see :func:`index`). The two URLs
    are aliased for backward compat (the app shipped with ``/`` as
    the dashboard URL since direct-landing; F02 introduces
    ``/patrimonio`` as the canonical URL — F02 D1 + D8 + D9). No
    HTTP redirect: the active-tab detection in ``base.html`` reads
    ``request.url.path`` and lights up the matching tab on either
    URL (``/`` highlights "Patrimônio").

    F07 — same sentinel handling as :func:`index` — Família
    activates the family aggregate via the bound sentinel id, no
    querystring needed.
    """
    profile = _resolve_patrimonio_target(request, db)
    view = _resolve_view_mode(request, db, profile)
    if profile is None and view != "family":
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)
    if view == "family":
        request.session["view_mode"] = "family"
    else:
        request.session.pop("view_mode", None)
    return _render_patrimonio(request, db, user, profile, view=view)


@router.get("/dashboard")
def get_legacy_dashboard() -> Response:
    """Legacy dashboard URL — returns HTTP 404 (F02 breaking change).

    The owner decided (D1) that ``/dashboard`` would not be aliased
    to ``/patrimonio``: any redirect would hide the breakage from
    e2e tests and surprise users with silent URL changes. Requests
    to ``/dashboard`` return 404 so the break is explicit. See F02
    decision D1 + D9.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


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

    F07 — when the operator selects the Família sentinel via the
    profile-switcher, the helper binds the sentinel id AND flips
    the session ``view_mode`` flag to ``"family"`` so the
    :func:`require_profile_writable` dep gates mutations on the
    same signal (the JSON POST from the select form does not
    carry the ``?view=household`` querystring). The redirect keeps
    the legacy querystring on the URL so the deep-link contract
    ``?view=household`` remains valid (D-F07.2 — the URL is the
    canonical family-view wire shape; the chip is the new entry
    point).
    """
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    request.session["active_profile_id"] = profile.id
    if profile.is_family_sentinel:
        request.session["view_mode"] = "family"
        return RedirectResponse("/patrimonio?view=household", status_code=303)
    request.session.pop("view_mode", None)
    return RedirectResponse("/", status_code=303)


def _load_asset_classes(db: DbSession, profile: Profile) -> list[AssetClass]:
    """Load the active profile's ``AssetClass`` rows (ordered, no nested eager).

    Used by both the patrimonio index and the rebalance page to detect
    the zero-classes state. The patrimonio path still eager-loads
    assets + positions because it needs the per-asset data; the
    rebalance page only needs the row count, so we skip the eager
    load to keep ``GET /rebalanceamento`` cheap.
    """
    return (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )


def _rebalance_contributions(request: Request) -> dict[str, float]:
    """Return normalized per-profile aporte memory from session state."""

    raw = request.session.get(_REBALANCE_SESSION_KEY)
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, float] = {}
    changed = False
    for profile_id, value in raw.items():
        if not isinstance(profile_id, str):
            changed = True
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            changed = True
            continue
        if not math.isfinite(parsed):
            changed = True
            continue
        normalized[profile_id] = parsed
    if changed:
        request.session[_REBALANCE_SESSION_KEY] = normalized
    return normalized


def _get_rebalance_contribution(request: Request, profile: Profile) -> float:
    """Return persisted aporte for profile, defaulting to zero."""

    return _rebalance_contributions(request).get(str(profile.id), 0.0)


def _set_rebalance_contribution(request: Request, profile: Profile, contribution: float) -> None:
    """Persist finite aporte for active profile in session memory."""

    contributions = _rebalance_contributions(request)
    contributions[str(profile.id)] = float(contribution)
    request.session[_REBALANCE_SESSION_KEY] = contributions


def _materialize_rebalance_plan(
    request: Request,
    db: DbSession,
    profile: Profile,
    contribution: float,
    *,
    min_deviation_value: float = DEFAULT_MIN_DEVIATION_VALUE,
    min_deviation_pct: float = DEFAULT_MIN_DEVIATION_PCT,
) -> RebalancePlanResponse:
    """Run rebalance, persisting non-negative aporte used by page UX."""

    plan = run_rebalance(
        db,
        profile,
        contribution,
        min_deviation_value=min_deviation_value,
        min_deviation_pct=min_deviation_pct,
    )
    if contribution >= 0:
        _set_rebalance_contribution(request, profile, contribution)
    return plan


def _parse_non_negative_form_float(
    raw: str | None, *, default: float
) -> tuple[float | None, str | None]:
    if raw is None or raw.strip() == "":
        return default, None
    try:
        parsed = float(raw)
    except ValueError:
        return None, "Valor inválido. Use um número finito."
    if not math.isfinite(parsed):
        return None, "Valor inválido. Use um número finito."
    if parsed < 0:
        return None, "Valor inválido. Use zero ou positivo."
    return parsed, None


def _resolved_threshold(value: float | None, default: float) -> float:
    return default if value is None else value


def _render_rebalance(
    request: Request,
    db: DbSession,
    user: User,
    profile: Profile,
    *,
    plan: RebalancePlanResponse | None = None,
    form_error: str | None = None,
    min_deviation_value: float = DEFAULT_MIN_DEVIATION_VALUE,
    min_deviation_pct: float = DEFAULT_MIN_DEVIATION_PCT,
) -> Response:
    """Build the Jinja context for ``rebalance.html`` and render it.

    Centralises the shared context assembly so GET and POST use the
    same path. ``plan`` is the resolved plan (or ``None`` for the
    initial plan-free render); ``form_error`` is the inline error string
    when the POST hit a validation failure (non-finite contribution
    or solver validation error).

    The plan object passed to Jinja is the Pydantic model itself so
    the template can access typed fields (``plan.metrics.contribution``,
    ``plan.warnings``). The Alpine ``rebalancePage({plan: ...})``
    initializer uses a ``tojson``-serialized dump via the template —
    the template references ``plan`` (the model) for server-side
    rendering and ``plan_dict`` (the dict) for the Alpine store.
    """
    asset_classes = _load_asset_classes(db, profile)
    zero_classes = len(asset_classes) == 0
    context = _common_context(request, db, user, profile)
    context.update(
        {
            "plan": plan,
            "plan_dict": plan.model_dump(mode="json") if plan is not None else None,
            "zero_classes": zero_classes,
            "form_inert": zero_classes,
            "form_error": form_error,
            "min_deviation_value": min_deviation_value,
            "min_deviation_pct": min_deviation_pct,
            "contribution": (
                plan.metrics.contribution
                if plan is not None
                else _get_rebalance_contribution(request, profile)
            ),
        }
    )
    return _templates(request).TemplateResponse(request, "rebalance.html", context)


@router.get("/rebalanceamento", response_class=HTMLResponse, response_model=None)
def get_rebalanceamento(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render rebalance page, materializing plan when profile has classes.

    When the active profile has zero classes, the main area renders
    the empty-state card. Otherwise the route resolves the persisted
    aporte for that profile (or ``0`` when absent), runs rebalance,
    and renders the current plan immediately. The in-body form is
    present in both cases; it is disabled only when the profile has
    zero classes (the operator must create a class first via the
    patrimonio "+ Nova classe" button — see F02 design notes for the
    button migration).

    The previous URL ``/rebalance`` is no longer served — see F02
    D1 + D9. Requests to ``/rebalance`` return HTTP 404 from a sibling
    handler so the breakage is visible.

    F07 — when the Família sentinel is the active profile, the
    rebalance page has no per-profile content to show (sentinel
    owns zero ``AssetClass`` rows); redirect to the canonical
    family-view entry point on the patrimonio dashboard.
    """
    redirect = _sentinel_redirect(request, db)
    if redirect is not None:
        return redirect
    profile = get_active_profile(request, db)
    if profile is None:
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)
    if _load_asset_classes(db, profile):
        try:
            plan = _materialize_rebalance_plan(
                request,
                db,
                profile,
                _get_rebalance_contribution(request, profile),
                min_deviation_value=DEFAULT_MIN_DEVIATION_VALUE,
                min_deviation_pct=DEFAULT_MIN_DEVIATION_PCT,
            )
        except RebalanceValidationError as exc:
            return _render_rebalance(
                request,
                db,
                user,
                profile,
                form_error=str(exc),
            )
        return _render_rebalance(
            request,
            db,
            user,
            profile,
            plan=plan,
            min_deviation_value=DEFAULT_MIN_DEVIATION_VALUE,
            min_deviation_pct=DEFAULT_MIN_DEVIATION_PCT,
        )
    return _render_rebalance(request, db, user, profile)


@router.post("/rebalanceamento", response_class=HTMLResponse, response_model=None)
def post_rebalanceamento(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    _writable: None = Depends(require_profile_writable),
    contribution: str = Form(default=""),
    min_deviation_value: str = Form(default=""),
    min_deviation_pct: str = Form(default=""),
) -> Response:
    """Run the rebalance pipeline and re-render the page with the plan.

    ``contribution`` is bound as a raw string because the wire
    boundary (HTML form) is untyped — we parse it here so a
    malformed value surfaces as ``form_error="Valor inválido..."``
    instead of a 422 (the JSON route owns the 422; the page flow is
    fully render-driven and never produces a 4xx response once the
    user is authenticated).

    Server-side accepts any finite float (positive, zero, negative)
    per the ``rebalance-route`` contract extension; the page itself
    gates ``contribution < 0`` client-side for v1 (withdrawal is a
    Phase 4 feature). Solver validation failures map to
    ``form_error`` with the validation message verbatim — the page
    re-renders, no redirect, no 4xx.

    F07 — Família sentinel: the ``require_profile_writable`` dep
    raises 409 ``household_read_only`` while the family session flag
    is set; the sentinel POST path therefore never reaches the
    rebalance solver.
    """
    profile = get_active_profile(request, db)
    if profile is None:
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)

    if contribution is None or contribution.strip() == "":
        parsed = 0.0
    else:
        try:
            parsed = float(contribution)
        except ValueError:
            return _render_rebalance(
                request,
                db,
                user,
                profile,
                form_error="Valor inválido. Use um número finito.",
            )

    if not math.isfinite(parsed):
        return _render_rebalance(
            request,
            db,
            user,
            profile,
            form_error="Valor inválido. Use um número finito.",
        )

    parsed_min_deviation_value, threshold_error = _parse_non_negative_form_float(
        min_deviation_value,
        default=DEFAULT_MIN_DEVIATION_VALUE,
    )
    if threshold_error is not None:
        return _render_rebalance(
            request,
            db,
            user,
            profile,
            form_error=threshold_error,
            min_deviation_value=DEFAULT_MIN_DEVIATION_VALUE,
            min_deviation_pct=DEFAULT_MIN_DEVIATION_PCT,
        )

    parsed_min_deviation_pct, threshold_error = _parse_non_negative_form_float(
        min_deviation_pct,
        default=DEFAULT_MIN_DEVIATION_PCT,
    )
    if threshold_error is not None:
        return _render_rebalance(
            request,
            db,
            user,
            profile,
            form_error=threshold_error,
            min_deviation_value=_resolved_threshold(
                parsed_min_deviation_value, DEFAULT_MIN_DEVIATION_VALUE
            ),
            min_deviation_pct=DEFAULT_MIN_DEVIATION_PCT,
        )

    try:
        plan = _materialize_rebalance_plan(
            request,
            db,
            profile,
            parsed,
            min_deviation_value=_resolved_threshold(
                parsed_min_deviation_value, DEFAULT_MIN_DEVIATION_VALUE
            ),
            min_deviation_pct=_resolved_threshold(
                parsed_min_deviation_pct, DEFAULT_MIN_DEVIATION_PCT
            ),
        )
    except RebalanceValidationError as exc:
        return _render_rebalance(
            request,
            db,
            user,
            profile,
            form_error=str(exc),
            min_deviation_value=_resolved_threshold(
                parsed_min_deviation_value, DEFAULT_MIN_DEVIATION_VALUE
            ),
            min_deviation_pct=_resolved_threshold(
                parsed_min_deviation_pct, DEFAULT_MIN_DEVIATION_PCT
            ),
        )

    return _render_rebalance(
        request,
        db,
        user,
        profile,
        plan=plan,
        min_deviation_value=_resolved_threshold(
            parsed_min_deviation_value, DEFAULT_MIN_DEVIATION_VALUE
        ),
        min_deviation_pct=_resolved_threshold(parsed_min_deviation_pct, DEFAULT_MIN_DEVIATION_PCT),
    )


@router.get("/rebalance")
def get_legacy_rebalance() -> Response:
    """Legacy rebalance URL — returns HTTP 404 (F02 breaking change).

    Same rationale as :func:`get_legacy_dashboard`. The F02 owner
    decision (D1 + D9) bans aliasing; e2e tests assert the 404
    explicitly so a regression would surface immediately.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/rentabilidade", response_class=HTMLResponse, response_model=None)
def get_rentabilidade(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the ``/rentabilidade`` stub page (F02, D6).

    The page body is a single "Em construção" card (see
    ``rentabilidade.html``); F03 replaces this stub with the real
    content (time series of returns). Stub exists so the F02 top nav
    is complete + clickable end-to-end — see F02 decision D6.

    F07 — Família sentinel: redirect to the family-view patrimonio.
    """
    redirect = _sentinel_redirect(request, db)
    if redirect is not None:
        return redirect
    profile = get_active_profile(request, db)
    if profile is None:
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)
    context = _common_context(request, db, user, profile)
    return _templates(request).TemplateResponse(request, "rentabilidade.html", context)


@router.get("/proventos", response_class=HTMLResponse, response_model=None)
def get_proventos(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
) -> Response:
    """Render the ``/proventos`` stub page (F02, D6).

    Same shape as :func:`get_rentabilidade`. F04 replaces this stub
    with the real content (dividends / JCP per asset, class, profile).

    F07 — Família sentinel: redirect to the family-view patrimonio.
    """
    redirect = _sentinel_redirect(request, db)
    if redirect is not None:
        return redirect
    profile = get_active_profile(request, db)
    if profile is None:
        request.session.pop("active_profile_id", None)
        return RedirectResponse("/login", status_code=303)
    context = _common_context(request, db, user, profile)
    return _templates(request).TemplateResponse(request, "proventos.html", context)


__all__ = [
    "router",
    "portfolio_aggregates",
    "family_aggregates",
    "family_asset_classes",
]


# Eight visually-distinct OKLCH colors assigned to classes in
# insertion order (class index in the loop, not the DB id, so
# reordering via display_order reshuffles colors predictably). More
# than 8 classes wraps around. AssetClass has no ``color`` column;
# this is the patrimonio's deterministic-per-position palette.
#
# F14: Catppuccin Frappe-derived palette. Mirrors --class-1..8 in :root.
_CLASS_COLORS: tuple[str, ...] = (
    "oklch(0.742 0.104 265.7)",  # blue          -- mirrors --class-1
    "oklch(0.765 0.111 311.7)",  # lavender       -- mirrors --class-2
    "oklch(0.783 0.073 184.6)",  # teal           -- mirrors --class-3
    "oklch(0.812 0.107 133.4)",  # green          -- mirrors --class-4
    "oklch(0.844 0.08 83.5)",  # amber          -- mirrors --class-5
    "oklch(0.717 0.124 19.4)",  # red            -- mirrors --class-6
    "oklch(0.65 0.04 274)",  # muted blue-gray -- 7th cycle slot
    "oklch(0.70 0.03 274)",  # slate          -- 8th cycle slot
)

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


def _pct_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    return (numerator / denominator) * _HUNDRED


def _pct_or_none(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= _ZERO:
        return None
    return (numerator / denominator) * _HUNDRED


def _target_value(total: Decimal, pct: Decimal | None) -> Decimal | None:
    if pct is None:
        return None
    return (total * pct) / _HUNDRED


def portfolio_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]:
    """Compute portfolio-level + per-class + per-asset aggregates for the patrimonio.

    Pure function — operates on already-loaded ORM objects. The caller
    is responsible for eager-loading ``AssetClass.assets[*].positions``
    (the patrimonio route uses ``selectinload`` to avoid N+1).

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
      percentages the M002 patrimonio renders: ``target_pct_class``
      (the stored :attr:`Asset.target_pct`), ``current_pct_class``
      (the asset's share of its class's ``current_value`` — same
      as ``asset_pct``), ``target_pct_total``
      (``target_pct_class * class.target_pct / 100``), and
      ``current_pct_total`` (the asset's share of the portfolio's
      ``current_value``, 0.0 when the portfolio is empty).

    All percentages are stored as ``Decimal`` values in the 0-100
    range so the template can format them with Jinja's ``|round(2)``.
    """
    # First pass: per-class totals via the shared helper, in one walk.
    class_rows: list[dict[str, Any]] = []
    portfolio_invested = _ZERO
    portfolio_current = _ZERO

    for index, klass in enumerate(asset_classes):
        # ``_compute_class_totals`` owns the per-asset qty/invested/
        # current summing loop (and the per-asset
        # ``target_pct_total`` calc, which only depends on the asset
        # + class target_pct — both constant for the request). The
        # patrimonio helper just glues the per-class result into the
        # class-level row and computes the class's portfolio share
        # in the second pass.
        totals = _compute_class_totals(klass)
        class_invested = totals["class_invested"]
        class_current = totals["class_current"]
        asset_rows = totals["assets"]
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
    if portfolio_invested == _ZERO:
        # Empty portfolio: surface a neutral None for gain_pct so the
        # template renders a dash, and force current_pcts to 0.0 so
        # the progress bars are empty (not 100% from div-by-zero).
        portfolio_gain_pct: Decimal | None = None
        for row in class_rows:
            row["current_pct"] = _ZERO
            for asset in row["_assets"]:
                asset["asset_pct"] = _ZERO
                # ``current_pct_class`` mirrors ``asset_pct`` (the
                # share of the class's current_value) — when the
                # class has no current_value, both are 0.
                asset["current_pct_class"] = _ZERO
                # ``current_pct_total`` is the share of the
                # portfolio's current_value — 0 when the portfolio
                # is empty (matches the S05 "empty bars" rule).
                asset["current_pct_total"] = _ZERO
    else:
        portfolio_gain_pct = (portfolio_gain / portfolio_invested) * _HUNDRED
        for row in class_rows:
            row["current_pct"] = _pct_or_zero(row["current_value"], portfolio_current)
            class_current = row["current_value"]
            for asset in row["_assets"]:
                # ``asset_pct`` (legacy S05 field) and
                # ``current_pct_class`` (M002 S01/T03 field) carry
                # the same value: the asset's share of its class's
                # current_value. The M002 patrimonio renders
                # ``current_pct_class`` in the 4-cell grid; the S05
                # test ``test_aggregates_per_asset_pct_is_share_of_class``
                # still asserts ``asset_pct`` so we keep both in
                # sync. ``current_pct_total`` is the share of the
                # whole portfolio.
                asset_pct = _pct_or_zero(asset["current_value"], class_current)
                asset["asset_pct"] = asset_pct
                asset["current_pct_class"] = asset_pct
                asset["current_pct_total"] = _pct_or_zero(asset["current_value"], portfolio_current)

    for row in class_rows:
        row["gain_value"] = row["current_value"] - row["invested"]
        row["gain_pct"] = _pct_or_none(row["gain_value"], row["invested"])
        row["class_current_pct_class"] = _HUNDRED if row["current_value"] > _ZERO else _ZERO
        row["class_target_pct_class"] = _HUNDRED if row["current_value"] > _ZERO else _ZERO
        row["class_deviation_pct_class"] = (
            row["class_current_pct_class"] - row["class_target_pct_class"]
        )
        row["portfolio_target_pct"] = row["target_pct"] or _ZERO
        row["portfolio_deviation_pct"] = row["current_pct"] - row["portfolio_target_pct"]
        row["position_target_value"] = _target_value(portfolio_current, row["portfolio_target_pct"])
        row["position_deviation_value"] = (
            row["current_value"] - row["position_target_value"]
            if row["position_target_value"] is not None
            else None
        )
        for asset in row["_assets"]:
            asset["class_deviation_pct"] = asset["current_pct_class"] - asset["target_pct_class"]
            asset["portfolio_target_pct"] = asset["target_pct_total"]
            asset["portfolio_deviation_pct"] = (
                asset["current_pct_total"] - asset["portfolio_target_pct"]
            )
            asset["position_target_value"] = _target_value(
                portfolio_current,
                asset["portfolio_target_pct"],
            )
            asset["position_deviation_value"] = (
                asset["current_value"] - asset["position_target_value"]
                if asset["position_target_value"] is not None
                else None
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


def _compute_class_totals(klass: AssetClass) -> dict[str, Any]:
    """Compute per-asset + per-class totals for a single :class:`AssetClass`.

    Private helper extracted from :func:`portfolio_aggregates` for
    two reasons:

    * ``portfolio_aggregates`` reads cleaner when the inner summing
      loop is named — the outer function only cares about
      class-level roll-ups + percentage calc.
    * ``audit/inventory.py:155`` and the patrimonio tests build
      hand-crafted per-asset dicts to mirror this shape. Keeping the
      single source of truth here means a future column addition
      (e.g. ``current_pct_class`` rename) only changes one place.

    Note: the rebalance builders (:mod:`omaha.rebalance.builders`)
    deliberately do NOT call this helper — they re-implement the
    same Decimal-summing loop against a different schema. See
    ``openspec/changes/rebalance-infra/design.md`` Decision 5:
    ``portfolio_aggregates`` is consumed by the patrimonio, the
    audit pipeline, and three test files; sharing the helper risks
    breaking the audit pipeline silently when the rebalance schema
    evolves.

    Returns a dict with three keys:

    * ``class_invested`` / ``class_current`` — sum of the per-asset
      totals (which themselves sum the broker-published
      ``total_invested`` / ``total_current`` directly — see
      ``broker-csv-import-totals``).
    * ``assets`` — list of per-asset dicts in
      ``klass.assets`` order. Each dict carries the fields the
      patrimonio template and the Alpine inline editor consume
      (``id``, ``name``, ``position_count``, ``qty``, ``invested``,
      ``current_value``, ``target_pct_class``, ``target_pct_total``,
      ``buy_enabled``, ``sell_enabled``, ``currency_code``).
    """
    class_invested = _ZERO
    class_current = _ZERO
    asset_rows: list[dict[str, Any]] = []
    for asset in klass.assets:
        asset_invested = _ZERO
        asset_current = _ZERO
        asset_qty = _ZERO
        for pos in asset.positions:
            qty = pos.qty or _ZERO
            asset_qty += qty
            # broker-csv-import-totals: sum the broker-published
            # per-row totals directly. ``NULL`` (legacy position
            # or CSV that did not publish the column) contributes
            # ``Decimal('0')`` — never recompute ``qty * price``;
            # that arithmetic is the exact drift source this
            # change eliminates.
            asset_invested += pos.total_invested or _ZERO
            asset_current += pos.total_current or _ZERO
        class_invested += asset_invested
        class_current += asset_current
        # ``target_pct_total`` only depends on the asset's stored
        # target_pct and the class's stored target_pct, both of
        # which are constant for the request — compute it now
        # alongside the per-row dict so the second pass doesn't
        # have to re-walk the loop. The Alpine inline editor in
        # the patrimonio template uses this field as the
        # ``target % total`` column.
        target_pct_total = (asset.target_pct or _ZERO) * (klass.target_pct or _ZERO) / _HUNDRED
        gain_value = asset_current - asset_invested
        asset_rows.append(
            {
                "id": asset.id,
                "name": asset.name,
                "position_count": len(asset.positions),
                "qty": asset_qty,
                "avg_price": (asset_invested / asset_qty) if asset_qty > _ZERO else None,
                "invested": asset_invested,
                "current_value": asset_current,
                "gain_value": gain_value,
                "gain_pct": _pct_or_none(gain_value, asset_invested),
                "target_pct_class": asset.target_pct or _ZERO,
                "target_pct_total": target_pct_total,
                # asset-trade-flags: propagate the three per-asset
                # trade-control attributes so the patrimonio's
                # inline toggle UI can render the current state
                # without an extra round-trip per asset row. The
                # template's ``x-data`` initializer copies these
                # into the local Alpine store (``assets``) so a
                # PATCH mutates the in-memory copy and the next
                # render reads the new value without a reload.
                "buy_enabled": asset.buy_enabled,
                "sell_enabled": asset.sell_enabled,
                "currency_code": asset.currency_code,
            }
        )
    return {
        "class_invested": class_invested,
        "class_current": class_current,
        "assets": asset_rows,
    }


def household_asset_classes(db: DbSession, viewer: User) -> list[AssetClass]:
    """DEPRECATED — kept for backward compat only.

    F01 implementation of the intra-User household aggregate.
    Superseded by :func:`family_asset_classes` in F06, which loads
    every :class:`Profile` row in the database (cross-User full-join).
    The F01 variant walked ``viewer.profiles`` and was therefore
    useless in the default seed (Italo and Ana are two separate
    ``User`` rows, so each one only ever saw their own profile).
    New code MUST call :func:`family_asset_classes`; the
    :func:`_render_patrimonio` ``view == 'family'`` branch is the
    single production consumer. Delete in a future R-slice refator.
    """
    profile_ids = [p.id for p in viewer.profiles]
    if not profile_ids:
        return []
    return (
        db.query(AssetClass)
        .options(
            selectinload(AssetClass.assets).selectinload(Asset.positions),
        )
        .filter(AssetClass.profile_id.in_(profile_ids))
        .order_by(AssetClass.profile_id, AssetClass.display_order)
        .all()
    )


def household_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]:
    """DEPRECATED — kept for backward compat only.

    F01 household-mode mirror of :func:`portfolio_aggregates`.
    Superseded by :func:`family_aggregates` in F06. New code MUST
    call :func:`family_aggregates`; the
    :func:`_render_patrimonio` ``view == 'family'`` branch is the
    single production consumer. Delete in a future R-slice refator.
    """
    return portfolio_aggregates(asset_classes)


def family_asset_classes(db: DbSession) -> list[AssetClass]:
    """Load every :class:`AssetClass` row in the database, eager-loaded.

    F06 — family aggregate view (cross-User full-join). The function
    walks **every** ``Profile`` row in the database (system-profile
    sentinel rows, if any, are excluded via ``Profile.name !=
    "system"``) and returns one flat list of :class:`AssetClass`
    rows in ``Profile.display_order`` / ``AssetClass.display_order``
    order so the template can render a single section per class
    without grouping logic.

    The selectinload strategy mirrors :func:`_render_patrimonio`'s
    per-profile path so the family branch keeps the same N+1-safe
    behaviour the original patrimonio already has.

    The function deliberately does NOT take a ``viewer`` parameter:
    ``cross-profile-sharing`` (F06 MODIFIED) requires the family
    aggregate to be identical regardless of which family operator
    is logged in. PRD §1.2 pins the two operators as password-shared,
    so exposing the cross-User aggregate does not leak data to
    third parties. If the product later introduces differentiated
    per-User authentication, a new gate must be reintroduced here.
    """
    return (
        db.query(AssetClass)
        .join(Profile, AssetClass.profile_id == Profile.id)
        .options(
            selectinload(AssetClass.assets).selectinload(Asset.positions),
        )
        .filter(Profile.name != "system")
        .order_by(Profile.display_order, AssetClass.display_order)
        .all()
    )


def _aggregate_classes_by_name(
    asset_classes: list[AssetClass],
) -> list[dict[str, Any]]:
    """Collapse :class:`AssetClass` rows with identical ``name`` (F06 D3).

    Returns a list of class-shaped dicts (same wire shape as
    :func:`_compute_class_totals` consumes) keyed by ``name``. The
    collapse preserves the ``color`` of the **first** occurrence in
    display order, the **minimum** ``display_order``, and sums
    ``class_invested`` / ``class_current`` verbatim per
    ``broker-csv-import-totals``.

    The ``id`` field carries the first occurrence's
    :class:`AssetClass.id` so the per-class CSS palette index
    stays deterministic across renders. ``target_pct`` is forced
    to ``None`` because the F06 invariant collapses classes whose
    per-profile ``target_pct`` may diverge — the template reads
    the flag and hides the ``Alvo`` pill in family mode.
    """
    grouped: dict[str, list[AssetClass]] = {}
    for klass in asset_classes:
        grouped.setdefault(klass.name, []).append(klass)

    rows: list[dict[str, Any]] = []
    for name, members in grouped.items():
        invested = Decimal("0")
        current = Decimal("0")
        for member in members:
            totals = _compute_class_totals(member)
            invested += totals["class_invested"]
            current += totals["class_current"]
        rows.append(
            {
                "id": members[0].id,
                "name": name,
                "target_pct": None,
                "color": _CLASS_COLORS[len(rows) % len(_CLASS_COLORS)],
                "invested": invested,
                "current_value": current,
                "display_order": min(m.display_order for m in members),
                "_members": members,
            }
        )
    return rows


def _aggregate_assets_by_name(classes: list[AssetClass]) -> list[dict[str, Any]]:
    """Collapse :class:`Asset` rows with identical ``name`` across classes.

    F06 D3 — within an aggregated class (already collapsed by
    ``name``), ``Asset`` rows whose ``name`` matches across the
    underlying profiles also collapse into a single asset row.
    Sums ``qty``, ``invested``, ``current_value``, and
    ``position_count`` verbatim per ``broker-csv-import-totals``.
    The first occurrence's ``buy_enabled`` / ``sell_enabled`` /
    ``currency_code`` wins so the row stays deterministic; a
    divergence flag (``flags_divergent``) is included for callers
    that want to surface the ambiguity in copy.
    """
    grouped: dict[str, list[Asset]] = {}
    for klass in classes:
        for asset in klass.assets:
            grouped.setdefault(asset.name, []).append(asset)

    rows: list[dict[str, Any]] = []
    for name, members in grouped.items():
        invested = _ZERO
        current = _ZERO
        qty = _ZERO
        position_count = 0
        for asset in members:
            for pos in asset.positions:
                position_count += 1
                qty += pos.qty or _ZERO
                invested += pos.total_invested or _ZERO
                current += pos.total_current or _ZERO
        buy = members[0].buy_enabled
        sell = members[0].sell_enabled
        any_buy_divergent = any(a.buy_enabled != buy for a in members)
        any_sell_divergent = any(a.sell_enabled != sell for a in members)
        gain_value = current - invested
        rows.append(
            {
                "id": members[0].id,
                "name": name,
                "position_count": position_count,
                "qty": qty,
                "avg_price": (invested / qty) if qty > _ZERO else None,
                "invested": invested,
                "current_value": current,
                "gain_value": gain_value,
                "gain_pct": _pct_or_none(gain_value, invested),
                "target_pct_class": None,
                "target_pct_total": None,
                "buy_enabled": buy,
                "sell_enabled": sell,
                "currency_code": members[0].currency_code,
                "flags_divergent": any_buy_divergent or any_sell_divergent,
            }
        )
    return rows


def family_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]:
    """F06 — family-mode mirror of :func:`portfolio_aggregates` with full-join.

    F06 D1 — keep ``portfolio_aggregates`` and ``family_aggregates``
    as sibling functions instead of one parametrized helper
    (F01 Decision 5 precedent). The collapsed classes / assets
    shortcut the per-profile path entirely.

    Sum invariants match :func:`portfolio_aggregates`:

    * ``broker-csv-import-totals`` — sum the broker-published
      ``Position.total_invested`` / ``Position.total_current``
      directly. Never recompute ``qty * price``.
    * Same ``Decimal`` / ``HUNDRED`` percent math.
    * Empty portfolio → ``gain_pct = None`` (renders "—") and
      ``current_pct`` zeroed so the progress bars are empty.
    * ``target_pct`` is forced to ``None`` for every class row
      so the template can branch on ``view == 'family'`` and hide
      the allocation-target pill. ``current_pct`` and
      ``current_value`` stay meaningful (sum is well-defined).
    """
    class_rows = _aggregate_classes_by_name(asset_classes)

    portfolio_invested = _ZERO
    portfolio_current = _ZERO
    for row in class_rows:
        portfolio_invested += row["invested"]
        portfolio_current += row["current_value"]
        # Collapse assets inside this aggregated class. Pass the
        # underlying class rows so positions across the same
        # asset name from different profiles add up.
        row["_assets"] = _aggregate_assets_by_name(row["_members"])
        # Drop the synthetic members list — the template only
        # consumes the per-asset dicts.
        row.pop("_members")

    portfolio_gain = portfolio_current - portfolio_invested
    if portfolio_invested == _ZERO:
        portfolio_gain_pct: Decimal | None = None
        for row in class_rows:
            row["current_pct"] = _ZERO
            for asset in row["_assets"]:
                asset["asset_pct"] = _ZERO
                asset["current_pct_class"] = _ZERO
                asset["current_pct_total"] = _ZERO
    else:
        portfolio_gain_pct = (portfolio_gain / portfolio_invested) * _HUNDRED
        for row in class_rows:
            row["current_pct"] = _pct_or_zero(row["current_value"], portfolio_current)
            class_current = row["current_value"]
            for asset in row["_assets"]:
                asset_pct = _pct_or_zero(asset["current_value"], class_current)
                asset["asset_pct"] = asset_pct
                asset["current_pct_class"] = asset_pct
                asset["current_pct_total"] = _pct_or_zero(asset["current_value"], portfolio_current)

    for row in class_rows:
        row["gain_value"] = row["current_value"] - row["invested"]
        row["gain_pct"] = _pct_or_none(row["gain_value"], row["invested"])
        row["class_current_pct_class"] = _HUNDRED if row["current_value"] > _ZERO else _ZERO
        row["class_target_pct_class"] = _HUNDRED if row["current_value"] > _ZERO else _ZERO
        row["class_deviation_pct_class"] = (
            row["class_current_pct_class"] - row["class_target_pct_class"]
        )
        row["portfolio_target_pct"] = None
        row["portfolio_deviation_pct"] = None
        row["position_target_value"] = None
        row["position_deviation_value"] = None
        for asset in row["_assets"]:
            asset["class_deviation_pct"] = None
            asset["portfolio_target_pct"] = None
            asset["portfolio_deviation_pct"] = None
            asset["position_target_value"] = None
            asset["position_deviation_value"] = None

    classes_out: list[dict[str, Any]] = []
    for row in class_rows:
        row["assets"] = row.pop("_assets")
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
