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

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.models import Asset, AssetClass, Profile, User
from omaha.validators import validate_target_pct_sum

router = APIRouter(tags=["assets"])

# Column width mirrors the schema in 0003_assets.
NAME_MAX_LEN = 64

# Per-asset target range mirrors the schema in 0006_asset_target_pct
# (Numeric(5, 2)) — the validator additionally enforces the
# per-class sum-to-100 invariant on top of this per-row cap.
PCT_MIN = Decimal("0")
PCT_MAX = Decimal("100")


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
    name: Annotated[str, Form()] = "",  # noqa: B006
    asset_class_id: Annotated[int, Form()] = 0,  # noqa: B006
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

    db.add(
        Asset(
            asset_class_id=target_class.id,
            name=name_clean,
            display_order=next_order,
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
        other_pcts = [a.target_pct for a in target_class.assets]
        candidate = other_pcts + [parsed_pct]
        ok, error = validate_target_pct_sum(candidate)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=error,
            )

    existing_assets = list(target_class.assets)
    next_order = (existing_assets[-1].display_order + 1) if existing_assets else 0

    asset = Asset(
        asset_class_id=target_class.id,
        name=name,
        target_pct=parsed_pct,
        display_order=next_order,
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

    return {"id": asset.id, "name": asset.name, "target_pct": str(asset.target_pct)}


@router.patch("/api/assets/{asset_id}", response_model=None)
def patch_asset(
    asset_id: int,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    body: Annotated[dict[str, Any], Body()] = {},  # noqa: B006
) -> dict[str, Any]:
    """Update one asset's ``target_pct`` and validate the per-class sum.

    The route is the server-side source of truth for the T03
    Alpine inline editor: PATCH 200 returns ``{"id", "target_pct"}``
    so the editor can refresh the row without a full page reload;
    PATCH 422 returns ``{"detail": "<Sobra/Falta X%>"}`` so the
    editor can paint the input red and surface the class-delta
    badge. The 422 vs 404 split lets the UI differentiate "bad
    input" from "stale URL".

    Body
    ----
    JSON object ``{"target_pct": "40"}`` — a *string* value so the
    editor can post ``"40"`` or ``"40.5"`` without a JSON-number
    round-trip. The same ``_parse_pct`` style as the S02 classes
    route is used (the value is a ``Decimal``, the field is text).

    Ownership check
    ---------------
    The asset id is resolved with a single ``db.get`` and the
    ownership check walks the FK back to the active profile —
    cross-profile is 404, never silent. The T03 editor only
    targets the active profile's own assets, so a 404 here means
    a stale URL or a hand-crafted id.

    Validation
    ----------
    The per-class sum is recomputed as ``[other_assets.target_pct] + [new_value]``
    and passed to :func:`omaha.validators.validate_target_pct_sum`.
    The validator is the single source of truth for the error
    message; the route re-emits it verbatim so the T03 preview
    and the T02 commit show identical wording.

    Returns
    -------
    - 200 with ``{"id": asset.id, "target_pct": "<new_value>"}`` on success.
    - 404 if the asset doesn't exist or doesn't belong to the active profile.
    - 422 with ``{"detail": "<validator error>"}`` on a per-class
      sum violation or a per-row range/out-of-range violation.
    """
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    raw = body.get("target_pct", "") if isinstance(body, dict) else ""
    parsed = _parse_pct(raw)
    if parsed is None or parsed < PCT_MIN or parsed > PCT_MAX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"A alocação do ativo deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
        )

    # Per-class sum: take every OTHER asset's current target_pct
    # plus the new value, and ask the validator. The validator
    # is the single source of truth for the message — the route
    # never re-formats it, so the T03 preview and the T02 commit
    # display identical wording.
    other_pcts = [a.target_pct for a in asset.asset_class.assets if a.id != asset.id]
    candidate = other_pcts + [parsed]
    ok, error = validate_target_pct_sum(candidate)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=error,
        )

    asset.target_pct = parsed
    db.commit()
    return {"id": asset.id, "target_pct": str(parsed)}


@router.delete(
    "/api/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
def delete_api_asset(
    asset_id: int,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
) -> Response:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(asset)
    db.commit()
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


@router.post("/assets/{asset_id}/delete", response_model=None)
def delete_asset(
    asset_id: int,
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
) -> RedirectResponse:
    """Delete an asset that walks back to the active profile, then 303.

    The ownership check walks the FK to the class and then the
    class to the profile — a hand-crafted id from another
    profile is a 404, not a silent delete. Same convention as
    the S02 ``/classes/{id}/delete`` route.
    """
    asset = db.get(Asset, asset_id)
    if asset is None or asset.asset_class.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(asset)
    db.commit()
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


__all__ = ["router"]
