"""DB mutation safety helpers (R06 — ``db-mutation-safety``).

Two coupled mechanisms protect the household's only SQLite
file (``data/portfolio.db``) from accidental destruction:

1. **Auto-snapshot** (:func:`snapshot_before_destructive`).
   A hot copy of the live DB is written to ``data/snapshots/``
   immediately before every destructive class/asset/import
   transaction commits. Failure of the snapshot operation
   aborts the mutation with HTTP 500 — a snapshot failure
   means the rollback path is broken, so letting the mutation
   proceed would defeat the whole point of the slice.

2. **Audit trail** (:func:`record_mutation_audit`). After the
   mutation commits, a :class:`~omaha.models.DbMutation` row
   is inserted carrying the route, actor, profile,
   before/after counts, and the snapshot path. The companion
   :class:`~omaha.models.DbSnapshot` row's ``mutation_id`` is
   back-filled to point at the new mutation id so the admin
   ``/admin/snapshots`` listing can show "which mutation
   triggered this snapshot".

PRD §4.11 (codified 2026-07-07) is the **process contract**
that governs which routes must call these helpers: every
destructive route captures a snapshot and writes an audit
row. The reactive layer is enough to RECOVER from any
wipe — the operator uses ``/admin/restore/{id}`` to roll
back. Prevention of accidental wipes is at the process
level (OpenSpec review, tests, validation against
established contracts) — not at the code level via
gates/flags.

The companion admin endpoints live in
:mod:`omaha.routes.admin` (snapshot listing, restore,
audit listing).
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from sqlalchemy.orm import Session

from omaha.models import Asset, AssetClass, DbMutation, DbSnapshot

# Where snapshots live on disk. The destructive routes resolve the
# path from ``Path("data/portfolio.db")`` at call time; constants
# here are the spec's canonical defaults. Override per-deployment
# by setting ``SNAPSHOT_SOURCE`` and ``SNAPSHOT_DEST_DIR`` env
# vars (the lifespan reads them once at startup; the destructive
# routes read them at call time).
DEFAULT_SNAPSHOT_SOURCE = Path("data/portfolio.db")
DEFAULT_SNAPSHOT_DEST_DIR = Path("data/snapshots")


def _resolve_source() -> Path:
    """Read ``SNAPSHOT_SOURCE`` from the environment, defaulting to the dev path."""
    raw = os.environ.get("SNAPSHOT_SOURCE", str(DEFAULT_SNAPSHOT_SOURCE))
    return Path(raw)


def _resolve_dest_dir() -> Path:
    """Read ``SNAPSHOT_DEST_DIR`` from the environment, defaulting to ``data/snapshots``."""
    raw = os.environ.get("SNAPSHOT_DEST_DIR", str(DEFAULT_SNAPSHOT_DEST_DIR))
    return Path(raw)


def count_classes(db: Session, profile_id: int) -> int:
    """Return the count of :class:`AssetClass` rows belonging to ``profile_id``."""
    return db.query(AssetClass).filter(AssetClass.profile_id == profile_id).count()


def count_assets(db: Session, profile_id: int) -> int:
    """Return the count of :class:`Asset` rows belonging to ``profile_id``."""
    return (
        db.query(Asset)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .filter(AssetClass.profile_id == profile_id)
        .count()
    )


def count_positions(db: Session, profile_id: int) -> int:
    """Return the count of :class:`Position` rows belonging to ``profile_id``."""
    from omaha.models import Position

    return (
        db.query(Position)
        .join(Asset, Position.asset_id == Asset.id)
        .join(AssetClass, Asset.asset_class_id == AssetClass.id)
        .filter(AssetClass.profile_id == profile_id)
        .count()
    )


def snapshot_counts(db: Session, profile_id: int) -> dict[str, int]:
    """Return the {classes, assets, positions} count snapshot for ``profile_id``.

    Used as the ``before`` and ``after`` payload of an audit row.
    The dict serialises to JSON in a single ``json.dumps`` call
    by :func:`record_mutation_audit`.
    """
    return {
        "classes": count_classes(db, profile_id),
        "assets": count_assets(db, profile_id),
        "positions": count_positions(db, profile_id),
    }


def snapshot_before_destructive(
    db: Session,
    *,
    source: Path | None = None,
    dest_dir: Path | None = None,
) -> tuple[Path, int]:
    """Capture a snapshot and insert a :class:`DbSnapshot` row; return ``(path, id)``.

    The snapshot file is written to ``dest_dir`` via
    :func:`scripts.snapshot_db.snapshot_live_db`; the row is
    inserted with ``mutation_id=None`` and the route back-fills
    the column after the audit insert via
    :func:`record_mutation_audit`.

    ``source`` and ``dest_dir`` default to the env-var
    resolution at call time (``SNAPSHOT_SOURCE`` /
    ``SNAPSHOT_DEST_DIR``); explicit values are accepted for
    tests.

    The function does NOT commit — the caller controls the
    transaction so the snapshot row commits atomically with the
    surrounding mutation. The audit insert happens in a
    separate commit (best-effort).

    Raises
    ------
    FileNotFoundError, sqlite3.Error, OSError
        Propagated from :func:`scripts.snapshot_db.snapshot_live_db`.
        The destructive route catches these and returns HTTP 500;
        the mutation is NOT applied.
    """
    from scripts.snapshot_db import snapshot_live_db

    src = source if source is not None else _resolve_source()
    dst = dest_dir if dest_dir is not None else _resolve_dest_dir()
    path = snapshot_live_db(src, dst)
    size = path.stat().st_size
    snap = DbSnapshot(path=str(path), size_bytes=size)
    db.add(snap)
    db.flush()  # populate snap.id without committing
    return path, snap.id


def record_mutation_audit(
    db: Session,
    *,
    route: str,
    actor_user_id: int | None,
    profile_id: int | None,
    before_counts: Mapping[str, int],
    after_counts: Mapping[str, int],
    snapshot_path: Path | str | None = None,
    snapshot_id: int | None = None,
) -> DbMutation:
    """Write a :class:`DbMutation` row and back-fill the snapshot's ``mutation_id``.

    Called from the destructive routes AFTER the destructive
    commit. The audit row's ``before_json`` and ``after_json``
    are JSON-serialised count dicts; the ``snapshot_path`` is
    the path returned by :func:`snapshot_before_destructive`.

    If ``snapshot_id`` is provided, the function back-fills
    ``db_snapshots.mutation_id`` on the matching row so the
    admin listing can attach the mutation to the snapshot.

    The function does NOT commit — the caller decides whether
    to commit the audit row (recommended) or roll it back on
    failure. Best-effort: the route wraps the call in a
    try/except and emits a structured WARN log if the insert
    fails; the user-visible mutation has already committed.
    """
    mutation = DbMutation(
        route=route,
        actor_user_id=actor_user_id,
        profile_id=profile_id,
        before_json=json.dumps(dict(before_counts), ensure_ascii=False),
        after_json=json.dumps(dict(after_counts), ensure_ascii=False),
        snapshot_path=str(snapshot_path) if snapshot_path is not None else None,
    )
    db.add(mutation)
    db.flush()  # populate mutation.id

    if snapshot_id is not None:
        snap = db.get(DbSnapshot, snapshot_id)
        if snap is not None:
            snap.mutation_id = mutation.id

    return mutation


__all__ = [
    "DEFAULT_SNAPSHOT_SOURCE",
    "DEFAULT_SNAPSHOT_DEST_DIR",
    "snapshot_before_destructive",
    "record_mutation_audit",
    "snapshot_counts",
    "count_classes",
    "count_assets",
    "count_positions",
    "_resolve_source",
    "_resolve_dest_dir",
]
