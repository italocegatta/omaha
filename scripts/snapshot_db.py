"""Auto-snapshot helper for the destructive-route DB-mutation guards (R06).

The destructive class/asset/import routes call
:func:`snapshot_live_db` immediately before committing the
mutation; the returned path is recorded in the corresponding
:mod:`omaha.models.DbMutation` row so the operator can roll
back via the ``/admin/restore/{snapshot_id}`` endpoint if the
mutation turns out to be bad.

The snapshot is a hot copy of the live SQLite file produced via
the stdlib :meth:`sqlite3.Connection.backup` API — same pattern
as :mod:`scripts.backup`. ``backup()`` acquires a shared lock on
the source for the duration of the copy; writers block briefly
but the destination is committed atomically per page. ``cp``
would race with writers and is unsafe while uvicorn is running,
so the platform does not use it.

The companion function :func:`prune_snapshots` enforces the
FIFO retention of 50 snapshots per the ``db-mutation-safety``
spec. It is invoked once on FastAPI lifespan boot (see
:mod:`omaha.main`) and never on the destructive-route path —
the prune must not block a user-visible mutation.

The script's ``__main__`` block is the operator one-shot path:
``python -m scripts.snapshot_db`` snapshots ``./data/portfolio.db``
into ``./data/snapshots/`` and runs the prune. The script does
NOT take a snapshot of the running uvicorn process via
``subprocess`` — the destructive route already calls
:func:`snapshot_live_db` from inside the request, and an
operator-initiated snapshot from outside the process is a
manual operation that lives in the task runner (``task
backup`` covers the operator's "give me a file I can copy
elsewhere" use case).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

# Default retention: 50 snapshots per ``db-mutation-safety`` spec.
# Owner can override per-deployment by passing ``--retention`` to the
# CLI or by reading ``SNAPSHOT_RETENTION`` from the environment inside
# the FastAPI lifespan.
DEFAULT_RETENTION = 50

# Default source path matches the omaha dev/prod layout.
DEFAULT_SOURCE = Path("./data/portfolio.db")
DEFAULT_DEST_DIR = Path("./data/snapshots")


def _now_utc_iso() -> str:
    """Return a UTC ISO-8601 timestamp safe for use in a filename.

    The colons are replaced with hyphens so the filename is safe
    to copy via ``scp``/``rsync`` and stays lexicographically
    sortable — ``"2026-07-07T14-23-00Z" < "2026-07-07T14-23-01Z"``
    matches chronological order, which is what
    :func:`prune_snapshots` relies on.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")


def snapshot_live_db(src: Path, dest_dir: Path) -> Path:
    """Copy ``src`` to a timestamped file under ``dest_dir`` and return the path.

    The destination directory is created if it does not exist. The
    returned path is the absolute, resolved path of the written
    file so the caller can store it in ``db_snapshots.path``
    without further normalization.

    Raises
    ------
    FileNotFoundError
        ``src`` does not exist (operator-visible: typo, missing
        bind mount, wrong working directory).
    sqlite3.Error
        The copy failed mid-stream; the partially-written
        destination is left on disk and the caller is expected to
        treat the operation as failed (the destructive route
        returns HTTP 500 without committing the mutation).
    OSError
        ``dest_dir`` is not writable (disk full, read-only volume,
        EACCES). Propagates unchanged so the operator gets the
        full traceback.
    """
    src = src.resolve()
    dest_dir = dest_dir.resolve()
    if not src.exists():
        raise FileNotFoundError(f"snapshot_live_db: source not found: {src}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"portfolio-{_now_utc_iso()}.db"

    # ``isolation_level=None`` puts sqlite3 in autocommit mode,
    # which ``Connection.backup()`` requires — it manages its own
    # transaction internally. Same pattern as ``scripts/backup.py``.
    with (
        sqlite3.connect(str(src), isolation_level=None) as src_conn,
        sqlite3.connect(str(dest), isolation_level=None) as dest_conn,
    ):
        remaining = src_conn.backup(dest_conn)

    if remaining not in (None, 0):
        # Defensive: ``backup()`` returns the number of remaining
        # pages if interrupted. A non-zero result means the copy
        # was partial; surface as an error so the destructive
        # route does NOT proceed.
        raise sqlite3.Error(
            f"snapshot_live_db: partial copy of {src} -> {dest} (remaining={remaining} pages)"
        )

    return dest


def prune_snapshots(dest_dir: Path, retention: int = DEFAULT_RETENTION) -> int:
    """Delete oldest snapshot files in ``dest_dir`` beyond ``retention``.

    Files matching the ``portfolio-<UTC>.db`` pattern are sorted
    lexicographically by filename (the timestamp is ISO-8601, so
    lexicographic == chronological). The oldest beyond the
    ``retention``-th are removed.

    Returns the number of files deleted. Returns 0 when
    ``dest_dir`` does not exist or contains fewer than
    ``retention + 1`` matching files (the common case).

    Non-matching files (e.g. an operator's manual copy) are
    ignored — the prune is scoped to the platform-managed
    snapshot namespace, never the operator's manual backups.
    """
    if not dest_dir.exists():
        return 0
    if retention < 0:
        raise ValueError(f"prune_snapshots: retention must be >= 0, got {retention}")

    # Filter to platform-managed snapshots only. The glob pattern
    # matches the naming used by ``snapshot_live_db`` above; any
    # operator-managed ``*.db`` files in the directory are left
    # alone.
    snapshots = sorted(dest_dir.glob("portfolio-*.db"))
    excess = len(snapshots) - retention
    if excess <= 0:
        return 0

    deleted = 0
    for path in snapshots[:excess]:
        try:
            path.unlink()
        except OSError:
            # An unlink failure (permission denied, file in use)
            # should not abort the prune — the next boot will
            # try again. Log via stderr so the operator sees
            # the issue without a stack trace.
            print(
                f"snapshot prune WARN: failed to delete {path}: {sys.exc_info()[1]}",
                file=sys.stderr,
            )
            continue
        deleted += 1
    return deleted


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Take a one-shot snapshot of the live omaha SQLite DB into "
            "data/snapshots/ and prune to the retention limit. The "
            "destructive-route hot path calls snapshot_live_db() in-process; "
            "this CLI is the operator's one-shot path."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to the source SQLite file. Default: %(default)s",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=DEFAULT_DEST_DIR,
        help="Directory to write the snapshot to. Default: %(default)s",
    )
    parser.add_argument(
        "--retention",
        type=int,
        default=DEFAULT_RETENTION,
        help="Maximum number of snapshots to retain. Default: %(default)s",
    )
    parser.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Skip the snapshot step; only run the prune. Useful for cron jobs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if not args.no_snapshot:
        try:
            dest = snapshot_live_db(args.source, args.dest_dir)
        except FileNotFoundError as exc:
            print(f"snapshot FAIL: {exc}", file=sys.stderr)
            return 1
        except sqlite3.Error as exc:
            print(f"snapshot FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        else:
            print(f"snapshot OK: {args.source} -> {dest}")

    deleted = prune_snapshots(args.dest_dir, retention=args.retention)
    if deleted:
        print(f"prune OK: deleted {deleted} old snapshot(s) from {args.dest_dir}")
    else:
        print(f"prune OK: no prune needed in {args.dest_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
