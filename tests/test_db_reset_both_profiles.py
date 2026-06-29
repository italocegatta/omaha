"""Integration test for ``scripts.reset_both_profiles`` — runs against a fresh SQLite.

Confirms that the wrapper:

1. Creates both ``User`` + ``Profile`` rows (via ``omaha.seed``).
2. Loads the CSV triplets for ``italo`` and ``ana``.
3. Resets + reseeds both profiles in one invocation.
4. Returns 0 (success).
5. Populates each profile with non-zero classes + assets + positions.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parent.parent


def _set_test_env(db_path: Path, password: str) -> dict[str, str]:
    """Return an env dict that points omaha + the wrapper at a fresh SQLite file."""
    return {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{db_path}",
        "ADMIN_PASSWORD": password,
        "SECRET_KEY": "test-secret-key-for-11.5",
        "OMAHA_SKIP_STARTUP": "1",
        "OMAHA_ENV": "development",
    }


def _run_alembic(env: dict[str, str]) -> None:
    """Apply alembic migrations to the fresh DB."""
    assert (REPO_ROOT / "alembic.ini").exists()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic failed (cwd={REPO_ROOT}): stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_reset_both_profiles_seeds_both_profiles(tmp_path: Path) -> None:
    """End-to-end: fresh DB → alembic → seed → wrapper → both profiles populated."""
    db_path = tmp_path / "portfolio.db"
    env = _set_test_env(db_path, "test-family-password")
    _run_alembic(env)

    # Run omaha.seed in a subprocess so its env-bound modules
    # see DATABASE_URL=test (the wrapper subprocess will pick
    # up the same URL too).
    seed_proc = subprocess.run(
        [sys.executable, "-m", "omaha.seed"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert seed_proc.returncode == 0, (
        f"omaha.seed failed: stdout={seed_proc.stdout!r} stderr={seed_proc.stderr!r}"
    )
    assert "seeded 2 users" in seed_proc.stdout

    # Run the wrapper.
    wrapper_proc = subprocess.run(
        [sys.executable, "-m", "scripts.reset_both_profiles"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert wrapper_proc.returncode == 0, (
        f"wrapper failed: stdout={wrapper_proc.stdout!r} stderr={wrapper_proc.stderr!r}"
    )
    assert "profile=italo mode=reset" in wrapper_proc.stdout
    assert "profile=ana mode=reset" in wrapper_proc.stdout

    # Verify with a fresh engine (not the in-process SessionLocal,
    # which was bound to the test's pre-existing DB URL at import
    # time and would mask the wrapper's writes).
    engine = create_engine(env["DATABASE_URL"])
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT p.name, COUNT(DISTINCT ac.id) AS classes, "
                    "COUNT(DISTINCT a.id) AS assets, "
                    "COUNT(DISTINCT pos.id) AS positions "
                    "FROM profiles p "
                    "LEFT JOIN asset_classes ac ON ac.profile_id = p.id "
                    "LEFT JOIN assets a ON a.asset_class_id = ac.id "
                    "LEFT JOIN positions pos ON pos.asset_id = a.id "
                    "GROUP BY p.id ORDER BY p.display_order"
                )
            ).fetchall()
        assert len(rows) == 2, f"expected 2 profiles, got {rows}"
        for name, classes, assets, positions in rows:
            assert classes > 0, f"{name} has 0 classes"
            assert assets > 0, f"{name} has 0 assets"
            assert positions > 0, f"{name} has 0 positions"
        # The first profile is Italo (display_order=0).
        assert rows[0][0] == "Italo"
        assert rows[1][0] == "Ana"
    finally:
        engine.dispose()
