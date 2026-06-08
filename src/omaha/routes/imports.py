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
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from omaha.auth import DbSession, require_active_profile, require_user
from omaha.csv_import import (
    RawPosition,
    match_positions,
    parse_positions,
    suggest_class_id,
)
from omaha.models import Asset, AssetClass, ImportPreview, Profile, User

router = APIRouter(tags=["imports"])

logger = logging.getLogger(__name__)

# 1 MB upload cap — broker statements are well under this, and a
# generous cap is friendlier than a tight one for the demo CSV.
MAX_UPLOAD_BYTES = 1 * 1024 * 1024

# A preview is "fresh" for this window. After 1h the review screen
# renders the "Expirado" state and forces the user to re-upload.
PREVIEW_TTL = timedelta(hours=1)

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
    }


def _dict_to_raw(d: dict) -> RawPosition:
    from decimal import Decimal

    return RawPosition(
        broker_ticker=d["broker_ticker"],
        name=d["name"],
        qty=Decimal(d["qty"]),
        avg_price=Decimal(d["avg_price"]),
        current_price=Decimal(d["current_price"]),
        row_index=int(d["row_index"]),
        suggested_category=d.get("suggested_category"),
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
    now = now or datetime.utcnow()
    return (now - preview.created_at) > PREVIEW_TTL


@router.get("/import", response_class=HTMLResponse, response_model=None)
def get_import(
    request: Request,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
) -> Response:
    """Render the upload form.

    The form posts back to the same URL with ``multipart/form-data``.
    """
    return _templates(request).TemplateResponse(
        request,
        "import.html",
        {"user": user, "profile": profile, "error": None},
    )


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
    """Render the matched/unmatched split. Re-runs the matcher against
    current assets (the preview may be slightly stale)."""
    preview_id = request.session.get(SESSION_PREVIEW_KEY)
    preview = _load_preview(db, profile.id, preview_id)
    if preview is None or _is_expired(preview):
        return _templates(request).TemplateResponse(
            request,
            "import_review.html",
            {
                "user": user,
                "profile": profile,
                "expired": True,
                "auto_matched": [],
                "unmatched": [],
                "auto_count": 0,
                "unmatched_count": 0,
                "asset_classes": [],
                "class_suggestions": {},
            },
        )

    raw = [_dict_to_raw(d) for d in json.loads(preview.raw_json)]
    existing_assets = _existing_assets_for_profile(db, profile.id)
    result = match_positions(raw, existing_assets)

    asset_classes = (
        db.query(AssetClass)
        .filter(AssetClass.profile_id == profile.id)
        .order_by(AssetClass.display_order)
        .all()
    )

    # Pre-select a class for each unmatched row based on the file's
    # "Minha Categoria" column. The user can still override via the
    # dropdown; the suggestion is a starting point, not a constraint.
    class_suggestions: dict[str, int] = {}
    for rp in result.unmatched:
        suggested = suggest_class_id(rp.suggested_category, asset_classes)
        if suggested is not None:
            class_suggestions[rp.broker_ticker] = suggested

    return _templates(request).TemplateResponse(
        request,
        "import_review.html",
        {
            "user": user,
            "profile": profile,
            "expired": False,
            "auto_matched": result.auto_matched,
            "unmatched": result.unmatched,
            "auto_count": len(result.auto_matched),
            "unmatched_count": len(result.unmatched),
            "asset_classes": asset_classes,
            "class_suggestions": class_suggestions,
        },
    )


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
        "(asset_id, qty, avg_price, current_price, broker_ticker, imported_at) "
        "VALUES "
        "(:asset_id, :qty, :avg_price, :current_price, :broker_ticker, CURRENT_TIMESTAMP) "
        "ON CONFLICT(asset_id, broker_ticker) DO UPDATE SET "
        "qty = excluded.qty, avg_price = excluded.avg_price, "
        "current_price = excluded.current_price, imported_at = excluded.imported_at"
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
            },
        )
        upserted += 1

    db.delete(preview)
    db.commit()

    request.session.pop(SESSION_PREVIEW_KEY, None)
    logger.info("import_confirm profile=%s upserted=%d", profile.id, upserted)
    return RedirectResponse("/", status_code=303)


def _render_import_error(request, user, profile, error: str) -> Response:
    return _templates(request).TemplateResponse(
        request,
        "import.html",
        {"user": user, "profile": profile, "error": error},
        status_code=200,
    )


__all__ = ["router"]
