"""Hot SQLite backup using stdlib :meth:`sqlite3.Connection.backup`.

The ``sqlite3`` shell binary is not present in the prod image
(``python:3.12-slim`` + the omaha venv only ship the Python
stdlib), so the backup uses the ``Connection.backup()`` API instead
of shelling out. The two are functionally equivalent for a
consistent snapshot: ``backup()`` acquires a shared lock on the
source for the duration of the copy, so writers block briefly but
the destination is committed atomically per page.

To restore: stop the prod stack, ``cp <backup>.db ./data/portfolio.db``
(in dev with a bind mount) or ``docker compose -f prod.yml cp
./backups/<backup>.db web:/app/data/portfolio.db`` (in prod with a
named volume), then ``docker compose -f prod.yml up -d``.

The script is invoked from prod.yml as the ``backup`` service:

    docker compose -f prod.yml run --rm backup

The service's CMD in prod.yml passes the destination path as the
positional argument (``/backups/portfolio-<UTC>.db``); the source
defaults to ``./data/portfolio.db`` (relative to the container's
working directory, which the prod image sets to ``/app``).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Hot SQLite backup via the stdlib Connection.backup() API. "
            "The destination is the positional argument; --source defaults "
            "to ./data/portfolio.db (the path inside the prod container's "
            "/app working directory)."
        )
    )
    parser.add_argument(
        "--source",
        default="./data/portfolio.db",
        help=(
            "Path to the source SQLite file. Resolved relative to the "
            "current working directory. Default: %(default)s"
        ),
    )
    parser.add_argument(
        "dest",
        help=(
            "Path to the destination SQLite file. The file is created if "
            "it does not exist; existing files are overwritten."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    source = Path(args.source)
    dest = Path(args.dest)

    # Surface missing source files with a clear error rather than
    # letting sqlite3 raise a less obvious ``unable to open database``
    # message. A missing source is operator-visible (typo, wrong
    # --source, missing bind mount) and worth a dedicated message.
    if not source.exists():
        print(f"backup FAIL: source not found: {source}", file=sys.stderr)
        return 1

    # Make sure the destination's parent directory exists; the
    # ``/backups`` bind mount in prod.yml is created on the host, so
    # this matters mostly when an operator runs the script locally
    # with a destination like ``./backups/foo.db``.
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        # ``isolation_level=None`` puts sqlite3 in autocommit mode,
        # which ``Connection.backup()`` requires — it manages its
        # own transaction internally.
        with (
            sqlite3.connect(str(source), isolation_level=None) as src,
            sqlite3.connect(str(dest), isolation_level=None) as dst,
        ):
            # ``backup()`` returns ``None`` on a clean completion in
            # Python 3.12, or the number of remaining pages if the
            # call was interrupted (which should not happen here
            # because we pass the default pages=-1 and let the
            # method run to completion). The success line reads
            # ``complete`` in the normal case and surfaces the
            # remaining-page count if the copy was partial, so an
            # operator can grep for the unusual value.
            remaining = src.backup(dst)
    except sqlite3.Error as exc:
        # Catch every sqlite3-level error (open, copy, commit).
        # Anything else (OSError on a full disk, PermissionError
        # on a read-only volume) propagates as the original
        # traceback — the operator gets the full context.
        print(f"backup FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if remaining is None:
        status = "complete"
    else:
        status = (
            f"complete (remaining={remaining})"
            if remaining == 0
            else f"PARTIAL (remaining={remaining})"
        )
    print(f"backup OK: {source} -> {dest} ({status})")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
