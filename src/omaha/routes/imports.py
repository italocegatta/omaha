"""S04 CSV import routes.

Endpoints
---------
- ``GET  /import``           — render the upload form.
- ``POST /import``           — parse an uploaded CSV, persist an
                               ``ImportPreview``, set the preview id
                               in the session, 303 to ``/import/review``.
- ``GET  /import/review``    — render the matched/unmatched split.
                               Honors a 1h preview expiration window.
- ``POST /import/confirm``   — upsert ``Position`` rows for every
                               auto-matched and user-resolved row,
                               delete the preview, 303 to ``/``.

The matcher from ``omaha.csv_import`` is the algorithm; this
module wires it to FastAPI, persists the parsed result in the
``import_previews`` table, and surfaces the review screen.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.config import settings
from omaha.csv_import import (
    RawPosition,
    match_positions,
    parse_positions,
    suggest_class_id,
)
from omaha.models import Asset, AssetClass, ImportPreview, Profile, User
from omaha.routes.pages import _CLASS_COLORS

router = APIRouter(tags=["imports"])

logger = logging.getLogger(__name__)

# 1 MB upload cap — broker statements are well under this, and a
# generous cap is friendlier than a tight one for the demo CSV.
MAX_UPLOAD_BYTES = 1 * 1024 * 1024

# A preview is "fresh" for this window. After PREVIEW_TTL_SECONDS the
# review screen renders the "Expirado" state and forces the user to
# re-upload. The TTL is configurable so e2e tests can use a 1s window.
PREVIEW_TTL = timedelta(seconds=settings.PREVIEW_TTL_SECONDS)

# Column width mirrors the schema in 0003_assets.
NAME_MAX_LEN = 64

SESSION_PREVIEW_KEY = "import_preview_id"


def _templates(request: Request):
    return request.app.state.templates


def _raw_to_dict(rp: RawPosition) -> dict:
    return {
        "broker_ticker": rp.broker_ticker,
        "name": rp.name,
        "qty": str(rp.qty),
        "avg_price": str(rp.avg_price),
        "current_price": str(rp.current_price),
        "row_index": rp.row_index,
        "suggested_category": rp.suggested_category,
        # broker-csv-import-totals: round-trip the per-row totals so
        # the preview survives a navigation. ``None`` when the source
        # CSV did not publish the column — the import review modal
        # renders ``R$ 0,00`` for the row's "Total atual" cell and
        # the dashboard calc treats it as zero contribution.
        "total_invested": str(rp.total_invested) if rp.total_invested is not None else None,
        "total_current": str(rp.total_current) if rp.total_current is not None else None,
    }


def _dict_to_raw(d: dict) -> RawPosition:
    return RawPosition(
        broker_ticker=d["broker_ticker"],
        name=d["name"],
        qty=Decimal(d["qty"]),
        avg_price=Decimal(d["avg_price"]),
        current_price=Decimal(d["current_price"]),
        row_index=int(d["row_index"]),
        suggested_category=d.get("suggested_category"),
        # broker-csv-import-totals: rehydrate the totals (or ``None``)
        # from the JSON-serialized preview.
        total_invested=Decimal(d["total_invested"])
        if d.get("total_invested") is not None
        else None,
        total_current=Decimal(d["total_current"]) if d.get("total_current") is not None else None,
    )


def _existing_assets_for_profile(db, profile_id: int) -> list[Asset]:
    return (
        db.query(Asset)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .filter(AssetClass.profile_id == profile_id)
        .all()
    )


def _load_preview(db, profile_id: int, preview_id: int | None) -> ImportPreview | None:
    if preview_id is None:
        return None
    preview = db.get(ImportPreview, preview_id)
    if preview is None or preview.profile_id != profile_id:
        return None
    return preview


def _is_expired(preview: ImportPreview, now: datetime | None = None) -> bool:
    now = now or datetime.now(tz=UTC).replace(tzinfo=None)
    return (now - preview.created_at) > PREVIEW_TTL


@router.get("/import", response_class=HTMLResponse, response_model=None)
def get_import(
    request: Request,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Redirect to dashboard — the standalone upload form is retired.

    Import now lives in the dashboard modal (S04). Any direct request
    to /import bounces to the dashboard.
    """
    return RedirectResponse("/", status_code=302)


