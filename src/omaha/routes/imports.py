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
import re
import shutil
import tempfile
import threading
import time
import unicodedata
import uuid
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
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

from omaha.auth import (
    DbSession,
    HouseholdReadOnlyError,
    require_active_profile,
    require_profile_writable,
    require_user,
)
from omaha.config import settings
from omaha.csv_import import (
    RawPosition,
    match_positions,
    normalize_name,
    parse_positions,
    suggest_class_id,
)
from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, ImportPreview, MyProfitSyncJob, Position, Profile, User
from omaha.mutation_guards import (
    record_mutation_audit,
    snapshot_before_destructive,
    snapshot_counts,
)
from omaha.myprofit.connector import MyProfitConnector, MyProfitConnectorError, MyProfitCsvDownload
from omaha.myprofit.telemetry import (
    elapsed_ms,
    emit_stage,
    emit_terminal,
    emit_transition,
    emit_ui_limit,
    telemetry_context,
)
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
TERMINAL_DEDUP_LIMIT = 4096

SYNC_ERROR_MESSAGES = {
    "credentials": "Não foi possível acessar as credenciais do MyProfit.",
    "login": "Não foi possível entrar no MyProfit.",
    "two_factor": "A autenticação do MyProfit não foi concluída.",
    "download": "Não foi possível baixar o CSV do MyProfit.",
    "preview": "Não foi possível preparar o CSV para revisão.",
    "connector": "Não foi possível sincronizar com o MyProfit.",
}


class PreviewBlobError(ValueError):
    """Sanitized failure while converting CSV bytes into an ImportPreview."""

    def __init__(self, code: str, message: str) -> None:
        self.stage = "preview"
        self.code = code
        self.message = message
        super().__init__(code)


