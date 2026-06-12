"""Macro-class CRUD routes (snapshot semantics).

Each :class:`~omaha.models.Profile` owns a list of named asset
classes (e.g. ``Renda Fixa 60%``) that drive the S03+ portfolio
breakdown. The editor lives in ``templates/classes.html`` (linked
from the dashboard) and always starts empty (D014); the user
retypes the desired set on every visit.

Endpoints
---------
- ``GET /classes`` — renders the snapshot editor with one empty
  row. No pre-population from the DB.
- ``POST /classes`` — accepts ``name[]`` / ``target_pct[]``
  parallel arrays via :class:`Form`. Validates per-row name + pct,
  in-form duplicate name, and the sum-to-100 invariant. On
  success, performs a delete-all-then-insert snapshot in one
  transaction and 303s to ``/`` (dashboard). On failure, re-renders
  the editor with an ``error`` message, status 200.
- ``POST /classes/{class_id}/delete`` — removes a single class
  after asserting it belongs to the active profile. 303s to ``/``.

The snapshot model (D016) is the only model: there is no
partial-update path. ``class_id[]`` and ``deleted_ids`` form
fields are not accepted.

Validation invariants
---------------------
The validation lives on the server because the client-side
"reactive total" affordance is a UX hint, not a security control.
The full set of rules:

1. Every ``name`` is non-empty and ≤ 64 characters (matches the
   column's ``String(64)`` width).
2. Every ``target_pct`` parses to a :class:`~decimal.Decimal` in
   the closed interval ``[0, 100]`` (matches the column's
   ``Numeric(5, 2)``).
3. ``abs(sum - 100) ≤ 0.01`` — a 1-cent tolerance so the message
   can be reported as a whole number (``Falta 10`` /
   ``Sobra 10``).
4. No two names in the same submission are identical (in addition
   to the DB unique constraint, so a duplicate surfaces as a
   clean 200 form re-render rather than an ``IntegrityError``).
5. Any row whose ``class_id`` references an existing row must
   reference a row that belongs to the active profile — defensive
   against a hand-crafted form submission.

The success path sets ``display_order = (max + 1)`` for new rows
in submission order, so the editor's stable iteration order
(``Profile.asset_classes`` is ``order_by="AssetClass.display_order"``)
matches the user's input order on the first save.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.models import AssetClass, Profile, User
from omaha.validators import validate_target_pct_sum

router = APIRouter(tags=["classes"])

# Column width + numeric range mirrors the schema in 0002_macro_classes.
NAME_MAX_LEN = 64
PCT_MIN = Decimal("0")
PCT_MAX = Decimal("100")
SUM_TARGET = Decimal("100")
SUM_TOLERANCE = Decimal("0.01")


def _templates(request: Request):
    """Return the application-wide Jinja2 templates instance."""
    return request.app.state.templates


def _parse_pct(raw: str) -> Decimal | None:
    """Return ``raw`` parsed as a :class:`Decimal`, or ``None`` on failure.

    Accepts any whitespace-padded, percent-sign-suffixed value a
    browser might submit (the form sends ``60`` or ``60.5`` — no
    percent sign — but the parse is forgiving for forward
    compatibility with paste-in values).
    """
    cleaned = raw.strip().rstrip("%").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _validate_rows(
    names: list[str],
    pcts: list[str],
) -> tuple[list[dict[str, object]] | None, str | None]:
    """Return ``(rows, None)`` on success or ``(None, error_message)``.

    Snapshot model: every submitted row is treated as a new row
    (no ``class_id`` in the payload). The route wipes the
    profile's existing classes and inserts the validated set in
    one transaction, so per-row identity is not part of the
    contract.
    """
    n = max(len(names), len(pcts))
    rows: list[dict[str, object]] = []
    seen_names: dict[str, int] = {}

    for i in range(n):
        name_raw = names[i] if i < len(names) else ""
        pct_raw = pcts[i] if i < len(pcts) else ""

        # Empty + whitespace names are caught before length to keep
        # the error message precise (the test plan demands
        # "obrigatório" for the empty case, not "must be at most
        # 64 characters").
        name = name_raw.strip()
        if not name:
            return None, "O nome da classe é obrigatório."
        if len(name) > NAME_MAX_LEN:
            return (
                None,
                f"O nome da classe deve ter no máximo {NAME_MAX_LEN} caracteres.",
            )

        # Duplicate detection runs against the stripped name so
        # ``"Renda Fixa "`` and ``"Renda Fixa"`` collide, matching
        # the DB unique constraint's case-sensitive comparison on
        # the trimmed value.
        if name in seen_names:
            return None, f"Já existe uma classe com o nome {name}."
        seen_names[name] = i

        pct = _parse_pct(pct_raw)
        if pct is None or pct < PCT_MIN or pct > PCT_MAX:
            return (
                None,
                f"A alocação da classe deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
            )

        rows.append({"name": name, "pct": pct})

    # Sum invariant is the last per-form check — it's the most
    # expensive (it touches every row) and the message is the
    # most user-facing.
    total = sum((r["pct"] for r in rows), Decimal("0"))
    delta = SUM_TARGET - total
    if abs(delta) > SUM_TOLERANCE:
        if delta > 0:
            return None, f"Falta {int(delta.to_integral_value(rounding=ROUND_HALF_UP))}."
        else:
            return None, f"Sobra {int((-delta).to_integral_value(rounding=ROUND_HALF_UP))}."

    return rows, None


@router.get("/classes", response_class=HTMLResponse, response_model=None)
def get_classes(
    request: Request,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Render the dedicated class editor page.

    The dashboard surfaces a "Gerenciar classes" shortcut that
    links here. The editor always starts with one empty row
    regardless of the profile's existing classes — the user must
    re-type the desired set on every visit (``POST /classes``
    performs a delete-all-then-insert snapshot).
    """
    return _templates(request).TemplateResponse(
        request,
        "classes.html",
        {"user": user, "profile": profile, "error": None},
    )


