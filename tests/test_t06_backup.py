"""S06/T05 \u2014 backup script smoke checks.

Two tests:

1. **Happy path.** A source DB with 5 rows in a known table copies
   to a destination path via ``python -m scripts.backup <dest>``.
   The destination exists, opens, and reports the same row count.
2. **Missing source.** A non-existent source file causes the script
   to exit non-zero and print a stderr line that names the missing
   path. Operators rely on the stderr message to distinguish a
   real backup failure from a transient error.

The test runs the script via ``subprocess`` (not an in-process
import) so the ``if __name__ == \"__main__\":`` block + the
``--source`` / positional ``dest`` argparse surface is what the
operator actually gets when they invoke
``docker compose -f prod.yml run --rm backup``.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_backup(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke ``python -m scripts.backup`` as a subprocess.

    ``env`` defaults to a sanitised copy of ``os.environ`` (with
    ``PYTHONPATH`` cleared so the subprocess picks up the repo's
    ``scripts/`` package from the import path correctly) plus a
    ``SECRET_KEY`` so the test-mode guard in ``omaha.config`` does
    not raise if the script transitively imports ``omaha.config``.
    """
    base_env = os.environ.copy()
    base_env.pop("PYTHONPATH", None)
    base_env.setdefault("SECRET_KEY", "test-secret-do-not-use")
    if env:
        base_env.update(env)
    return subprocess.run(  # noqa: S603 \u2014 controlled input
        [sys.executable, "-m", "scripts.backup", *args],
        cwd=str(REPO_ROOT),
        env=base_env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_backup_copies_rows_to_destination(tmp_path: Path) -> None:
    """A source DB with 5 rows is fully copied to the destination.

    The destination's row count is the strong assertion (verifies
    that ``Connection.backup()`` actually executed, not just that
    the destination file was touched). The success line is also
    checked for the documented shape so the operator-facing
    contract is pinned.
    """
    source = tmp_path / "source.db"
    with sqlite3.connect(str(source)) as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.executemany("INSERT INTO t (x) VALUES (?)", [(i,) for i in range(5)])
        conn.commit()

    dest = tmp_path / "dest.db"
    result = _run_backup("--source", str(source), str(dest))

    assert result.returncode == 0, (
        f"backup exited {result.returncode}: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert dest.exists(), "destination file was not created"

    # Strong check: open the destination and confirm the row count.
    # If ``Connection.backup()`` silently failed, the dest might
    # exist as an empty file; the row count catches that.
    with sqlite3.connect(str(dest)) as conn:
        (count,) = conn.execute("SELECT COUNT(*) FROM t").fetchone()
    assert count == 5, f"expected 5 rows in destination, got {count}"

    # Pin the operator-facing success line shape. The status
    # suffix is informational, but the ``backup OK:`` prefix + the
    # ``source -> dest`` arrow is what an operator greps for in
    # cron output. ``Connection.backup()`` returns ``None`` on a
    # clean completion in Python 3.12, so the script writes
    # ``(complete)`` for the normal case.
    assert "backup OK:" in result.stdout
    assert str(source) in result.stdout
    assert str(dest) in result.stdout
    assert "complete" in result.stdout


def test_backup_exits_nonzero_with_stderr_when_source_missing(
    tmp_path: Path,
) -> None:
    """A missing source file causes a non-zero exit and a stderr line.

    The script's :func:`main` checks ``source.exists()`` before
    opening sqlite3; that path produces the ``backup FAIL: source
    not found:`` message and exit code 1. Operators tailing the
    output need both signals to alert on a real failure.
    """
    nonexistent = tmp_path / "definitely-not-here.db"
    dest = tmp_path / "dest.db"
    assert not nonexistent.exists()  # sanity

    result = _run_backup("--source", str(nonexistent), str(dest))

    assert result.returncode != 0, (
        f"backup should have failed for missing source; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "source not found" in result.stderr, (
        f"stderr should mention the missing source path; got: {result.stderr!r}"
    )
    # The destination must not have been created \u2014 a backup that
    # silently succeeds against a missing source is worse than a
    # loud failure.
    assert not dest.exists(), "backup wrote a destination file despite a missing source"


def test_backup_works_against_real_dev_db(tmp_path: Path) -> None:
    """Smoke test against the seeded dev DB.

    Skips cleanly if ``data/portfolio.db`` is not present (e.g. on
    a fresh checkout where the operator has not yet run the dev
    server once). When present, the destination should be a
    byte-for-byte (or at least page-for-page) copy that opens
    cleanly. This is the verification the T05 plan called out:
    '`uv run python -m scripts.backup /tmp/omaha-test-backup.db`
    produces a valid backup; ``sqlite3`` (or Python
    ``sqlite3.connect``) shows the same tables.'
    """
    dev_db = REPO_ROOT / "data" / "portfolio.db"
    if not dev_db.exists():
        pytest.skip("data/portfolio.db not present (run the dev server once)")

    # Collect the source's table list up front so the assertion is
    # explicit (we are not just checking that the dest opens).
    with sqlite3.connect(str(dev_db)) as src:
        src_tables = {
            row[0] for row in src.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

    dest = tmp_path / "dev-backup.db"
    result = _run_backup("--source", str(dev_db), str(dest))

    assert result.returncode == 0, (
        f"backup of dev DB failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    with sqlite3.connect(str(dest)) as dst:
        dst_tables = {
            row[0] for row in dst.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert src_tables == dst_tables, (
        f"table list differs: source={src_tables!r} dest={dst_tables!r}"
    )