@router.post("/import", response_class=HTMLResponse, response_model=None)
async def post_import(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
    file: UploadFile = File(...),  # noqa: B008
) -> Response:
    """Parse the upload, persist a preview, redirect to /import/review."""
    blob = await file.read()
    if len(blob) > MAX_UPLOAD_BYTES:
        return _render_import_error(request, user, profile, "Arquivo excede 1 MB.")
    if not blob:
        return _render_import_error(request, user, profile, "Arquivo vazio.")
    try:
        text_data = blob.decode("utf-8")
    except UnicodeDecodeError:
        return _render_import_error(request, user, profile, "Arquivo precisa ser UTF-8.")
    try:
        raw = parse_positions(text_data)
    except Exception as exc:  # pragma: no cover - safety net
        logger.exception("parse_positions crashed: %s", exc)
        return _render_import_error(request, user, profile, "Falha ao processar o CSV.")
    if not raw:
        return _render_import_error(request, user, profile, "Nenhuma posição reconhecida no CSV.")

    raw_dicts = [_raw_to_dict(rp) for rp in raw]
    preview = ImportPreview(
        profile_id=profile.id,
        raw_json=json.dumps(raw_dicts, ensure_ascii=False),
    )
    db.add(preview)
    db.commit()
    db.refresh(preview)

    request.session[SESSION_PREVIEW_KEY] = preview.id
    return RedirectResponse("/import/review", status_code=303)


