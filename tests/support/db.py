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