@router.post("/classes", response_class=HTMLResponse, response_model=None)
def post_classes(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
    name: Annotated[list[str], Form(alias="name[]")] = [],  # noqa: B006
    target_pct: Annotated[list[str], Form(alias="target_pct[]")] = [],  # noqa: B006
) -> Response:
    """Validate, then **snapshot-replace** the profile's class rows.

    Model: the form is the source of truth. Whatever the user
    submits replaces everything that was there before. Empty form
    arrays are accepted as a "clear all classes" action — the
    profile ends up with zero classes and the dashboard no
    longer shows the summary.

    Returns
    -------
    - 303 → ``/`` on success.
    - 200 with the editor re-rendered and ``error`` in the body
      on validation failure.
    """
    # Empty submission = clear all. The editor disables the save
    # button on zero rows, so this branch only fires for the
    # "wipe everything" use case (intentional or programmatic).
    if not name:
        db.query(AssetClass).filter(AssetClass.profile_id == profile.id).delete()
        db.commit()
        return RedirectResponse("/", status_code=303)

    rows, error = _validate_rows(name, target_pct)
    if error is not None:
        return _render_classes_with_error(
            request,
            user,
            profile,
            error=error,
        )

    # Snapshot: wipe all existing rows for this profile, then insert
    # the submitted set in the order they arrived. One transaction,
    # so partial failures leave the DB untouched.
    db.query(AssetClass).filter(AssetClass.profile_id == profile.id).delete()

    for idx, row in enumerate(rows):
        db.add(
            AssetClass(
                profile_id=profile.id,
                name=row["name"],  # type: ignore[arg-type]
                target_pct=row["pct"],  # type: ignore[arg-type]
                display_order=idx,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _render_classes_with_error(
            request,
            user,
            profile,
            error="Já existe uma classe com o nome duplicado.",
        )

    return RedirectResponse("/", status_code=303)


@router.post("/classes/{class_id}/delete", response_model=None)
def delete_class(
    class_id: int,
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
) -> RedirectResponse:
    """Delete a class that belongs to the active profile, then 303 to ``/``.

    A non-existent id and a cross-profile id are both treated as
    404 — the form template only renders delete buttons for the
    active profile's own rows, so this is the right response for
    a stale or hand-crafted URL.
    """
    cls = db.get(AssetClass, class_id)
    if cls is None or cls.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(cls)
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.patch("/api/classes/{class_id}", response_model=None)
def patch_class(
    class_id: int,
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    payload: dict = None,
) -> Response:
    """Update a single class's ``target_pct" inline with per-profile sum validation.

    The dashboard's Alpine component clicks the % cell, turns it into an
    input, and on blur sends a PATCH with ``{"target_pct": "<new>"}``.
    Only the ``target_pct`` field is accepted — name changes and other
    mutations go through the snapshot ``POST /classes`` editor.

    Returns
    -------
    - 200 with ``{"id": class_id, "target_pct": "<new>"}" on success.
    - 404 if the class does not exist or belongs to another profile.
    - 422 with ``{"detail": <error>}" if the new value breaks the
      per-profile 100-sum invariant (message matches the class editor's
      "Sobra X%" / "Falta X%" wording).
    """
    cls = db.get(AssetClass, class_id)
    if cls is None or cls.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    raw_pct = payload.get("target_pct")
    if raw_pct is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    new_pct = _parse_pct(str(raw_pct))
    if new_pct is None or new_pct < PCT_MIN or new_pct > PCT_MAX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A alocação da classe deve estar entre {int(PCT_MIN)} e {int(PCT_MAX)}.",
        )

    # Gather all other classes in the profile + the new value for this one.
    other_classes = (
        db.query(AssetClass)
        .filter(
            AssetClass.profile_id == profile.id,
            AssetClass.id != class_id,
        )
        .all()
    )
    all_pcts = [c.target_pct for c in other_classes] + [new_pct]

    ok, error = validate_target_pct_sum(all_pcts)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error,
        )

    cls.target_pct = new_pct
    db.commit()
    return {"id": cls.id, "target_pct": str(new_pct)}


def _render_classes_with_error(
    request: Request,
    user: User,
    profile: Profile,
    *,
    error: str,
) -> Response:
    """Re-render ``classes.html`` with ``error``.

    The status is 200 (not 4xx) so the form is re-submittable —
    the same pattern :mod:`omaha.routes.auth` uses for bad
    credentials. The snapshot editor always starts with one empty
    row (D014), so the user's previous submission is not echoed
    on error; they retype the corrected set.
    """
    return _templates(request).TemplateResponse(
        request,
        "classes.html",
        {"user": user, "profile": profile, "error": error},
        status_code=200,
    )


__all__ = ["router"]