@router.get("/import/review", response_class=HTMLResponse, response_model=None)
def get_review(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Redirect to dashboard — the standalone review page is retired.

    Import review now lives in the dashboard modal (S04). Any direct
    request to /import/review bounces to the dashboard.
    """
    _ = (db, user, profile)  # keep the dependencies wired
    return RedirectResponse("/", status_code=302)


@router.post("/import/confirm", response_model=None)
async def post_confirm(
    request: Request,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Upsert Position rows for every row in the preview, then redirect."""
    preview_id = request.session.get(SESSION_PREVIEW_KEY)
    preview = _load_preview(db, profile.id, preview_id)
    if preview is None or _is_expired(preview):
        return RedirectResponse("/import", status_code=303)

    form = await request.form()
    class_ids = form.getlist("class_id[]")
    asset_names = form.getlist("asset_name[]")

    raw = [_dict_to_raw(d) for d in json.loads(preview.raw_json)]
    existing_assets = _existing_assets_for_profile(db, profile.id)
    result = match_positions(raw, existing_assets)

    upserted = 0

    # Auto-matched: the server is the source of truth. We commit
    # every (rp, asset_id) pair from match_positions() regardless
    # of the form payload — the hidden fields in the review form
    # are a UX affordance, not a security control.
    upsert_sql = (
        "INSERT INTO positions "
        "(asset_id, qty, avg_price, current_price, broker_ticker, "
        "total_invested, total_current, imported_at) "
        "VALUES "
        "(:asset_id, :qty, :avg_price, :current_price, :broker_ticker, "
        ":total_invested, :total_current, CURRENT_TIMESTAMP) "
        "ON CONFLICT(asset_id, broker_ticker) DO UPDATE SET "
        "qty = excluded.qty, avg_price = excluded.avg_price, "
        "current_price = excluded.current_price, "
        "total_invested = excluded.total_invested, "
        "total_current = excluded.total_current, "
        "imported_at = excluded.imported_at"
    )
    for rp, asset_id in result.auto_matched:
        db.execute(
            text(upsert_sql),
            {
                "asset_id": asset_id,
                "qty": str(rp.qty),
                "avg_price": str(rp.avg_price),
                "current_price": str(rp.current_price),
                "broker_ticker": rp.broker_ticker,
                # ``None`` → SQL NULL; the column is nullable and the
                # dashboard treats NULL as zero contribution.
                "total_invested": str(rp.total_invested) if rp.total_invested is not None else None,
                "total_current": str(rp.total_current) if rp.total_current is not None else None,
            },
        )
        upserted += 1

    # Unmatched: for each row whose class_id[] is non-empty, create
    # a new Asset (or reuse one with the same name in that class) and
    # insert a Position.
    for i, rp in enumerate(result.unmatched):
        if i >= len(class_ids) or i >= len(asset_names):
            continue
        try:
            class_id = int(class_ids[i])
        except (ValueError, TypeError):
            continue
        asset_name = (asset_names[i] or "").strip()
        if not asset_name:
            continue
        if len(asset_name) > NAME_MAX_LEN:
            continue
        # Validate the class belongs to this profile.
        target_class = (
            db.query(AssetClass)
            .filter(AssetClass.id == class_id, AssetClass.profile_id == profile.id)
            .one_or_none()
        )
        if target_class is None:
            continue
        # Reuse existing asset in that class with the same name if any.
        existing = (
            db.query(Asset)
            .filter(Asset.asset_class_id == target_class.id, Asset.name == asset_name)
            .one_or_none()
        )
        if existing is None:
            existing_assets_in_class = list(target_class.assets)
            next_order = (
                (existing_assets_in_class[-1].display_order + 1) if existing_assets_in_class else 0
            )
            new_asset = Asset(
                asset_class_id=target_class.id,
                name=asset_name,
                display_order=next_order,
            )
            db.add(new_asset)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                continue
            asset_id = new_asset.id
        else:
            asset_id = existing.id

        db.execute(
            text(upsert_sql),
            {
                "asset_id": asset_id,
                "qty": str(rp.qty),
                "avg_price": str(rp.avg_price),
                "current_price": str(rp.current_price),
                "broker_ticker": rp.broker_ticker,
                "total_invested": str(rp.total_invested) if rp.total_invested is not None else None,
                "total_current": str(rp.total_current) if rp.total_current is not None else None,
            },
        )
        upserted += 1

    db.delete(preview)
    db.commit()

    logger.info("import_confirm profile=%s upserted=%d", profile.id, upserted)
    return RedirectResponse("/", status_code=303)


def _render_import_error(request, user, profile, error: str) -> Response:
    return _templates(request).TemplateResponse(
        request,
        "import.html",
        {"user": user, "profile": profile, "error": error},
        status_code=200,
    )


# ---------------------------------------------------------------------------
# Pydantic models for JSON API
# ---------------------------------------------------------------------------


class AssignmentItem(BaseModel):
    """One user-assigned mapping from broker ticker to asset class.

    asset-trade-flags adds the three per-asset trade-control fields
    so the user can flip a flag in the import modal review and have
    it persist on commit. All three default to ``True / True /
    'BRL'`` when omitted (so a payload with only ``broker_ticker`` /
    ``class_id`` / ``asset_name`` keeps working as before).
    """

    broker_ticker: str
    class_id: int | None = None
    asset_name: str
    buy_enabled: bool = True
    sell_enabled: bool = True
    currency_code: str = "BRL"


class CommitRequest(BaseModel):
    """Request body for POST /api/import/commit."""

    preview_id: int
    assignments: list[AssignmentItem]


# ---------------------------------------------------------------------------
# Shared response builder
# ---------------------------------------------------------------------------


def _build_preview_response(
    db: Session,
    profile: Profile,
    preview: ImportPreview,
) -> dict:
    """Build the JSON response dict from an ImportPreview row.

    Re-runs match_positions() against current assets and queries
    current AssetClasses so the response is always fresh.

    asset-trade-flags: every row in ``auto_matched`` / ``unmatched``
    carries ``buy_enabled`` / ``sell_enabled`` / ``currency_code``.
    For auto-matched rows the value mirrors the existing Asset so a
    re-import preserves the user's prior toggle choices; for
    unmatched rows the value is the project default
    (``True / True / "BRL"``).
    """
    raw = [_dict_to_raw(d) for d in json.loads(preview.raw_json)]
    existing_assets = _existing_assets_for_profile(db, profile.id)
    result = match_positions(raw, existing_assets)

    class_rows = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )
    asset_classes = [
        {
            "id": ac.id,
            "name": ac.name,
            "color": _CLASS_COLORS[index % len(_CLASS_COLORS)],
        }
        for index, ac in enumerate(class_rows)
    ]

    asset_class_of: dict[int, int] = {}
    asset_by_id: dict[int, Asset] = {}
    for asset in existing_assets:
        asset_class_of[asset.id] = asset.asset_class_id
        asset_by_id[asset.id] = asset

    auto_matched = [
        {
            "broker_ticker": rp.broker_ticker,
            "name": rp.name,
            "qty": str(rp.qty),
            "avg_price": str(rp.avg_price),
            "current_price": str(rp.current_price),
            "asset_id": asset_id,
            "asset_class_id": asset_class_of.get(asset_id),
            # broker-csv-import-totals: surface the broker totals
            # so the import-modal review table renders the broker's
            # ``Total atual`` / ``Total investido`` directly — no JS
            # math, no recompute. ``None`` → 0 (CSV without totals
            # still gets a placeholder row in the review).
            "invested": str(rp.total_invested) if rp.total_invested is not None else "0",
            "current_value": str(rp.total_current) if rp.total_current is not None else "0",
            # asset-trade-flags: per-asset trade-control fields. The
            # auto_matched preview preserves the Asset's current
            # values so re-importing doesn't reset the operator's
            # prior toggle choices. Falls back to the project
            # defaults when the asset id is somehow absent (defensive
            # — should never happen in practice).
            "buy_enabled": asset_by_id[asset_id].buy_enabled,
            "sell_enabled": asset_by_id[asset_id].sell_enabled,
            "currency_code": asset_by_id[asset_id].currency_code,
        }
        for rp, asset_id in result.auto_matched
    ]

    unmatched = [
        {
            "broker_ticker": rp.broker_ticker,
            "name": rp.name,
            "qty": str(rp.qty),
            "avg_price": str(rp.avg_price),
            "current_price": str(rp.current_price),
            "suggested_category": rp.suggested_category,
            "suggested_class_id": suggest_class_id(rp.suggested_category, class_rows),
            "invested": str(rp.total_invested) if rp.total_invested is not None else "0",
            "current_value": str(rp.total_current) if rp.total_current is not None else "0",
            # asset-trade-flags: unmatched rows will be created at
            # commit time; preview them with the project defaults.
            "buy_enabled": True,
            "sell_enabled": True,
            "currency_code": "BRL",
        }
        for rp in result.unmatched
    ]

    return {
        "preview_id": preview.id,
        "auto_matched": auto_matched,
        "unmatched": unmatched,
        "asset_classes": asset_classes,
    }


