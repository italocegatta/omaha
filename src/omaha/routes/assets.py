"""Asset CRUD routes (per-row model).

Each :class:`~omaha.models.AssetClass` owns a list of named
:class:`~omaha.models.Asset` rows (e.g. ``Tesouro Selic 2029``
under ``Renda Fixa``). Unlike the S02 snapshot model for
classes, the asset list is per-row: the user adds and removes
one asset at a time, so the editor does not need to re-type
the full list on every edit.

Endpoints
---------
- ``GET /assets`` — renders ``templates/assets.html`` with the
  profile's classes (for the dropdown) and each class's asset
  list. If the profile has zero classes, the template renders
  an empty-state with a link to ``/classes``; the add-asset
  form is hidden.
- ``POST /assets`` — accepts ``name`` (single string) and
  ``asset_class_id`` (single int) via :class:`Form`. Validates
  that the name is non-empty + ≤ 64 chars and the class id
  belongs to the active profile. On success, appends a new
  :class:`Asset` with ``display_order = max_existing + 1`` and
  303s to ``/assets`` (the editor, not the dashboard — matches
  the S02 POST → /classes editor redirect). On failure,
  re-renders with ``error`` and status 200.
- ``POST /assets/{asset_id}/delete`` — removes an asset after
  asserting it walks the FK back to the active profile. 303s
  to ``/assets``.

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

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.models import Asset, AssetClass, Profile, User

router = APIRouter(tags=["assets"])

# Column width mirrors the schema in 0003_assets.
NAME_MAX_LEN = 64


def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


@router.get("/assets", response_class=HTMLResponse, response_model=None)
def get_assets(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Render the dedicated asset editor page.

    Loads the profile's classes (ordered by ``display_order``) and
    each class's assets for the table view. If the profile has no
    classes yet, the template shows the "Crie classes antes"
    empty state with a link to ``/classes``; the add-asset form
    is hidden because there is no class to add an asset to.
    """
    classes = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )
    assets_by_class: dict[int, list[Asset]] = {cls.id: list(cls.assets) for cls in classes}
    return _templates(request).TemplateResponse(
        request,
        "assets.html",
        {
            "user": user,
            "profile": profile,
            "classes": classes,
            "assets_by_class": assets_by_class,
            "error": None,
        },
    )


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
