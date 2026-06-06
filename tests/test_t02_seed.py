"""Tests for T02: database layer, models, Alembic migration, and seed.

Three concerns are exercised here, each in its own test:

1. ``test_seed_creates_user_and_profiles`` — :func:`omaha.seed.seed` is
   idempotent and populates the expected rows.
2. ``test_seed_is_idempotent`` — running :func:`seed` twice does not
   create duplicate users or profiles.
3. ``test_alembic_upgrade_creates_tables`` — running
   ``alembic upgrade head`` against a temporary SQLite file creates the
   ``users`` and ``profiles`` tables with the expected columns and
   unique constraint.

The DB-targeted tests use a per-test temporary SQLite file via the
``TMP_DATABASE_URL`` env var; :func:`omaha.config.settings` is
re-imported lazily so each test sees the URL it set.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


def _tmp_db_url(tmp_path: Path) -> str:
    """Return a ``sqlite:///`` URL pointing to a fresh file in ``tmp_path``."""
    db_file = tmp_path / "portfolio.db"
    return f"sqlite:///{db_file}"


@pytest.fixture()
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Configure a temporary SQLite DB, run alembic, then seed.

    Yields the :class:`pathlib.Path` to the database file. Restores the
    original environment on teardown.
    """
    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-t02")

    # Re-import omaha modules so they pick up the new DATABASE_URL.
    # ``omaha.config.settings`` is read at import time, so we have to
    # drop the cached modules and reimport.
    for mod_name in list(sys.modules):
        if mod_name == "omaha" or mod_name.startswith("omaha."):
            del sys.modules[mod_name]
    import omaha.config  # noqa: F401
    import omaha.db
    import omaha.models  # noqa: F401
    import omaha.seed

    # Run alembic upgrade head against the temp DB via the ``alembic``
    # CLI. We invoke it as a subprocess so the env var picked up by
    # ``env.py`` matches the rest of the test exactly. The subprocess
    # also needs ``SECRET_KEY`` because pytest is *not* in its
    # ``sys.modules``, so :func:`omaha.config._build_settings` would
    # otherwise raise ``RuntimeError`` on import.
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-t02",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    return {
        "db_path": Path(urlparse(db_url).path),
        "db_url": db_url,
        "seed": omaha.seed.seed,
        "SessionLocal": omaha.db.SessionLocal,
    }


def test_seed_creates_user_and_profiles(seeded_db) -> None:
    prior = seeded_db["seed"]()
    assert prior == 0, "fresh DB should have no users before seed"

    SessionLocal = seeded_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Profile, User

        users = session.query(User).all()
        assert len(users) == 1
        assert users[0].username == "family"
        assert users[0].password_hash  # bcrypt hash is non-empty
        assert users[0].password_hash.startswith("$2"), "password_hash should be a bcrypt hash"

        profiles = session.query(Profile).order_by(Profile.display_order).all()
        assert [p.name for p in profiles] == ["Italo", "Ana Livia"]
        assert [p.display_order for p in profiles] == [0, 1]
        assert all(p.user_id == users[0].id for p in profiles)


def test_seed_is_idempotent(seeded_db) -> None:
    seeded_db["seed"]()
    # Second call should detect the existing user and skip inserts.
    prior = seeded_db["seed"]()
    assert prior == 1, "second seed call should report 1 prior user"

    SessionLocal = seeded_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Profile, User

        assert session.query(User).count() == 1
        assert session.query(Profile).count() == 2


def test_alembic_upgrade_creates_tables(tmp_path: Path) -> None:
    """Run ``alembic upgrade head`` against an empty SQLite file and inspect schema."""
    db_url = _tmp_db_url(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-t02",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    db_path = Path(urlparse(db_url).path)
    assert db_path.exists(), "alembic should have created the SQLite file"

    engine = create_engine(db_url)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert {"users", "profiles"}.issubset(table_names), table_names

    # users columns
    user_cols = {c["name"] for c in inspector.get_columns("users")}
    assert {"id", "username", "password_hash", "created_at"}.issubset(user_cols)

    # profiles columns
    profile_cols = {c["name"] for c in inspector.get_columns("profiles")}
    assert {"id", "user_id", "name", "display_order", "created_at"}.issubset(profile_cols)

    # unique constraint on (user_id, name)
    unique_constraints = inspector.get_unique_constraints("profiles")
    constraint_names = {uc["name"] for uc in unique_constraints}
    assert "uq_profile_user_name" in constraint_names, unique_constraints

    # FK with ON DELETE CASCADE
    fks = inspector.get_foreign_keys("profiles")
    assert any(
        fk["constrained_columns"] == ["user_id"]
        and fk["referred_table"] == "users"
        and fk.get("options", {}).get("ondelete", "").upper() == "CASCADE"
        for fk in fks
    ), fks

    engine.dispose()
