"""Periodic backup scheduler for the prod stack.

Runs ``scripts.backup`` on a fixed interval (``BACKUP_INTERVAL`` env var,
integer seconds, default 86400 = 24h). Failures are logged at ERROR and
the loop continues so a transient error (DB locked by migration, disk
full) does not take the scheduler down. The container therefore stays
in ``running`` state across individual run failures.

Invoked from prod.yml as the ``backup-scheduler`` service:

    docker compose -f prod.yml up -d backup-scheduler

The image (``omaha:prod``) and bind mount layout are reused from the
existing one-shot ``backup`` service (D-I01.2 in the slice design). The
scheduler never touches the live database — ``omaha-data:/app/data:ro``
keeps the data volume mounted read-only, same as the manual path.

Validation of ``BACKUP_INTERVAL`` happens once at start-up: a
non-integer or non-positive value is fatal (exit 2) so a typo in the
env file surfaces immediately instead of producing a stream of broken
schedules.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import UTC, datetime

_DEFAULT_INTERVAL = 86400
_DEFAULT_DEST_DIR = "/backups"


def _now_utc_iso() -> str:
    """ISO-8601 UTC timestamp with trailing ``Z`` (e.g. ``2026-07-06T03:14:15Z``)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_interval() -> int:
    """Read ``BACKUP_INTERVAL`` from the environment.

    Defaults to 24h. A non-integer or non-positive value fails fast
    with a clear message on stderr — the container exits so the
    operator notices the misconfiguration instead of silently running
    a broken loop.
    """
    raw = os.environ.get("BACKUP_INTERVAL", str(_DEFAULT_INTERVAL))
    try:
        value = int(raw)
    except ValueError:
        print(
            f"backup_scheduler FATAL: BACKUP_INTERVAL={raw!r} is not an integer",
            file=sys.stderr,
        )
        sys.exit(2)
    if value <= 0:
        print(
            f"backup_scheduler FATAL: BACKUP_INTERVAL must be a positive integer, got {value}",
            file=sys.stderr,
        )
        sys.exit(2)
    return value


def _dest_path() -> str:
    """Lexically-sortable UTC-timestamped path inside the bind-mounted backups dir.

    ``BACKUP_DEST_DIR`` overrides the destination directory (default
    ``/backups``, which matches the bind mount in prod.yml). The
    override exists so the scheduler can be exercised in dev against
    a host-local ``./backups/`` path without requiring root.

    Mirrors the manual ``backup`` service's pattern so a scheduled run
    produces the same filename shape as an ad-hoc ``run --rm backup``.
    """
    dest_dir = os.environ.get("BACKUP_DEST_DIR", _DEFAULT_DEST_DIR)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{dest_dir.rstrip('/')}/portfolio-{timestamp}.db"


def _run_once() -> int:
    """Execute one backup invocation, log the outcome, return the exit code.

    The subprocess call is wrapped so a non-zero exit code is captured
    and reported — it does NOT raise. The outer loop must continue
    regardless of individual run failures (D-I01.5).
    """
    dest = _dest_path()
    print(f"{_now_utc_iso()} INFO backup started dest={dest}")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.backup", dest],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        # ``scripts.backup`` already prints ``backup OK: <src> -> <dest>``
        # on stdout. Surface it on its own log line so the scheduler
        # output is grep-friendly.
        print(f"{_now_utc_iso()} INFO backup OK: {result.stdout.strip()}")
        return 0
    # Trim trailing newline from the script's own stderr; the scheduler
    # adds its own prefix so the log line stays one-liner.
    stderr = result.stderr.strip() or "(no stderr)"
    print(
        f"{_now_utc_iso()} ERROR backup failed: exit={result.returncode} stderr={stderr}",
        file=sys.stderr,
    )
    return result.returncode


def main() -> int:
    interval = _parse_interval()
    print(f"{_now_utc_iso()} INFO backup_scheduler started interval={interval}s")
    while True:
        _run_once()
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
