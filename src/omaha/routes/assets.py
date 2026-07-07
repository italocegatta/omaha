"""Asset CRUD routes (per-row model).

Each :class:`~omaha.models.AssetClass` owns a list of named
:class:`~omaha.models.Asset` rows (e.g. ``Tesouro Selic 2029``
under ``Renda Fixa``). Unlike the S02 snapshot model for
classes, the asset list is per-row: the user adds and removes
one asset at a time, so the editor does not need to re-type
the full list on every edit.

Endpoints
---------
- ``GET /assets`` — renders ``templates/assets.html``.

- ``POST /assets`` — form-encoded, adds asset, 303s to
  ``/assets``.

- ``POST /api/assets`` — JSON API for dashboard inline
  "+ Ativo" form. Creates an asset with ``name``, ``asset_class_id``,
  and optional ``target_pct``. Returns 201 on success, 409 on
  duplicate name, 422 on validation failure.

- ``PATCH /api/assets/{asset_id}`` — JSON API for inline target
  percent editor. Returns 200 / 404 / 422.

- ``DELETE /api/assets/{asset_id}`` — JSON API for dashboard
  inline ``×`` delete button. Returns 204 / 404.

- ``POST /assets/{asset_id}/delete`` — form-encoded, 303s to
  ``/assets``.

Validation invariants
---------------------
1. ``name`` is non-empty after ``.strip()`` and ≤ 64 chars
   (matches the column's ``String(64)`` width).
2. ``asset_class_id`` is a positive int that maps to an
   :class:`AssetClass` whose ``profile_id`` matches the active
   profile. Cross-class / cross-profile ids are rejected as 200
   with an error so the form is re-submittable (matches the
   S02 pattern for bad credentials and bad name).
3. On success, ``display_order`` is set to ``max + 1`` so the
   editor's stable iteration order (which is
   ``order_by="Asset.display_order"`` on the relationship)
   matches the user's insertion order across multiple adds.

Failure modes
-------------
- Validation failure: 200 with ``error`` in the body, no row
  committed. Inspectable in pytest output and via the rendered
  HTML (the error is rendered into a dedicated element so
  future copy edits don't break the assertion).
- Cross-profile / cross-class: 200 with an error message.
  Defensive against a hand-crafted form submission.
- Delete with a foreign id: 404, so a stale URL never silently
  no-ops.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile, require_profile_writable, require_user
from omaha.models import Asset, AssetClass, Profile, User
from omaha.mutation_guards import (
    record_mutation_audit,
    snapshot_before_destructive,
    snapshot_counts,
)

router = APIRouter(tags=["assets"])

# Column width mirrors the schema in 0003_assets.
NAME_MAX_LEN = 64

# Per-asset target range mirrors the schema in 0006_asset_target_pct
# (Numeric(5, 2)) — the validator additionally enforces the
# per-class sum-to-100 invariant on top of this per-row cap.
PCT_MIN = Decimal("0")
PCT_MAX = Decimal("100")

# asset-trade-flags: the per-asset ``currency_code`` allowlist mirrors
# the DB CHECK ``ck_asset_currency_code`` (migration 0016). The route
# rejects non-allowlist values with 422 BEFORE the DB enforces the
# CHECK so the client gets a clean ``detail`` message.
VALID_CURRENCY_CODES = frozenset({"BRL", "USD"})


def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


@router.get("/assets")
def get_assets() -> Response:
    """S03/T05 retired: the dedicated asset page is replaced by dashboard inline editing.

    Any request to ``GET /assets`` returns a 302 redirect to ``/``
    so any stale bookmark or stale browser tab lands on the
    dashboard, which now hosts the inline asset-target editor
    (S03/T03) and the inline add-asset form (S03/T03) and delete
    button (S03/T04). The form-encoded ``POST /assets`` (create)
    and ``POST /assets/{id}/delete`` (delete) handlers below
    remain wired; they are dead code that a future polish slice
    may prune.
    """
    return RedirectResponse("/", status_code=302)


@router.post("/assets", response_class=HTMLResponse, response_model=None)
def post_assets(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
    name: Annotated[str, Form()] = "",  # noqa: B006
    asset_class_id: Annotated[int, Form()] = 0,  # noqa: B006
    buy_enabled: Annotated[str, Form()] = "",  # noqa: B006
    sell_enabled: Annotated[str, Form()] = "",  # noqa: B006
    currency_code: Annotated[str, Form()] = "",  # noqa: B006
) -> Response:
    """Add a single asset to one of the active profile's classes.

    Returns
    -------
    - 303 → ``/assets`` on success.
    - 200 with the editor re-rendered and ``error`` in the body
      on validation failure (so the form is re-submittable).

    On success, the new row's ``display_order`` is the next slot
    after the class's current max, so repeated adds produce a
    contiguous, stable order.
    """
    # Reload classes for the re-render on either path (success
    # bounces via 303, but on failure the form re-renders with
    # the same data as the GET endpoint).
    classes = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )

    name_clean = name.strip()
    if not name_clean:
        return _render_assets_with_error(
            request,
            user,
            profile,
            classes,
            error="O nome do ativo é obrigatório.",
        )
    if len(name_clean) > NAME_MAX_LEN:
        return _render_assets_with_error(
            request,
            user,
            profile,
            classes,
            error=f"O nome do ativo deve ter no máximo {NAME_MAX_LEN} caracteres.",
        )

    # Cross-class / cross-profile rejection: the class id must
    # resolve to an AssetClass whose profile_id matches the
    # active profile. A hand-crafted id from another profile is
    # surfaced as a 200 with an error, not a 404, so the form is
    # re-submittable.
    target_class = (
        db.query(AssetClass)
        .filter(
            AssetClass.id == asset_class_id,
            AssetClass.profile_id == profile.id,
        )
        .one_or_none()
    )
    if target_class is None:
        return _render_assets_with_error(
            request,
            user,
            profile,
            classes,
            error="Selecione uma classe válida.",
        )

    # Next display_order slot: max(existing) + 1, or 0 if the
    # class is empty. The relationship's order_by makes
    # ``list(target_class.assets)`` already in display_order, so
    # the last element is the max.
    existing = list(target_class.assets)
    next_order = (existing[-1].display_order + 1) if existing else 0

    # asset-trade-flags: parse the 3 new trade-control fields with
    # permissive fallbacks (empty cell → defaults). An invalid
    # currency surfaces as a 200 with a human-readable error so
    # the legacy form path stays consistent with the rest of this
    # route.
    parsed_buy = _parse_bool(buy_enabled)
    # Empty / missing form field → default True (matches DB server_default).
    if parsed_buy is None:
        parsed_buy = True
    parsed_sell = _parse_bool(sell_enabled)
    if parsed_sell is None:
        parsed_sell = True
    parsed_currency = _parse_currency(currency_code) if currency_code.strip() else "BRL"
    if parsed_currency is None:
        return _render_assets_with_error(
            request,
            user,
            profile,
            classes,
            error=f"Moeda inválida: {currency_code!r}. Use BRL ou USD.",
        )

    db.add(
        Asset(
            asset_class_id=target_class.id,
            name=name_clean,
            display_order=next_order,
            buy_enabled=parsed_buy,
            sell_enabled=parsed_sell,
            currency_code=parsed_currency,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # Unique (asset_class_id, name) — two submits with the
        # same name in the same class are a DB-level collision
        # (the test only validates within-class uniqueness via
        # the unique constraint, not in-form duplicates).
        db.rollback()
        return _render_assets_with_error(
            request,
            user,
            profile,
            classes,
            error=f"Já existe um ativo com o nome {name_clean} nessa classe.",
        )

    return RedirectResponse("/assets", status_code=303)


@router.post("/api/assets", status_code=status.HTTP_201_CREATED, response_model=None)
def post_api_asset(
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
    body: Annotated[dict[str, Any] | None, Body()] = None,
) -> dict[str, Any]:
    if body is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Payload ausente.",
        )

    name_raw = body.get("name", "")
    name = name_raw.strip() if isinstance(name_raw, str) else ""
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O nome do ativo é obrigatório.",
        )
    if len(name) > NAME_MAX_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"O nome do ativo deve ter no máximo {NAME_MAX_LEN} caracteres.",
        )

    raw_class_id = body.get("asset_class_id")
    if raw_class_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selecione uma classe válida.",
        )
    try:
        asset_class_id = int(raw_class_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selecione uma classe válida.",
        ) from None

    target_class = (
        db.query(AssetClass)
        .filter(
            AssetClass.id == asset_class_id,
            AssetClass.profile_id == profile.id,
        )
        .one_or_none()
    )
    if target_class is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selecione uma classe válida.",
        )

    existing = (
        db.query(Asset)
        .filter(
            Asset.asset_class_id == target_class.id,
            Asset.name == name,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um ativo com o nome {name} nessa classe.",
        )

    if "target_pct" not in body:
        parsed_pct: Decimal = Decimal("0")
    else:
        raw_pct = body.get("target_pct")
        if raw_pct is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"A alocação do ativo deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
            )
        parsed_pct = _parse_pct(str(raw_pct))
        if parsed_pct is None or parsed_pct < PCT_MIN or parsed_pct > PCT_MAX:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"A alocação do ativo deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
            )

    if parsed_pct > Decimal("0"):
        # Sum gate removed by D006: off-100 per-class sums are
        # accepted on POST /api/assets; the alert UI surfaces the
        # deviation through the dashboard's class-delta badge and
        # the sticky allocation alert card.
        pass

    # asset-trade-flags: parse the 3 new trade-control fields. Each
    # is optional; missing → the model/DB default (``True / True /
    # 'BRL'``) is applied. An invalid value (non-allowlist currency,
    # garbage bool) is rejected with a 422 carrying the offending
    # field name so the dashboard's "+ Ativo" modal can surface it.
    parsed_buy = True
    if "buy_enabled" in body:
        raw_buy = body["buy_enabled"]
        if raw_buy is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="buy_enabled inválido.",
            )
        parsed = _parse_bool(raw_buy)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="buy_enabled inválido.",
            )
        parsed_buy = parsed

    parsed_sell = True
    if "sell_enabled" in body:
        raw_sell = body["sell_enabled"]
        if raw_sell is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="sell_enabled inválido.",
            )
        parsed = _parse_bool(raw_sell)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="sell_enabled inválido.",
            )
        parsed_sell = parsed

    parsed_currency = "BRL"
    if "currency_code" in body:
        raw_currency = body["currency_code"]
        if raw_currency is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="currency_code inválido.",
            )
        parsed = _parse_currency(raw_currency)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(f"currency_code {raw_currency!r} inválido. Use BRL ou USD."),
            )
        parsed_currency = parsed

    existing_assets = list(target_class.assets)
    next_order = (existing_assets[-1].display_order + 1) if existing_assets else 0

    asset = Asset(
        asset_class_id=target_class.id,
        name=name,
        target_pct=parsed_pct,
        display_order=next_order,
        buy_enabled=parsed_buy,
        sell_enabled=parsed_sell,
        currency_code=parsed_currency,
    )
    db.add(asset)
    try:
        db.commit()
        db.refresh(asset)
    except IntegrityError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um ativo com o nome {name} nessa classe.",
        ) from err

    return {
        "id": asset.id,
        "name": asset.name,
        "target_pct": str(asset.target_pct),
        "buy_enabled": asset.buy_enabled,
        "sell_enabled": asset.sell_enabled,
        "currency_code": asset.currency_code,
    }


@router.patch("/api/assets/{asset_id}", response_model=None)
def patch_asset(
    asset_id: int,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
    body: Annotated[dict[str, Any], Body()] = {},  # noqa: B006
) -> dict[str, Any]:
    """Update one asset's mutable attributes (per-row range check only; D006).

    Per the ``asset-table-view`` change (D006), the per-class sum
    gate was removed from this route: every commit is accepted
    within the per-row 0-100 range, and the resulting deviation
    (if any) is surfaced through the dashboard's class-delta badge
    and the sticky allocation alert card rather than a 422.

    The asset-trade-flags change extends the body with three more
    fields (``buy_enabled``, ``sell_enabled``, ``currency_code``)
    so the dashboard's inline toggle UI can flip a flag in a
    single round-trip. The route accepts any subset of the four
    fields; absent fields are no-ops. An empty body (no field
    supplied) is rejected with 422 so the caller doesn't get a
    silent no-op.

    The route is the server-side source of truth for the Alpine
    inline editor: PATCH 200 returns the updated asset state
    (``id``, ``target_pct``, ``buy_enabled``, ``sell_enabled``,
    ``currency_code``) so the editor can refresh the row without
    a full page reload; PATCH 422 is reserved for per-row range
    violations, invalid bools / currencies, and cross-profile /
    cross-class ownership errors. The 422 vs 404 split lets the
    UI differentiate "bad input" from "stale URL".

    Body
    ----
    JSON object — any subset of ``target_pct``, ``buy_enabled``,
    ``sell_enabled``, ``currency_code``. ``target_pct`` is a
    *string* value so the editor can post ``"40"`` or ``"40.5"``
    without a JSON-number round-trip (same ``_parse_pct`` style
    as the S02 classes route). ``buy_enabled`` / ``sell_enabled``
    accept JSON booleans or the string forms ``"true"`` /
    ``"false"`` / ``"1"`` / ``"0"``; ``currency_code`` must be
    one of ``"BRL"`` or ``"USD"`` (case-insensitive; normalized
    to upper case before persistence).

    Ownership check
    ---------------
    The asset id is resolved with a single ``db.get`` and the
    ownership check walks the FK back to the active profile —
    cross-profile is 404, never silent. The inline editor only
    targets the active profile's own assets, so a 404 here means
    a stale URL or a hand-crafted id.

    Returns
    -------
    - 200 with ``{id, target_pct, buy_enabled, sell_enabled,
      currency_code}`` on success.
    - 404 if the asset doesn't exist or doesn't belong to the active profile.
    - 422 with ``{"detail": "..."}`` on per-row range, bool,
      currency, or empty-body violations.
    """
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if not isinstance(body, dict) or not body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Informe ao menos um campo: target_pct, buy_enabled, "
            "sell_enabled ou currency_code.",
        )

    allowed_keys = {"target_pct", "buy_enabled", "sell_enabled", "currency_code"}
    unknown = set(body) - allowed_keys
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Campo desconhecido: {', '.join(sorted(unknown))}.",
        )

    if not any(k in body for k in allowed_keys):
        # Body present but empty of recognized keys (e.g. {"foo": "bar"}).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Informe ao menos um campo: target_pct, buy_enabled, "
            "sell_enabled ou currency_code.",
        )

    if "target_pct" in body:
        raw = body["target_pct"]
        parsed = _parse_pct(raw)
        if parsed is None or parsed < PCT_MIN or parsed > PCT_MAX:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"A alocação do ativo deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
            )
        asset.target_pct = parsed

    if "buy_enabled" in body:
        raw = body["buy_enabled"]
        parsed = _parse_bool(raw)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="buy_enabled inválido.",
            )
        asset.buy_enabled = parsed

    if "sell_enabled" in body:
        raw = body["sell_enabled"]
        parsed = _parse_bool(raw)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="sell_enabled inválido.",
            )
        asset.sell_enabled = parsed

    if "currency_code" in body:
        raw = body["currency_code"]
        parsed = _parse_currency(raw)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"currency_code {raw!r} inválido. Use BRL ou USD.",
            )
        asset.currency_code = parsed

    # Per-class sum: sum gate removed by D006 — off-100 per-class
    # sums are accepted on PATCH /api/assets/{id}; the dashboard's
    # alert UI (the class-delta badge + sticky allocation alert
    # card) surfaces the resulting deviation.

    db.commit()
    return {
        "id": asset.id,
        "target_pct": str(asset.target_pct),
        "buy_enabled": asset.buy_enabled,
        "sell_enabled": asset.sell_enabled,
        "currency_code": asset.currency_code,
    }


@router.delete(
    "/api/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
def delete_api_asset(
    asset_id: int,
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
) -> Response:
    """Delete one asset.

    R06 (PRD §4.11): captures a pre-mutation snapshot and
    writes an audit row after the commit. The operator can
    roll back any wipe via ``/admin/restore/{snapshot_id}``.
    """
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    snapshot_path, snapshot_id = _capture_or_abort(db, "DELETE /api/assets/{id}")
    before_counts = snapshot_counts(db, profile.id)
    db.delete(asset)
    db.commit()
    _record_audit(
        db,
        route="DELETE /api/assets/{id}",
        actor_user_id=_current_user_id(request),
        profile_id=profile.id,
        before_counts=before_counts,
        snapshot_path=snapshot_path,
        snapshot_id=snapshot_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _parse_pct(raw: str) -> Decimal | None:
    """Return ``raw`` parsed as a :class:`Decimal`, or ``None`` on failure.

    Mirrors the S02 ``classes`` route's ``_parse_pct`` so the
    editor can post ``"40"`` or ``"40.5"`` with the same
    forgiving parse. A percent sign is stripped if present; an
    empty / whitespace / non-numeric string is rejected.
    """
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().rstrip("%").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except (ArithmeticError, ValueError, TypeError):  # pragma: no cover - Decimal edge cases
        return None


def _parse_bool(raw: object) -> bool | None:
    """Return ``raw`` parsed as a :class:`bool`, or ``None`` on failure.

    Permissive like ``_parse_pct`` so the inline toggle UI can post
    ``true``/``false`` (JSON boolean) and the form-encoded legacy
    POST can post ``"1"``/``"0"`` interchangeably. ``None`` means
    "missing or unparseable" — the caller decides whether to treat
    it as a 422 or fall back to the route's default. An empty
    string is also ``None`` so legacy form posts that omit the
    field cleanly default to the route's True (matches the DB
    ``server_default``).
    """
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        s = raw.strip().lower()
        if not s:
            return None
        if s in {"true", "1", "yes", "y", "t"}:
            return True
        if s in {"false", "0", "no", "n", "f"}:
            return False
    return None


def _parse_currency(raw: object) -> str | None:
    """Return ``raw`` normalized to the currency allowlist, or ``None`` on failure.

    Upper-cases the input; rejects anything outside
    ``VALID_CURRENCY_CODES``. Used by both the JSON
    ``POST /api/assets`` / ``PATCH /api/assets/{id}`` paths and
    the form-encoded ``POST /assets`` legacy path.
    """
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip().upper()
    if cleaned in VALID_CURRENCY_CODES:
        return cleaned
    return None


@router.post("/assets/{asset_id}/delete", response_model=None)
def delete_asset(
    asset_id: int,
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
) -> RedirectResponse:
    """Delete an asset that walks back to the active profile, then 303.

    The ownership check walks the FK to the class and then the
    class to the profile — a hand-crafted id from another
    profile is a 404, not a silent delete. Same convention as
    the S02 ``/classes/{id}/delete`` route.

    R06: captures a pre-mutation snapshot and writes an audit
    row after the commit (PRD §4.11 reactive layer).
    """
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    snapshot_path, snapshot_id = _capture_or_abort(db, "POST /assets/{id}/delete")
    before_counts = snapshot_counts(db, profile.id)
    db.delete(asset)
    db.commit()
    _record_audit(
        db,
        route="POST /assets/{id}/delete",
        actor_user_id=_current_user_id(request),
        profile_id=profile.id,
        before_counts=before_counts,
        snapshot_path=snapshot_path,
        snapshot_id=snapshot_id,
    )
    return RedirectResponse("/assets", status_code=303)


def _render_assets_with_error(
    request: Request,
    user: User,
    profile: Profile,
    classes: list[AssetClass],
    *,
    error: str,
) -> Response:
    """Re-render ``assets.html`` with ``error``.

    Status 200 (not 4xx) so the form is re-submittable. The
    classes list and per-class assets are reloaded so the page
    matches the GET view exactly.
    """
    assets_by_class: dict[int, list[Asset]] = {cls.id: list(cls.assets) for cls in classes}
    return _templates(request).TemplateResponse(
        request,
        "assets.html",
        {
            "user": user,
            "profile": profile,
            "classes": classes,
            "assets_by_class": assets_by_class,
            "error": error,
        },
        status_code=200,
    )


# ---------------------------------------------------------------------------
# R06 — DB mutation safety helpers (PRD §4.11 reactive layer)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


def _current_user_id(request: Request) -> int | None:
    """Read the current user id from the session, or ``None``."""
    return request.session.get("user_id")


def _capture_or_abort(db: DbSession, route: str) -> tuple[Path | None, int | None]:
    """Capture a pre-mutation snapshot; abort with HTTP 500 on failure."""
    try:
        return snapshot_before_destructive(db)
    except (FileNotFoundError, OSError, Exception) as exc:  # noqa: BLE001
        logger.exception("snapshot_before_destructive failed for %s: %s", route, exc)
        raise


def _record_audit(
    db: DbSession,
    *,
    route: str,
    actor_user_id: int | None,
    profile_id: int | None,
    before_counts: dict,
    snapshot_path: Path | None,
    snapshot_id: int | None,
) -> None:
    """Write a :class:`DbMutation` audit row after a destructive commit (best-effort)."""
    after_counts = snapshot_counts(db, profile_id) if profile_id else {}
    try:
        record_mutation_audit(
            db,
            route=route,
            actor_user_id=actor_user_id,
            profile_id=profile_id,
            before_counts=before_counts,
            after_counts=after_counts,
            snapshot_path=snapshot_path,
            snapshot_id=snapshot_id,
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - best-effort
        logger.warning("record_mutation_audit failed for %s: %s", route, exc)
        db.rollback()


__all__ = ["router"]