# ---------------------------------------------------------------------------
# T01: POST /api/import/preview — parse CSV and return JSON preview
# ---------------------------------------------------------------------------


@router.post("/api/import/preview", response_model=None)
async def preview_import(
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
    file: UploadFile = File(...),
) -> Response:
    """Parse an uploaded CSV and return a JSON preview.

    Returns the same information as the HTML POST /import endpoint but
    as JSON, without setting the session cookie. The modal owns the
    preview_id in Alpine state.
    """
    blob = await file.read()
    if len(blob) > MAX_UPLOAD_BYTES:
        return JSONResponse({"detail": "Arquivo excede 1 MB."}, status_code=400)
    if not blob:
        return JSONResponse({"detail": "Arquivo vazio."}, status_code=400)
    try:
        text_data = blob.decode("utf-8")
    except UnicodeDecodeError:
        return JSONResponse({"detail": "Arquivo precisa ser UTF-8."}, status_code=400)
    try:
        raw = parse_positions(text_data)
    except Exception:  # pragma: no cover — safety net
        logger.exception("parse_positions crashed")
        return JSONResponse({"detail": "Falha ao processar o CSV."}, status_code=400)
    if not raw:
        return JSONResponse({"detail": "Nenhuma posicao reconhecida no CSV."}, status_code=400)

    raw_dicts = [_raw_to_dict(rp) for rp in raw]
    preview = ImportPreview(
        profile_id=profile.id,
        raw_json=json.dumps(raw_dicts, ensure_ascii=False),
    )
    db.add(preview)
    db.commit()
    db.refresh(preview)

    body = _build_preview_response(db, profile, preview)
    return JSONResponse(body, status_code=200)


