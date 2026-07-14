"""Safe test-database bootstrap and cleanup helpers."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TEST_SECRET_KEY = "test-secret-do-not-use"
TEST_ADMIN_PASSWORD = "test-password"


@dataclass(frozen=True)
class SafeTestDatabase:
    path: Path
    snapshot_dir: Path


def prepare_safe_test_database(repo_root: Path) -> SafeTestDatabase:
    """Bind Omaha to a session-scoped temporary database before test collection."""
    safe_dir = Path(tempfile.mkdtemp(prefix="omaha-conftest-safe-"))
    db_path = safe_dir / "portfolio.db"
    snapshot_dir = safe_dir / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SNAPSHOT_SOURCE"] = str(db_path)
    os.environ["SNAPSHOT_DEST_DIR"] = str(snapshot_dir)
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
    os.environ["OMAHA_SKIP_STARTUP"] = "1"
    os.environ["OMAHA_ENV"] = "development"

    import omaha.config  # noqa: F401
    import omaha.db  # noqa: F401
    import omaha.seed  # noqa: F401

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(repo_root),
        env={**os.environ},
        check=True,
        capture_output=True,
        text=True,
    )
    omaha.seed.seed()
    return SafeTestDatabase(path=db_path, snapshot_dir=snapshot_dir)


def prepare_worker_database(worker_id: str, repo_root: Path) -> SafeTestDatabase:
    """Provision an isolated SQLite database for one pytest-xdist worker.

    Each worker gets its own tempdir with ``portfolio.db`` and
    ``snapshots/``. The directory structure mirrors the session-scoped
    layout from :func:`prepare_safe_test_database`. Uses the existing
    :func:`run_alembic_upgrade` helper and test constants.
    """
    safe_dir = Path(tempfile.mkdtemp(prefix=f"omaha-worker-{worker_id}-"))
    db_path = safe_dir / "portfolio.db"
    snapshot_dir = safe_dir / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SNAPSHOT_SOURCE"] = str(db_path)
    os.environ["SNAPSHOT_DEST_DIR"] = str(snapshot_dir)
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["ADMIN_PASSWORD"] = TEST_ADMIN_PASSWORD
    os.environ["OMAHA_SKIP_STARTUP"] = "1"
    os.environ["OMAHA_ENV"] = "development"

    import omaha.config  # noqa: F401
    import omaha.db  # noqa: F401
    import omaha.seed  # noqa: F401

    run_alembic_upgrade(repo_root, f"sqlite:///{db_path}")
    omaha.seed.seed()
    return SafeTestDatabase(path=db_path, snapshot_dir=snapshot_dir)


def verify_session_local_is_safe() -> None:
    """Fail hard when a test session is accidentally bound to production DB."""
    from omaha.db import SessionLocal

    probe = SessionLocal()
    try:
        bind = probe.get_bind()
        url = str(bind.url) if bind is not None else ""
        if "data/portfolio.db" in url or url.endswith("/data/portfolio.db"):
            raise RuntimeError(
                f"PROD-DB ISOLATION BROKEN: SessionLocal is bound to prod DB ({url!r}). "
                "Conftest env isolation failed — refusing to run any test that would wipe/seed "
                "prod. "
                "See conftest.py module-load block."
            )
    finally:
        probe.close()


def make_test_env(
    db_url: str,
    *,
    password: str = TEST_ADMIN_PASSWORD,
) -> dict[str, str]:
    """Return a complete env dict for subprocess tests.

    Combines ``os.environ`` with the Omaha-specific variables needed to
    point a subprocess at *db_url* with the given admin *password*.

    Typical usage::

        env = make_test_env(f"sqlite:///{tmp_path / 'db.sqlite'}")
        subprocess.run([...], env=env)

    Callers that need a non-default ``SECRET_KEY`` or other variables
    can override entries on the returned dict before passing it to
    ``subprocess.run``.
    """
    return {
        **os.environ,
        "DATABASE_URL": db_url,
        "ADMIN_PASSWORD": password,
        "SECRET_KEY": TEST_SECRET_KEY,
        "OMAHA_SKIP_STARTUP": "1",
        "OMAHA_ENV": "development",
    }


def run_alembic_upgrade(repo_root: Path, db_url: str) -> None:
    """Run migrations in a subprocess against ``db_url``."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
            "SECRET_KEY": TEST_SECRET_KEY,
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def run_alembic_and_seed(
    repo_root: Path,
    db_url: str,
    *,
    password: str = TEST_ADMIN_PASSWORD,
) -> None:
    """Run alembic migrations + omaha seed in one shot.

    Calls :func:`run_alembic_upgrade` then spawns ``omaha.seed`` as a
    subprocess (so its env-bound modules see ``DATABASE_URL``).

    Typical usage in a pytest fixture that needs a fresh seeded DB::

        db_url = f"sqlite:///{tmp_path / 'portfolio.db'}"
        run_alembic_and_seed(REPO_ROOT, db_url)

    The caller retains full control of *db_url* and *password* while
    the helper handles the repeated subprocess dance.
    """
    run_alembic_upgrade(repo_root, db_url)
    env = make_test_env(db_url, password=password)
    result = subprocess.run(
        [sys.executable, "-m", "omaha.seed"],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"omaha.seed failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def set_asset_target_pcts_via_db(
    assignments: dict[str, float],
    db_path: Path | None = None,
) -> None:
    """Patch ``Asset.target_pct`` directly via sqlite so the
    CVXPY rebalance engine sees a valid portfolio (assets' target_pct
    must sum to 100 within each class).

    Used by e2e tests that need the rebalance plan to render but
    don't have a CSV import path that already encodes target_pct.
    Direct DB write — bypasses the asset/position seed invariant
    (PRD §4.3) because this is test-only setup.
    """
    if db_path is None:
        db_path = Path(__file__).resolve().parent.parent.parent / "data" / "test_e2e.db"
    conn = sqlite3.connect(db_path)
    try:
        for asset_name, target_pct in assignments.items():
            conn.execute(
                "UPDATE assets SET target_pct = ? WHERE name = ?",
                (target_pct, asset_name),
            )
        conn.commit()
    finally:
        conn.close()


def wipe_profile_in_sqlite(db_path: Path, profile_name: str) -> None:
    """Delete one profile's test data while preserving historical test ordering."""
    from scripts.seed_from_csv.wipe import wipe_profile_rows

    if not db_path.exists():
        return
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA busy_timeout = 3000")
        row = conn.execute("SELECT id FROM profiles WHERE name = ?", (profile_name,)).fetchone()
        if row is None:
            return
        wipe_profile_rows(
            row[0],
            lambda statement, params: conn.execute(statement, params),
            remove_orphan_positions=True,
            import_previews_before_assets=False,
        )
        conn.commit()
    finally:
        conn.close()
