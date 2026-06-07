"""Macro-class CRUD routes.

Each :class:`~omaha.models.Profile` owns a list of named asset
classes (e.g. ``Renda Fixa 60%``) that drive the S03+ portfolio
breakdown. The editor lives inside the dashboard template
(``templates/dashboard.html``), but the form posts here.

Endpoints
---------
- ``GET /classes`` — URL contract for future direct links; the
  editor is rendered inside the dashboard, so this currently 303s
  to ``/``.
- ``POST /classes`` — accepts ``class_id[]`` / ``name[]`` /
  ``target_pct[]`` parallel arrays via :class:`Form`. Validates
  per-row name + pct, in-form duplicate name, and the sum-to-100
  invariant. On success, commits all rows in a single transaction
  (insert new, update existing) and 303s to ``/``. On failure,
  re-renders the dashboard with an ``error`` message and the
  submitted rows echoed back, status 200.
- ``POST /classes/{class_id}/delete`` — removes a single class
  after asserting it belongs to the active profile. 303s to ``/``.

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
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile
from omaha.models import AssetClass, Profile

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
    class_ids: list[str],
    names: list[str],
    pcts: list[str],
) -> tuple[list[dict[str, object]] | None, str | None]:
    """Return ``(rows, None)`` on success or ``(None, error_message)``.

    On success, ``rows`` is a list of dicts with normalised
    ``class_id`` (``int`` for existing rows, ``None`` for new),
    ``name`` (stripped), and ``pct`` (:class:`Decimal`). The dict
    is the shape the dashboard template expects when echoing the
    submission back to the user on a validation failure.
    """
    n = max(len(class_ids), len(names), len(pcts))
    rows: list[dict[str, object]] = []
    seen_names: dict[str, int] = {}

    for i in range(n):
        cid_raw = class_ids[i] if i < len(class_ids) else ""
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

        cid: int | None = None
        cid_text = cid_raw.strip()
        if cid_text:
            try:
                cid = int(cid_text)
            except (TypeError, ValueError):
                return None, "Identificador de classe inválido."

        rows.append({"class_id": cid, "name": name, "pct": pct})

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
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Render the dedicated class editor page.

    The S03 dashboard surfaces a "Gerenciar classes" shortcut that
    links here, and the editor is the canonical view of a profile's
    asset classes. The template seeds itself from the profile's
    existing ``AssetClass`` rows so a user returning to the editor
    sees what they previously saved.
    """
    classes = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )
    # Coerce ORM rows to plain dicts so Jinja's ``tojson`` filter can
    # serialise them in the Alpine ``x-init`` initial state. The
    # editor's ``_toRow`` reads ``class_id`` (snake_case, matches the
    # hidden form field name) and ``target_pct`` (matches the DB
    # column) as the public keys.
    class_rows = [
        {
            "id": c.id,
            "class_id": c.id,
            "name": c.name,
            "target_pct": float(c.target_pct),
        }
        for c in classes
    ]
    return _templates(request).TemplateResponse(
        request,
        "classes.html",
        {"profile": profile, "classes": class_rows, "error": None},
    )