# ---------------------------------------------------------------------------
# T02: POST /api/import/commit — commit a preview to assets + positions
# ---------------------------------------------------------------------------


@router.post("/api/import/commit", response_model=None)
def commit_import(
    body: CommitRequest,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Commit a preview: create Asset rows for unmatched, upsert Positions.

    Accepts JSON {"preview_id": int, "assignments": [{broker_ticker, class_id, asset_name}]}.
    Re-runs match_positions() to get auto_matched pairs, then for
    unmatched rows finds the matching assignment by broker_ticker,
    creates/reuses an Asset, and upserts a Position.
    Returns {"upserted": N, "created": M} on success.
    """
    preview = _load_preview(db, profile.id, body.preview_id)
    if preview is None or _is_expired(preview):
        raise HTTPException(status_code=400, detail="Preview expirado ou nao encontrado.")

    raw = [_dict_to_raw(d) for d in json.loads(preview.raw_json)]
    existing_assets = _existing_assets_for_profile(db, profile.id)
    result = match_positions(raw, existing_assets)

    # Build asset_id/class lookups for auto-matched rows.
    ticker_to_asset_id: dict[str, int] = {}
    ticker_to_original_class: dict[str, int] = {}
    for rp, asset_id in result.auto_matched:
        ticker_to_asset_id[rp.broker_ticker] = asset_id
    asset_class_of: dict[int, int] = {a.id: a.asset_class_id for a in existing_assets}
    ticker_to_original_class = {
        ticker: asset_class_of.get(aid) for ticker, aid in ticker_to_asset_id.items()
    }

    # Build assignment lookup from user input.
    assignment_map: dict[str, AssignmentItem] = {}
    for a in body.assignments:
        # asset-trade-flags: the trade-control fields are optional in
        # the wire format (the modal may pre-fill them from the
        # preview's current asset state, or let the operator override
        # before commit). Reject a ``currency_code`` outside the
        # allowlist so a hand-crafted body cannot bypass the DB CHECK.
        currency_code = a.currency_code.strip().upper() if a.currency_code else "BRL"
        if currency_code not in {"BRL", "USD"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"currency_code {a.currency_code!r} inválido. Use BRL ou USD.",
            )
        assignment_map[a.broker_ticker] = a.model_copy(update={"currency_code": currency_code})

    upsert_sql = (
        "INSERT INTO positions "
        "(asset_id, qty, avg_price, current_price, broker_ticker, "
        "total_invested, total_current, imported_at) "
        "VALUES "
        "(:asset_id, :qty, :avg_price, :current_price, :broker_ticker, "
        ":total_invested, :total_current, CURRENT_TIMESTAMP) "
        "ON CONFLICT(asset_id, broker_ticker) DO UPDATE SET "
        "qty = excluded.qty, avg_price = excluded.avg_price, "
        "current_price = excluded.current_price, "
        "total_invested = excluded.total_invested, "
        "total_current = excluded.total_current, "
        "imported_at = excluded.imported_at"
    )

    upserted = 0
    created = 0

    # Process ALL raw positions through the assignment map.
    # - Auto-matched without explicit assignment keeps original class.
    # - Auto-matched with assignment uses assigned class (possibly new).
    # - Unmatched rows without assignment or with empty class_id are skipped.
    for rp in raw:
        original_asset_id = ticker_to_asset_id.get(rp.broker_ticker)
        assignment = assignment_map.get(rp.broker_ticker)

        # Determine target class_id.
        if original_asset_id is not None and assignment is None:
            class_id = ticker_to_original_class.get(rp.broker_ticker)
        elif assignment is not None and assignment.class_id is not None:
            class_id = assignment.class_id
        else:
            continue

        if class_id is None:
            continue

        # Validate class ownership.
        target_class = (
            db.query(AssetClass)
            .filter(AssetClass.id == class_id, AssetClass.profile_id == profile.id)
            .one_or_none()
        )
        if target_class is None:
            continue

        # Determine asset name.
        if original_asset_id is not None and assignment is None:
            asset_name = rp.name
        elif assignment is not None:
            asset_name = assignment.asset_name.strip()
        else:
            continue

        if not asset_name or len(asset_name) > NAME_MAX_LEN:
            continue

        # Determine asset_id.
        if (
            original_asset_id is not None
            and ticker_to_original_class.get(rp.broker_ticker) == class_id
        ):
            asset_id = original_asset_id
            # asset-trade-flags: auto-matched row with no class move —
            # the asset already exists, so propagate the three
            # trade-control fields from the assignment onto the
            # existing row. The AssignmentItem defaults to
            # ``True / True / 'BRL'``; the modal pre-fills with the
            # current values from the preview, so the write is a
            # no-op for any field the operator didn't touch.
            existing_asset = db.get(Asset, asset_id)
            if existing_asset is not None and assignment is not None:
                existing_asset.buy_enabled = assignment.buy_enabled
                existing_asset.sell_enabled = assignment.sell_enabled
                existing_asset.currency_code = assignment.currency_code
        else:
            existing = (
                db.query(Asset)
                .filter(Asset.asset_class_id == target_class.id, Asset.name == asset_name)
                .one_or_none()
            )
            if existing is None:
                max_order = (
                    db.query(func.coalesce(func.max(Asset.display_order), -1))
                    .filter(Asset.asset_class_id == target_class.id)
                    .scalar()
                )
                # asset-trade-flags: brand-new asset. Pull the
                # trade-control fields off the assignment (the user
                # may have flipped a flag in the modal review).
                buy_enabled = True
                sell_enabled = True
                currency_code = "BRL"
                if assignment is not None:
                    buy_enabled = assignment.buy_enabled
                    sell_enabled = assignment.sell_enabled
                    currency_code = assignment.currency_code
                new_asset = Asset(
                    asset_class_id=target_class.id,
                    name=asset_name,
                    display_order=max_order + 1,
                    buy_enabled=buy_enabled,
                    sell_enabled=sell_enabled,
                    currency_code=currency_code,
                )
                db.add(new_asset)
                try:
                    db.flush()
                except IntegrityError:
                    db.rollback()
                    continue
                asset_id = new_asset.id
                created += 1
            else:
                asset_id = existing.id
                # asset-trade-flags: existing asset in the new class
                # — same propagation as the auto-matched branch above.
                if assignment is not None:
                    existing.buy_enabled = assignment.buy_enabled
                    existing.sell_enabled = assignment.sell_enabled
                    existing.currency_code = assignment.currency_code

        db.execute(
            text(upsert_sql),
            {
                "asset_id": asset_id,
                "qty": str(rp.qty),
                "avg_price": str(rp.avg_price),
                "current_price": str(rp.current_price),
                "broker_ticker": rp.broker_ticker,
                "total_invested": str(rp.total_invested) if rp.total_invested is not None else None,
                "total_current": str(rp.total_current) if rp.total_current is not None else None,
            },
        )
        upserted += 1

    db.delete(preview)
    db.commit()

    logger.info(
        "import_commit_api profile=%s upserted=%d created=%d", profile.id, upserted, created
    )
    return JSONResponse({"upserted": upserted, "created": created}, status_code=200)


# ---------------------------------------------------------------------------
# T02: GET /api/import/preview/{preview_id} — re-fetch a preview as JSON
# ---------------------------------------------------------------------------


@router.get("/api/import/preview/{preview_id}", response_model=None)
def get_preview(
    preview_id: int,
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Re-fetch a preview's data as JSON (same shape as POST /api/import/preview).

    Returns 404 if the preview is not found, expired, or does not belong
    to the active profile.
    """
    preview = _load_preview(db, profile.id, preview_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Preview nao encontrado.")
    if _is_expired(preview):
        raise HTTPException(status_code=404, detail="Preview expirado.")

    body = _build_preview_response(db, profile, preview)
    return JSONResponse(body, status_code=200)


__all__ = ["router"]