class SyncInProgress(RuntimeError):
    """A real profile already owns a queued or running synchronization."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__("sync_in_progress")


def _safe_error_message(stage: str | None) -> str:
    safe_stage = MyProfitSyncJob.safe_error_stage(stage)
    return SYNC_ERROR_MESSAGES.get(safe_stage, SYNC_ERROR_MESSAGES["connector"])


def _utcnow() -> datetime:
    return datetime.now(tz=UTC).replace(tzinfo=None)


def _job_duration_ms(job: MyProfitSyncJob) -> int:
    if job.created_at is None or job.finished_at is None:
        return 0
    return max(0, int((job.finished_at - job.created_at).total_seconds() * 1000))


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "export.csv").name
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name).strip("._")
    if not name:
        return "export.csv"
    if len(name) > 128:
        name = name[:128]
    return name


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


def _preview_rows_and_baseline(raw_json: str) -> tuple[list[dict], list[dict] | None]:
    """Read both legacy raw-list previews and F65 baseline envelopes."""
    payload = json.loads(raw_json)
    if isinstance(payload, list):
        return payload, None
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        baseline = payload.get("baseline")
        return payload["rows"], baseline if isinstance(baseline, list) else None
    raise ValueError("Formato de preview inválido.")


def _existing_assets_for_profile(db, profile_id: int) -> list[Asset]:
    return (
        db.query(Asset)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .filter(AssetClass.profile_id == profile_id)
        .all()
    )


def _capture_preview_baseline(db: Session, profile_id: int, raw: list[RawPosition]) -> list[dict]:
    """Capture profile-scoped Asset/Position state before preview review."""
    existing_assets = _existing_assets_for_profile(db, profile_id)
    match = match_positions(raw, existing_assets)
    asset_by_id = {asset.id: asset for asset in existing_assets}
    matched_asset_by_row = {
        id(raw_position): asset_by_id[asset_id] for raw_position, asset_id in match.auto_matched
    }
    asset_ids = list(asset_by_id)
    positions = (
        db.query(Position).filter(Position.asset_id.in_(asset_ids)).all() if asset_ids else []
    )
    position_by_key = {
        (position.asset_id, position.broker_ticker): position for position in positions
    }

    baseline: list[dict] = []
    for raw_position in raw:
        asset = matched_asset_by_row.get(id(raw_position))
        position = (
            position_by_key.get((asset.id, raw_position.broker_ticker))
            if asset is not None
            else None
        )
        baseline.append(
            {
                "asset_id": asset.id if asset is not None else None,
                "asset_class_id": asset.asset_class_id if asset is not None else None,
                "asset": (
                    {
                        "name": asset.name,
                        "buy_enabled": asset.buy_enabled,
                        "sell_enabled": asset.sell_enabled,
                        "currency_code": asset.currency_code,
                    }
                    if asset is not None
                    else None
                ),
                "position": (
                    {
                        "qty": str(position.qty),
                        "avg_price": str(position.avg_price),
                        "current_price": str(position.current_price),
                        "total_invested": (
                            str(position.total_invested)
                            if position.total_invested is not None
                            else None
                        ),
                        "total_current": (
                            str(position.total_current)
                            if position.total_current is not None
                            else None
                        ),
                    }
                    if position is not None
                    else None
                ),
            }
        )
    return baseline


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


def preview_from_blob(db: Session, profile: Profile, blob: bytes) -> ImportPreview:
    """Parse bytes and persist one profile-scoped review preview.

    Manual upload and background sync share this boundary. It never mutates
    portfolio rows and never invokes the commit route.
    """
    if len(blob) > MAX_UPLOAD_BYTES:
        raise PreviewBlobError("file_too_large", "Arquivo excede 1 MB.")
    if not blob:
        raise PreviewBlobError("empty_file", "Arquivo vazio.")
    try:
        text_data = blob.decode("utf-8")
    except UnicodeDecodeError:
        raise PreviewBlobError("invalid_utf8", "Arquivo precisa ser UTF-8.") from None
    try:
        raw = parse_positions(text_data)
    except Exception:
        raise PreviewBlobError("parse_failed", "Falha ao processar o CSV.") from None
    if not raw:
        raise PreviewBlobError("no_positions", "Nenhuma posicao reconhecida no CSV.")

    baseline = _capture_preview_baseline(db, profile.id, raw)
    preview = ImportPreview(
        profile_id=profile.id,
        raw_json=json.dumps(
            {"rows": [_raw_to_dict(rp) for rp in raw], "baseline": baseline},
            ensure_ascii=False,
        ),
    )
    db.add(preview)
    db.commit()
    db.refresh(preview)
    return preview


class MyProfitSyncService:
    """Single-process, profile-isolated background synchronization boundary."""

    def __init__(
        self,
        *,
        connector: MyProfitConnector | None = None,
        session_factory=SessionLocal,
        temp_root: str | Path | None = None,
        max_workers: int = 2,
    ) -> None:
        self.connector = connector
        self.session_factory = session_factory
        self.temp_root = Path(temp_root) if temp_root is not None else None
        self._lock = threading.RLock()
        self._worker_slots = threading.BoundedSemaphore(max_workers)
        self._max_workers = max_workers
        self._active_workers = 0
        self._reservations: dict[int, str] = {}
        self._owned_dirs: dict[str, Path] = {}
        self._ui_limit_observed: set[str] = set()
        # Keep duplicate protection bounded while allowing every new terminal
        # settlement to emit. Lifecycle guards prevent normal late
        # worker/expiry races from settling the same job twice.
        self._terminal_observed: OrderedDict[str, None] = OrderedDict()
        self._stopping = False

    def start(
        self, db: Session, profile: Profile, background_tasks: BackgroundTasks
    ) -> MyProfitSyncJob:
        """Create queued row and hand execution to FastAPI BackgroundTasks."""
        with self._lock:
            if self._stopping:
                self._stopping = False
            active_id = self._reservations.get(profile.id)
            if active_id is not None:
                emit_stage(
                    active_id,
                    domain="concurrency",
                    status="rejected",
                    stage="concurrency",
                    code="sync_in_progress",
                    duration_ms=0,
                )
                raise SyncInProgress(active_id)
            existing = (
                db.query(MyProfitSyncJob)
                .filter(
                    MyProfitSyncJob.profile_id == profile.id,
                    MyProfitSyncJob.status.in_(MyProfitSyncJob.ACTIVE_STATUSES),
                )
                .order_by(MyProfitSyncJob.created_at.desc())
                .first()
            )
            self.prune_expired_jobs(db, profile_id=profile.id)
            if existing is not None and _utcnow() >= existing.expires_at:
                self.expire_myprofit_sync_job(existing.job_id, db=db)
                existing = None
            if existing is not None:
                self._reservations[profile.id] = existing.job_id
                emit_stage(
                    existing.job_id,
                    domain="concurrency",
                    status="rejected",
                    stage="concurrency",
                    code="sync_in_progress",
                    duration_ms=0,
                )
                raise SyncInProgress(existing.job_id)

            now = _utcnow()
            job = MyProfitSyncJob(
                job_id=str(uuid.uuid4()),
                profile_id=profile.id,
                status="queued",
                expires_at=now + timedelta(seconds=settings.PREVIEW_TTL_SECONDS),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            self._reservations[profile.id] = job.job_id
            emit_transition(job.job_id, status="queued", stage="queue", code="started")
            background_tasks.add_task(self.run_myprofit_sync_job, job.job_id, profile.id)
            return job

    def _cleanup_owned_dir(self, job: MyProfitSyncJob) -> bool:
        with self._lock:
            raw_path = self._owned_dirs.get(job.job_id)
            if raw_path is None and job.work_dir:
                raw_path = Path(job.work_dir)
        if raw_path is None:
            return True
        try:
            if raw_path.exists():
                shutil.rmtree(raw_path)
            with self._lock:
                self._owned_dirs.pop(job.job_id, None)
            return True
        except OSError:
            return False

    def _clear_reservation(self, profile_id: int, job_id: str) -> None:
        with self._lock:
            if self._reservations.get(profile_id) == job_id:
                self._reservations.pop(profile_id, None)

    def _mark_failed(
        self,
        db: Session,
        job: MyProfitSyncJob,
        *,
        stage: str,
        code: str,
        telemetry_stage_recorded: bool = False,
    ) -> None:
        db.refresh(job)
        if job.status == "expired" or _utcnow() >= job.expires_at:
            self.expire_myprofit_sync_job(job.job_id, db=db)
            return
        if job.preview_id is not None:
            preview = db.get(ImportPreview, job.preview_id)
            if preview is not None:
                db.delete(preview)
        job.preview_id = None
        job.status = "failed"
        job.error_stage, job.error_code = MyProfitSyncJob.normalize_error(stage, code)
        job.finished_at = _utcnow()
        job.retention_until = job.finished_at + PREVIEW_TTL
        db.commit()
        self._clear_ui_limit_observation(job.job_id)
        if not telemetry_stage_recorded:
            emit_stage(
                job.job_id,
                domain="preview_handoff" if stage == "preview" else "connector",
                status="failed",
                stage=stage,
                code=code,
                duration_ms=0,
            )
        emit_transition(job.job_id, status="failed", stage=stage, code="transitioned")
        self._emit_terminal_once(job, status="failed", code=MyProfitSyncJob.safe_error_code(code))

    @property
    def active_worker_count(self) -> int:
        """Return current worker count for internal health/contract checks."""
        with self._lock:
            return self._active_workers

    def _process_downloaded_csv(
        self,
        db: Session,
        job: MyProfitSyncJob,
        profile: Profile,
        *,
        filename: str,
        content: bytes,
    ) -> None:
        """Persist one downloaded blob through the existing preview boundary.

        Connector invocation stays in :meth:`run_myprofit_sync_job`; this
        internal handoff keeps byte-to-preview behavior directly testable
        without constructing a connector, browser, credential, or network
        dependency.
        """
        db.refresh(job)
        if _utcnow() >= job.expires_at or job.status != "running":
            self.expire_myprofit_sync_job(job.job_id, db=db)
            return

        job_dir = Path(
            tempfile.mkdtemp(
                prefix=f"omaha-myprofit-sync-{job.job_id}-",
                dir=str(self.temp_root) if self.temp_root is not None else None,
            )
        )
        with self._lock:
            self._owned_dirs[job.job_id] = job_dir
        safe_name = _safe_filename(filename)
        work_file = job_dir / safe_name
        job.work_dir = str(job_dir)
        job.work_file = str(work_file)
        job.filename = safe_name
        db.commit()

        work_file.write_bytes(content)
        if _utcnow() >= job.expires_at:
            self.expire_myprofit_sync_job(job.job_id, db=db)
            return

        stage_started = time.perf_counter()
        try:
            preview = preview_from_blob(db, profile, work_file.read_bytes())
        except PreviewBlobError as exc:
            emit_stage(
                job.job_id,
                domain="preview_handoff",
                status="failed",
                stage=exc.stage,
                code="unknown",
                duration_ms=elapsed_ms(stage_started),
            )
            self._mark_failed(
                db, job, stage=exc.stage, code=exc.code, telemetry_stage_recorded=True
            )
            return

        db.refresh(job)
        if _utcnow() >= job.expires_at or job.status != "running":
            db.delete(preview)
            db.commit()
            self.expire_myprofit_sync_job(job.job_id, db=db)
            return
        job.preview_id = preview.id
        job.status = "succeeded"
        job.finished_at = _utcnow()
        job.retention_until = job.finished_at + PREVIEW_TTL
        job.error_stage = None
        job.error_code = None
        db.commit()
        emit_stage(
            job.job_id,
            domain="preview_handoff",
            status="succeeded",
            stage="handoff",
            code="success",
            duration_ms=elapsed_ms(stage_started),
        )
        emit_transition(job.job_id, status="succeeded", stage="handoff", code="transitioned")
        self._clear_ui_limit_observation(job.job_id)
        self._emit_terminal_once(job, status="succeeded", code="success")

    def _clear_ui_limit_observation(self, job_id: str) -> None:
        with self._lock:
            self._ui_limit_observed.discard(job_id)

    def _emit_terminal_once(self, job: MyProfitSyncJob, *, status: str, code: str) -> None:
        with self._lock:
            if job.job_id in self._terminal_observed:
                return
            self._terminal_observed[job.job_id] = None
            self._terminal_observed.move_to_end(job.job_id)
            if len(self._terminal_observed) > TERMINAL_DEDUP_LIMIT:
                self._terminal_observed.popitem(last=False)
        emit_terminal(
            job.job_id,
            status=status,
            code=code,
            total_duration_ms=_job_duration_ms(job),
        )

    def observe_ui_limit(self, db: Session, profile: Profile, job_id: str) -> bool:
        """Record one owned browser-limit observation without changing DB state."""
        with self._lock:
            if job_id in self._ui_limit_observed:
                return False
            job = db.get(MyProfitSyncJob, job_id)
            if job is None or job.profile_id != profile.id:
                return False
            if job.status not in MyProfitSyncJob.ACTIVE_STATUSES:
                return False
            self._ui_limit_observed.add(job_id)
        emit_ui_limit(job_id, status=job.status)
        return True

    def run_myprofit_sync_job(self, job_id: str, profile_id: int) -> None:
        """Execute one job using an independent DB session and owned path."""
        acquired = self._worker_slots.acquire()
        if not acquired:  # pragma: no cover - BoundedSemaphore.acquire blocks
            return
        db = self.session_factory()
        job: MyProfitSyncJob | None = None
        with self._lock:
            self._active_workers += 1
        try:
            job = db.get(MyProfitSyncJob, job_id)
            profile = db.get(Profile, profile_id)
            if job is None or profile is None or job.profile_id != profile_id:
                return
            now = _utcnow()
            if job.status != "queued" or now >= job.expires_at:
                if job.status in MyProfitSyncJob.ACTIVE_STATUSES:
                    self.expire_myprofit_sync_job(job_id, db=db)
                return
            job.status = "running"
            job.started_at = now
            db.commit()

            emit_transition(job.job_id, status="running", stage="queue", code="transitioned")
            with telemetry_context(job_id, started_at=time.perf_counter()):
                if profile.is_family_sentinel:
                    self._mark_failed(db, job, stage="credentials", code="household_read_only")
                    return

                connector = self.connector
                if connector is None:
                    from omaha.myprofit.connector import PlaywrightMyProfitConnector

                    connector = PlaywrightMyProfitConnector()
                try:
                    downloaded: MyProfitCsvDownload = connector.download_positions_csv(profile)
                    self._process_downloaded_csv(
                        db,
                        job,
                        profile,
                        filename=downloaded.filename,
                        content=downloaded.content,
                    )
                except MyProfitConnectorError as exc:
                    self._mark_failed(
                        db, job, stage=exc.stage, code=exc.code, telemetry_stage_recorded=True
                    )
                    return
                except (OSError, ValueError, TypeError, AttributeError):
                    self._mark_failed(db, job, stage="download", code="file_failed")
                    return

            return
        except Exception:
            # No exception text is persisted or emitted: status is a safe
            # connector failure, never a credential/path/raw CSV channel.
            if job is not None and db.get(MyProfitSyncJob, job_id) is not None:
                self._mark_failed(db, job, stage="connector", code="failed")
        finally:
            if job is not None:
                cleaned = self._cleanup_owned_dir(job)
                if cleaned:
                    try:
                        current = db.get(MyProfitSyncJob, job_id)
                        if current is not None:
                            current.work_dir = None
                            current.work_file = None
                            db.commit()
                    except Exception:
                        db.rollback()
            self._clear_reservation(profile_id, job_id)
            db.close()
            with self._lock:
                self._active_workers -= 1
            self._worker_slots.release()

    def expire_myprofit_sync_job(self, job_id: str, *, db: Session | None = None) -> bool:
        """Expire one owned job and remove only its linked preview/path."""
        owns_db = db is None
        session = db or self.session_factory()
        try:
            with self._lock:
                job = session.get(MyProfitSyncJob, job_id)
                if job is None:
                    return False
                if job.status == "expired":
                    if job.retention_until is None:
                        job.finished_at = job.finished_at or _utcnow()
                        job.retention_until = job.finished_at + PREVIEW_TTL
                    self._cleanup_owned_dir(job)
                    session.commit()
                    return True
                if job.status not in {"queued", "running", "succeeded"}:
                    return False
                if _utcnow() < job.expires_at:
                    return False
                if job.preview_id is not None:
                    preview = session.get(ImportPreview, job.preview_id)
                    if preview is not None:
                        session.delete(preview)
                job.preview_id = None
                job.status = "expired"
                job.finished_at = _utcnow()
                job.retention_until = job.finished_at + PREVIEW_TTL
                job.work_dir = None if self._cleanup_owned_dir(job) else job.work_dir
                job.work_file = None if job.work_dir is None else job.work_file
                session.commit()
                self._clear_reservation(job.profile_id, job.job_id)
                self._clear_ui_limit_observation(job.job_id)
                emit_transition(job.job_id, status="expired", stage="terminal", code="transitioned")
                self._emit_terminal_once(job, status="expired", code="unknown")
                return True
        finally:
            if owns_db:
                session.close()

    def prune_expired_jobs(
        self,
        db: Session,
        *,
        profile_id: int,
        now: datetime | None = None,
        limit: int = 100,
    ) -> int:
        """Prune bounded F59 terminal rows after their retention deadline."""
        now = now or _utcnow()
        jobs = (
            db.query(MyProfitSyncJob)
            .filter(
                MyProfitSyncJob.profile_id == profile_id,
                MyProfitSyncJob.status.in_({"failed", "succeeded", "expired"}),
                MyProfitSyncJob.retention_until.is_not(None),
                MyProfitSyncJob.retention_until <= now,
            )
            .order_by(MyProfitSyncJob.retention_until.asc())
            .limit(max(0, limit))
            .all()
        )
        pruned = 0
        for job in jobs:
            if not self._cleanup_owned_dir(job):
                continue
            if job.preview_id is not None:
                preview = db.get(ImportPreview, job.preview_id)
                if preview is not None and preview.profile_id == job.profile_id:
                    db.delete(preview)
            db.delete(job)
            pruned += 1
        if pruned:
            db.commit()
        return pruned

    def status_for_profile(self, db: Session, profile: Profile, job_id: str) -> dict | None:
        """Return status only when job belongs to active real profile."""
        with self._lock:
            job = db.get(MyProfitSyncJob, job_id)
            if job is None or job.profile_id != profile.id:
                return None
            if job.status in {"queued", "running", "succeeded"} and _utcnow() >= job.expires_at:
                self.expire_myprofit_sync_job(job_id, db=db)
                job = db.get(MyProfitSyncJob, job_id)
                if job is None:
                    return None
            preview_body = None
            if job.status == "succeeded" and job.preview_id is not None:
                preview = _load_preview(db, profile.id, job.preview_id)
                if preview is None or _is_expired(preview):
                    self.expire_myprofit_sync_job(job_id, db=db)
                    job = db.get(MyProfitSyncJob, job_id)
                else:
                    preview_body = _build_preview_response(db, profile, preview)
            return job.to_status_dict(
                preview=preview_body,
                error_message=_safe_error_message(job.error_stage),
            )

    def latest_page_error(self, db: Session, profile_id: int) -> dict | None:
        job = (
            db.query(MyProfitSyncJob)
            .filter(
                MyProfitSyncJob.profile_id == profile_id,
                MyProfitSyncJob.status.in_({"failed", "expired"}),
            )
            .order_by(MyProfitSyncJob.created_at.desc())
            .first()
        )
        if job is None:
            return None
        return job.to_status_dict(error_message=_safe_error_message(job.error_stage))

    def shutdown(self) -> None:
        """Settle owned jobs and clean only paths registered by this service."""
        with self._lock:
            self._stopping = True
            reservations = list(self._reservations.values())
            owned = list(self._owned_dirs.items())
        db = self.session_factory()
        try:
            for job_id in dict.fromkeys(reservations):
                job = db.get(MyProfitSyncJob, job_id)
                if job is None or job.status not in MyProfitSyncJob.ACTIVE_STATUSES:
                    continue
                if job.preview_id is not None:
                    preview = db.get(ImportPreview, job.preview_id)
                    if preview is not None and preview.profile_id == job.profile_id:
                        db.delete(preview)
                job.preview_id = None
                job.status = "expired"
                job.finished_at = _utcnow()
                job.retention_until = job.finished_at + PREVIEW_TTL
                cleaned = self._cleanup_owned_dir(job)
                if cleaned:
                    job.work_dir = None
                    job.work_file = None
                db.commit()
                self._clear_ui_limit_observation(job.job_id)
                emit_transition(job.job_id, status="expired", stage="terminal", code="transitioned")
                self._emit_terminal_once(job, status="expired", code="unknown")
            with self._lock:
                self._reservations.clear()
            for job_id, path in owned:
                try:
                    if path.exists():
                        shutil.rmtree(path)
                except OSError:
                    continue
                with self._lock:
                    self._owned_dirs.pop(job_id, None)
        finally:
            db.close()


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
    _writable: None = Depends(require_profile_writable),
    file: UploadFile = File(...),  # noqa: B008
) -> Response:
    """Parse the upload, persist a preview, redirect to /import/review."""
    blob = await file.read()
    try:
        preview = preview_from_blob(db, profile, blob)
    except PreviewBlobError as exc:
        return _render_import_error(request, user, profile, exc.message)

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
    _writable: None = Depends(require_profile_writable),
) -> Response:
    """Upsert Position rows for every row in the preview, then redirect."""
    preview_id = request.session.get(SESSION_PREVIEW_KEY)
    preview = _load_preview(db, profile.id, preview_id)
    if preview is None or _is_expired(preview):
        return RedirectResponse("/import", status_code=303)

    form = await request.form()
    class_ids = form.getlist("class_id[]")
    asset_names = form.getlist("asset_name[]")

    raw_rows, _ = _preview_rows_and_baseline(preview.raw_json)
    raw = [_dict_to_raw(d) for d in raw_rows]
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


def _require_sync_profile(
    request: Request, db: DbSession, user: User = Depends(require_user)
) -> Profile:
    """Resolve active profile, rejecting Família before job lookup/side effects."""
    profile_id = request.session.get("active_profile_id")
    profile = db.get(Profile, profile_id) if profile_id is not None else None
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if profile.is_family_sentinel:
        raise HouseholdReadOnlyError()
    return profile


@router.post("/api/myprofit/sync", response_model=None)
def start_myprofit_sync(
    background_tasks: BackgroundTasks,
    db: DbSession,
    request: Request,
    profile: Profile = Depends(_require_sync_profile),
    _writable: None = Depends(require_profile_writable),
) -> Response:
    """Queue one profile-isolated MyProfit synchronization."""
    service = request.app.state.myprofit_sync_service
    try:
        job = service.start(db, profile, background_tasks)
    except SyncInProgress as exc:
        return JSONResponse(
            {"reason": "sync_in_progress", "code": "sync_in_progress", "job_id": exc.job_id},
            status_code=status.HTTP_409_CONFLICT,
        )
    return JSONResponse({"job_id": job.job_id, "status": job.status}, status_code=202)


@router.get("/api/myprofit/sync/{job_id}", response_model=None)
def get_myprofit_sync_status(
    job_id: str,
    db: DbSession,
    request: Request,
    profile: Profile = Depends(_require_sync_profile),
    _writable: None = Depends(require_profile_writable),
) -> Response:
    """Poll one job without disclosing jobs owned by another profile."""
    payload = request.app.state.myprofit_sync_service.status_for_profile(db, profile, job_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(payload, status_code=200)


@router.post("/api/myprofit/sync/{job_id}/ui-limit", response_model=None)
def observe_myprofit_sync_ui_limit(
    job_id: str,
    db: DbSession,
    request: Request,
    profile: Profile = Depends(_require_sync_profile),
    _writable: None = Depends(require_profile_writable),
) -> Response:
    """Accept one fixed, owned browser local-limit observation."""
    service = request.app.state.myprofit_sync_service
    if service.observe_ui_limit(db, profile, job_id):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    job = db.get(MyProfitSyncJob, job_id)
    if job is None or job.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


_TRIAGE_POSITION_FIELDS = (
    ("qty", "Qtde", "unidades"),
    ("avg_price", "Preço médio", "R$"),
    ("current_price", "Preço atual", "R$"),
    ("total_invested", "Total investido", "R$"),
    ("total_current", "Total atual", "R$"),
)


def _sort_text(value: str | None) -> str:
    text_value = (value or "").strip()
    return unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode().casefold()


def _triage_sort_key(row: dict) -> tuple:
    name = row.get("name")
    ticker = row.get("broker_ticker")
    return (
        1 if not (name or "").strip() else 0,
        _sort_text(name),
        _sort_text(ticker),
        name or "",
        ticker or "",
    )


def _position_value(value: object) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _diff_display(
    field_id: str,
    value: object,
    *,
    missing_position: bool = False,
    asset_name: str | None = None,
) -> str:
    if value is None:
        return "Não havia posição" if missing_position else "Não disponível"
    if field_id == "asset.name":
        return str(value).strip()
    if field_id == "qty":
        decimals = 3 if (asset_name or "").strip().upper() == "BTC" else 1
        amount = Decimal(str(value)).quantize(Decimal(1).scaleb(-decimals))
        return f"{amount:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if field_id in {"avg_price", "current_price", "total_invested", "total_current"}:
        amount = Decimal(str(value)).quantize(Decimal("1"))
        sign = "-" if amount < 0 else ""
        return f"{sign}R$ {abs(amount):,.0f}".replace(",", ".")
    return str(value)


def _changed_field(
    field_id: str,
    label: str,
    unit: str,
    incoming: object,
    previous: object,
    *,
    missing_position: bool = False,
    asset_name: str | None = None,
) -> dict:
    if field_id.startswith("asset.") or incoming is None or previous is None:
        sign = "not-applicable"
    else:
        incoming_decimal = _position_value(incoming)
        previous_decimal = _position_value(previous)
        if incoming_decimal is None or previous_decimal is None:
            sign = "not-applicable"
        elif incoming_decimal > previous_decimal:
            sign = "positive"
        elif incoming_decimal < previous_decimal:
            sign = "negative"
        else:
            sign = "zero"
    incoming_value = str(incoming) if incoming is not None else None
    previous_value = str(previous) if previous is not None else None
    return {
        "id": field_id,
        "field": field_id,
        "label": label,
        "unit": unit,
        "sign": sign,
        "incoming": incoming_value,
        "incoming_value": incoming_value,
        "incoming_display": _diff_display(field_id, incoming, asset_name=asset_name),
        "previous": previous_value,
        "previous_value": previous_value,
        "previous_display": _diff_display(
            field_id,
            previous,
            missing_position=missing_position,
            asset_name=asset_name,
        ),
    }


def _build_changed_fields(rp: RawPosition, baseline: dict) -> list[dict]:
    fields: list[dict] = []
    baseline_asset = baseline.get("asset")
    if baseline_asset is not None:
        incoming_name = rp.name.strip()
        previous_name = str(baseline_asset.get("name", "")).strip()
        if incoming_name != previous_name:
            fields.append(
                _changed_field("asset.name", "Nome", "texto", incoming_name, previous_name)
            )

    baseline_position = baseline.get("position")
    for field_id, label, unit in _TRIAGE_POSITION_FIELDS:
        incoming = getattr(rp, field_id)
        previous = baseline_position.get(field_id) if baseline_position is not None else None
        if baseline_position is None or _position_value(incoming) != _position_value(previous):
            fields.append(
                _changed_field(
                    field_id,
                    label,
                    unit,
                    incoming,
                    _position_value(previous),
                    missing_position=baseline_position is None,
                    asset_name=rp.name,
                )
            )
    return fields


def _build_absent_rows(
    db: Session,
    existing_assets: list[Asset],
    incoming_asset_names: set[str],
    class_name_by_id: dict[int, str],
) -> list[dict]:
    """Serialize profile assets whose normalized names are absent from preview."""
    asset_by_id = {asset.id: asset for asset in existing_assets}
    positions = (
        db.query(Position).filter(Position.asset_id.in_(asset_by_id)).all() if asset_by_id else []
    )
    positions_by_asset: dict[int, list[Position]] = {}
    for position in positions:
        positions_by_asset.setdefault(position.asset_id, []).append(position)

    rows: list[dict] = []
    for asset in existing_assets:
        if normalize_name(asset.name) in incoming_asset_names:
            continue
        asset_positions = positions_by_asset.get(asset.id) or [None]
        for position in asset_positions:
            rows.append(
                {
                    "broker_ticker": position.broker_ticker if position is not None else "",
                    "name": asset.name,
                    "qty": str(position.qty) if position is not None else "0",
                    "avg_price": str(position.avg_price) if position is not None else "0",
                    "current_price": str(position.current_price) if position is not None else "0",
                    "invested": (
                        str(position.total_invested)
                        if position is not None and position.total_invested is not None
                        else "0"
                    ),
                    "current_value": (
                        str(position.total_current)
                        if position is not None and position.total_current is not None
                        else "0"
                    ),
                    "asset_id": asset.id,
                    "asset_class_id": asset.asset_class_id,
                    "asset_class_name": class_name_by_id.get(asset.asset_class_id, ""),
                    "buy_enabled": asset.buy_enabled,
                    "sell_enabled": asset.sell_enabled,
                    "currency_code": asset.currency_code,
                    "state": "absent",
                    "changed_fields": [],
                    "read_only": True,
                    "committable": False,
                }
            )
    rows.sort(key=_triage_sort_key)
    return rows


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
    raw_rows, persisted_baseline = _preview_rows_and_baseline(preview.raw_json)
    raw = [_dict_to_raw(d) for d in raw_rows]
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

    compatibility_by_row: dict[int, dict] = {}
    for (rp, _), row in zip(result.auto_matched, auto_matched, strict=True):
        compatibility_by_row[id(rp)] = row
    for rp, row in zip(result.unmatched, unmatched, strict=True):
        compatibility_by_row[id(rp)] = row

    baseline = persisted_baseline
    if not isinstance(baseline, list) or len(baseline) != len(raw):
        baseline = _capture_preview_baseline(db, profile.id, raw)

    triage = {"new": [], "changed": [], "unchanged": [], "absent": []}
    for index, rp in enumerate(raw):
        row = dict(compatibility_by_row[id(rp)])
        baseline_row = baseline[index]
        has_asset = baseline_row.get("asset_id") is not None
        changed_fields = _build_changed_fields(rp, baseline_row) if has_asset else []
        state = "new" if not has_asset else ("changed" if changed_fields else "unchanged")
        row["state"] = state
        row["changed_fields"] = changed_fields
        triage[state].append(row)

    for group in triage.values():
        group.sort(key=_triage_sort_key)

    triage["absent"] = _build_absent_rows(
        db,
        existing_assets,
        {normalize_name(raw_position.name) for raw_position in raw},
        {ac.id: ac.name for ac in class_rows},
    )

    return {
        "preview_id": preview.id,
        "auto_matched": auto_matched,
        "unmatched": unmatched,
        "asset_classes": asset_classes,
        "triage": triage,
    }


# ---------------------------------------------------------------------------
# T01: POST /api/import/preview — parse CSV and return JSON preview
# ---------------------------------------------------------------------------


@router.post("/api/import/preview", response_model=None)
async def preview_import(
    db: DbSession,
    user: User = Depends(require_user),
    profile: Profile = Depends(require_active_profile),
    _writable: None = Depends(require_profile_writable),
    file: UploadFile = File(...),
) -> Response:
    """Parse an uploaded CSV and return a JSON preview.

    Returns the same information as the HTML POST /import endpoint but
    as JSON, without setting the session cookie. The modal owns the
    preview_id in Alpine state.
    """
    blob = await file.read()
    try:
        preview = preview_from_blob(db, profile, blob)
    except PreviewBlobError as exc:
        return JSONResponse({"detail": exc.message}, status_code=400)

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
    _writable: None = Depends(require_profile_writable),
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

    raw_rows, _ = _preview_rows_and_baseline(preview.raw_json)
    raw = [_dict_to_raw(d) for d in raw_rows]
    existing_assets = _existing_assets_for_profile(db, profile.id)
    result = match_positions(raw, existing_assets)

    # R06 (PRD §4.11 reactive layer): capture a pre-mutation
    # snapshot before the import commit. The import upserts
    # position state for every broker_ticker in the CSV, which
    # is destructive (overwrites prior qty/avg/current).
    try:
        snapshot_path, snapshot_id = snapshot_before_destructive(db)
    except (FileNotFoundError, OSError, Exception) as exc:
        logger.exception("snapshot_before_destructive failed for POST /api/import/commit: %s", exc)
        return JSONResponse(
            {"detail": f"Falha ao capturar snapshot: {exc}"},
            status_code=500,
        )
    before_counts = snapshot_counts(db, profile.id)

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

    # R06 (PRD §4.11 reactive layer): write audit row after the
    # import commit. Import is a destructive op because it
    # overwrites position state for every broker_ticker in the
    # CSV; the operator can roll back via /admin/restore/.
    after_counts = snapshot_counts(db, profile.id)
    try:
        record_mutation_audit(
            db,
            route="POST /api/import/commit",
            actor_user_id=user.id,
            profile_id=profile.id,
            before_counts=before_counts,
            after_counts=after_counts,
            snapshot_path=snapshot_path,
            snapshot_id=snapshot_id,
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - best-effort
        logger.warning("record_mutation_audit failed for POST /api/import/commit: %s", exc)
        db.rollback()

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