@router.post("/classes", response_class=HTMLResponse, response_model=None)
def post_classes(
    request: Request,
    db: DbSession,
    profile: Profile = Depends(require_active_profile),
    class_id: Annotated[list[str], Form(alias="class_id[]")] = [],  # noqa: B006 — FastAPI form list
    name: Annotated[list[str], Form(alias="name[]")] = [],  # noqa: B006
    target_pct: Annotated[list[str], Form(alias="target_pct[]")] = [],  # noqa: B006
    deleted_ids: Annotated[str, Form()] = "",
) -> Response:
    """Validate, then upsert the profile's class rows in one transaction.

    Empty form arrays are accepted (the user may have removed every
    row) and are rejected by the sum check with ``"Falta 100"`` —
    the same surface a deliberate-but-incomplete submission would
    hit, so the error UX is uniform.

    Returns
    -------
    - 303 → ``/`` on success.
    - 200 with the dashboard re-rendered and ``error`` in the body
      on validation failure.
    - 200 with ``"Já existe uma classe com o nome X"`` if a name
      collides with an existing row in the DB (the in-form
      duplicate check above catches same-form collisions; this
      catches cross-submission collisions when the user edits an
      existing class to a name already used by a sibling).
    """
    rows, error = _validate_rows(class_id, name, target_pct)
    if error is not None:
        # Echo the raw submission back so the template can repopulate
        # the form. The S03 classes.html re-renders the editor with
        # the same rows the user submitted and surfaces the error.
        echoed = _echoed_rows(class_id, name, target_pct)
        return _render_classes_with_error(request, profile, error=error, rows=echoed)

    # Lock the new-row display_order against a fresh max query so
    # the assigned values are stable across the loop even if the
    # caller mixed new and updated rows in any order.
    max_order = (
        db.query(func.max(AssetClass.display_order))
        .filter(AssetClass.profile_id == profile.id)
        .scalar()
    )
    next_order = (max_order + 1) if max_order is not None else 0

    for row in rows:
        if row["class_id"] is None:
            db.add(
                AssetClass(
                    profile_id=profile.id,
                    name=row["name"],  # type: ignore[arg-type]
                    target_pct=row["pct"],  # type: ignore[arg-type]
                    display_order=next_order,
                )
            )
            next_order += 1
        else:
            existing = db.get(AssetClass, row["class_id"])
            if existing is None or existing.profile_id != profile.id:
                # Defensive: a hand-crafted form pointed at someone
                # else's class. 404 keeps the surface honest.
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            existing.name = row["name"]  # type: ignore[assignment]
            existing.target_pct = row["pct"]  # type: ignore[assignment]

    try:
        db.commit()
    except IntegrityError:
        # A name collided with a sibling row that the in-form
        # duplicate check missed (e.g. the user edited row A to
        # match row B's name in the same submission). Convert to
        # a clean form re-render so the user can fix the
        # collision and resubmit.
        db.rollback()
        echoed = _echoed_rows(class_id, name, target_pct)
        return _render_classes_with_error(
            request,
            profile,
            error="Já existe uma classe com o nome duplicado.",
            rows=echoed,
        )

    # Process the soft-deleted ids (the Alpine editor records ids of
    # rows the user removed client-side as a comma-separated list and
    # submits them in a hidden field). We delete after the upsert so
    # the response is the fresh view of the profile's classes, not a
    # mid-transaction snapshot.
    if deleted_ids:
        ids_to_delete = [int(x) for x in deleted_ids.split(",") if x.strip().isdigit()]
        if ids_to_delete:
            victims = (
                db.query(AssetClass)
                .filter(
                    AssetClass.id.in_(ids_to_delete),
                    AssetClass.profile_id == profile.id,
                )
                .all()
            )
            for victim in victims:
                db.delete(victim)
            db.commit()

    return RedirectResponse("/classes", status_code=303)


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


def _echoed_rows(class_ids: list[str], names: list[str], pcts: list[str]) -> list[dict[str, str]]:
    """Return the raw submission as strings, aligned row-by-row.

    The dashboard template receives this list to repopulate the
    editor inputs on a validation failure. We keep the values as
    strings (not parsed) so the user sees exactly what they
    submitted, including the bad pct that triggered the error.
    """
    n = max(len(class_ids), len(names), len(pcts))
    return [
        {
            "class_id": class_ids[i] if i < len(class_ids) else "",
            "name": names[i] if i < len(names) else "",
            "target_pct": pcts[i] if i < len(pcts) else "",
        }
        for i in range(n)
    ]


def _render_classes_with_error(
    request: Request,
    profile: Profile,
    *,
    error: str,
    rows: list[dict[str, str]],
) -> Response:
    """Re-render ``classes.html`` with ``error`` + echoed ``rows``.

    The status is 200 (not 4xx) so the form is re-submittable —
    the same pattern :mod:`omaha.routes.auth` uses for bad
    credentials. ``rows`` is the echoed user submission, which
    the S03 editor seeds itself with so the user can fix and
    resubmit. The editor's reactive total still surfaces the
    "Falta/Sobra" message in addition to the server-rendered
    one.
    """
    return _templates(request).TemplateResponse(
        request,
        "classes.html",
        {"profile": profile, "classes": rows, "error": error},
        status_code=200,
    )


__all__ = ["router"]
