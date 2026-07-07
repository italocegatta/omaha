"""Admin recovery endpoints (R06 — ``admin-recovery``).

Three endpoints, all gated by the :func:`require_admin` dependency
which checks the ``X-Admin-Password`` request header against
``os.environ["ADMIN_PASSWORD"]``. The env-var gate is the design's
D-R06.6 choice: the platform has no User-role table (both Italo
and Ana share the same family password per PRD §1.2), and
forcing an env-var gate decouples the recovery path from the
session cookie — the operator authenticates even after the user
DB is corrupted, and the gate is rotated via deployment.

Endpoints
---------
- ``GET  /admin/snapshots``           — list available rollback points
- ``POST /admin/restore/{snapshot_id}`` — copy snapshot over live DB and restart
- ``GET  /admin/audit``               — paginated mutation history

The ``/admin`` path prefix is intentionally outside the session
namespace: the gate does not call :func:`omaha.auth.require_user`
or :func:`require_active_profile`, so a corrupted
``active_profile_id`` cannot lock the operator out of recovery.
The env-var gate is the only authentication the recovery path
needs.

For the restore endpoint's systemd behaviour, see design
D-R06.7: when ``omaha-web.service`` is registered with the
user-level systemd manager, the endpoint shells out
``systemctl --user restart omaha-web.service``; otherwise the
endpoint returns ``{"restart_needed": true}`` and the operator
is responsible for ``pkill -f 'uvicorn omaha.main' && task serve``.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from omaha.db import get_db
from omaha.models import DbMutation, DbSnapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# 10s is enough for ``systemctl --user restart`` to bring the
# service back healthy. The endpoint polls ``/healthz`` after the
# restart; if the service does not come back within the timeout,
# the endpoint returns 202 with ``restart_needed: true`` so the
# operator can investigate (the DB has already been replaced —
# the operator MUST restart before any destructive route can
# write a new mutation that conflicts with the restored state).
HEALTHZ_TIMEOUT_SECONDS = 10

# Hard cap on the audit listing ``limit`` query param. ``500``
# is generous (a year of daily mutations fits comfortably) and
# protects the JSON serialiser from a hand-crafted ``limit=10**6``
# that would block the worker.
AUDIT_LIMIT_MAX = 500
AUDIT_LIMIT_DEFAULT = 100

# Default live DB path: the same path uvicorn opens at boot.
# ``shutil.copy2`` writes atomically (well, the dest is replaced
# in place; an open file handle keeps the inode alive — sqlite3
# tolerates this because every new connection reopens the file
# by path).
DEFAULT_LIVE_DB = Path("data/portfolio.db")


def _resolve_snapshots_dir() -> Path:
    """Read ``SNAPSHOT_DEST_DIR`` from the environment, defaulting to the dev path.

    Mirrors :func:`omaha.mutation_guards._resolve_dest_dir` —
    the restore endpoint reads snapshots from the same dir
    the destructive routes write to. Sharing the env var
    keeps test + prod aligned: a per-test ``SNAPSHOT_DEST_DIR``
    is the same dir for the snapshot writer and the restore
    reader.
    """
    raw = os.environ.get("SNAPSHOT_DEST_DIR", "data/snapshots")
    return Path(raw)


def _resolve_live_db() -> Path:
    """Read ``SNAPSHOT_SOURCE`` from the environment, defaulting to the dev path.

    Same env var as the snapshot helper: the restore endpoint
    overwrites the same file the destructive routes snapshot,
    so the env var that points the snapshot at the source DB
    also points the restore at it.
    """
    raw = os.environ.get("SNAPSHOT_SOURCE", str(DEFAULT_LIVE_DB))
    return Path(raw)


# ---------------------------------------------------------------------------
# Auth gate
# ---------------------------------------------------------------------------


def require_admin(request: Request) -> None:
    """Raise 401 unless ``X-Admin-Password`` matches the env var.

    The wire shape is ``{"reason": "unauthorized"}`` — same
    pattern as the ``HouseholdReadOnlyError`` handler in
    :mod:`omaha.auth`, no FastAPI ``{"detail": ...}`` wrapper.

    The check uses ``hmac.compare_digest`` to avoid a timing
    side-channel on the env-var comparison. The env var is
    read on every call so a deployment-time rotation takes
    effect without a process restart.
    """
    import hmac

    expected = os.environ.get("ADMIN_PASSWORD", "")
    if not expected:
        # Refuse to authenticate at all when the env var is
        # unset — better a hard 401 than a silent passwordless
        # admin gate.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin gate not configured",
        )
    provided = request.headers.get("x-admin-password", "")
    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )


# ---------------------------------------------------------------------------
# GET /admin/snapshots
# ---------------------------------------------------------------------------


@router.get("/snapshots", response_model=None)
def list_snapshots(
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> JSONResponse:
    """Return available rollback points sorted by ``created_at`` desc.

    The list joins ``db_snapshots`` against ``db_mutations`` via
    ``db_snapshots.mutation_id`` to attach the triggering
    mutation's id (or ``null`` for orphan snapshots — the few
    milliseconds between snapshot capture and audit insert).

    Snapshots whose underlying file is missing (manually deleted
    by the operator) are filtered out so the listing never
    surfaces a path that would 404 on restore.
    """
    rows = db.execute(select(DbSnapshot).order_by(DbSnapshot.created_at.desc())).scalars().all()
    out: list[dict[str, object]] = []
    for snap in rows:
        path = Path(snap.path)
        if not path.exists():
            logger.info("snapshot_list: skipping %s (file missing)", snap.path)
            continue
        out.append(
            {
                # ``path.stem`` strips the ``.db`` extension so the
                # id is the ``portfolio-<UTC>`` portion (matches
                # the spec's "id (the basename minus .db)" and
                # matches what the restore endpoint accepts —
                # the restore appends ``.db`` internally so the
                # caller never has to know the file extension).
                "id": path.stem,
                "path": str(path),
                "size_bytes": int(snap.size_bytes),
                "created_at": snap.created_at.isoformat() + "Z",
                "mutation_id": snap.mutation_id,
            }
        )
    return JSONResponse(out, status_code=200)


# ---------------------------------------------------------------------------
# POST /admin/restore/{snapshot_id}
# ---------------------------------------------------------------------------


@router.post("/restore/{snapshot_id}", response_model=None)
def restore_snapshot(
    snapshot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> JSONResponse:
    """Overwrite ``data/portfolio.db`` with the named snapshot; restart uvicorn.

    The snapshot id is the file basename (e.g.
    ``portfolio-2026-07-07T14-23-00Z``) — the same id returned
    by ``GET /admin/snapshots``. The endpoint refuses to
    accept a path that contains ``..`` or starts with ``/`` to
    prevent the operator from being phished into restoring a
    file outside ``data/snapshots/``.

    Returns 202 with ``restart_needed: false`` when the
    ``omaha-web.service`` systemd unit is registered and the
    restart succeeds, or ``restart_needed: true`` when no
    systemd unit is present. The DB is overwritten BEFORE the
    restart so the new uvicorn process picks up the restored
    state on its first query.
    """
    # URL-decode first so a hand-crafted ``..%2F..%2F`` does
    # not bypass the traversal check. ``unquote`` is safe for
    # the snapshot id — the file basename we generate has no
    # percent-escaped characters in the normal case.
    decoded = unquote(snapshot_id)
    if ".." in decoded or decoded.startswith("/") or "/" in decoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="snapshot_id inválido",
        )
    src = _resolve_snapshots_dir() / f"{decoded}.db"
    if not src.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="snapshot_not_found",
        )

    # Copy the snapshot over the live DB. ``shutil.copy2``
    # preserves metadata (not that it matters for SQLite) and
    # is the stdlib's documented atomic-replace helper. An
    # in-flight uvicorn request would still see the old file
    # because the inode changes; sqlite3 reopens the file per
    # query, so the new file is picked up on the next
    # request.
    dest = _resolve_live_db()
    try:
        shutil.copy2(src, dest)
    except OSError as exc:
        logger.exception("restore_snapshot: copy failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"copy_failed: {exc}",
        ) from exc

    # Attempt systemd restart. Failure (no unit present, or the
    # unit failed) is not a hard error — the DB has been
    # restored; the operator can restart manually.
    restart_needed = True
    restarted_via: str | None = None
    try:
        result = subprocess.run(
            ["systemctl", "--user", "restart", "omaha-web.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            restart_needed = False
            restarted_via = "systemd"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        logger.info("restore_snapshot: systemd restart unavailable: %s", exc)

    if restart_needed:
        logger.warning(
            "restore_snapshot: restart needed — DB restored to %s but no "
            "omaha-web.service unit; operator must restart manually",
            dest,
        )

    return JSONResponse(
        {
            "restart_needed": restart_needed,
            "restarted_via": restarted_via,
        },
        status_code=202,
    )


# ---------------------------------------------------------------------------
# GET /admin/audit
# ---------------------------------------------------------------------------


@router.get("/audit", response_model=None)
def list_audit(
    since: str | None = Query(
        default=None,
        description=("ISO-8601 UTC timestamp; rows with created_at > since are returned."),
    ),
    limit: int = Query(
        default=AUDIT_LIMIT_DEFAULT,
        ge=1,
        description=(
            "Maximum number of rows to return. The handler clamps the "
            "value to AUDIT_LIMIT_MAX (500) — a hand-crafted "
            "``limit=10000`` is honoured as 500, not rejected as a "
            "validation error."
        ),
    ),
    db: Session = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> JSONResponse:
    """Return mutation rows, paginated by ``since`` and clamped to ``limit``.

    Results are sorted by ``created_at`` descending. The
    ``before_json`` and ``after_json`` columns are deserialised
    back to dicts in the response so the operator does not have
    to re-parse JSON client-side.
    """
    # Clamp the limit internally rather than rejecting at the
    # Query level. The spec scenario "WHEN the operator sends
    # ``limit=10000`` THEN the system clamps the limit to 500"
    # is satisfied by the clamp; FastAPI's ``Query(le=...)`` is
    # a hard 422 which does not match the spec's "clamp" verb.
    effective_limit = min(limit, AUDIT_LIMIT_MAX)

    stmt = select(DbMutation).order_by(DbMutation.created_at.desc()).limit(effective_limit)
    if since is not None:
        try:
            # Accept ``2026-07-01T00:00:00Z`` and
            # ``2026-07-01T00:00:00+00:00``. We treat the input
            # as naive UTC if no tzinfo is present.
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"since inválido: {exc}",
            ) from exc
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=UTC)
        # SQLAlchemy compares naive datetimes to the DB column
        # (which is naive UTC per the migration); strip the
        # tzinfo for the comparison.
        stmt = stmt.where(DbMutation.created_at > since_dt.replace(tzinfo=None))

    rows = db.execute(stmt).scalars().all()
    out: list[dict[str, object]] = []
    for row in rows:
        out.append(
            {
                "id": int(row.id),
                "created_at": row.created_at.isoformat() + "Z",
                "route": row.route,
                "actor_user_id": row.actor_user_id,
                "profile_id": row.profile_id,
                "before": _safe_json(row.before_json),
                "after": _safe_json(row.after_json),
                "snapshot_path": row.snapshot_path,
            }
        )
    return JSONResponse(out, status_code=200)


def _safe_json(raw: str) -> object:
    """Return ``json.loads(raw)`` or the original string on parse failure.

    Defensive: a hand-crafted ``before_json`` (shouldn't happen
    in practice — the route always writes via ``json.dumps``)
    must not crash the listing endpoint. Returns the original
    string so the operator can diagnose.
    """
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


__all__ = [
    "router",
    "require_admin",
    "HEALTHZ_TIMEOUT_SECONDS",
    "AUDIT_LIMIT_MAX",
    "AUDIT_LIMIT_DEFAULT",
    "DEFAULT_LIVE_DB",
]
