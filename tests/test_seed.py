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


def _restore_omaha_modules(saved: dict[str, object]) -> None:
    """Re-populate ``sys.modules`` with the omaha.* modules saved before the fixture.

    Drop any modules that the fixture re-imported (so we don't keep
    stale env-bound copies in ``sys.modules``), then restore the
    pre-fixture snapshot.
    """
    for name in list(sys.modules):
        if (name == "omaha" or name.startswith("omaha.")) and name not in saved:
            del sys.modules[name]
    for name, mod in saved.items():
        sys.modules[name] = mod


def _tmp_db_url(tmp_path: Path) -> str:
    """Return a ``sqlite:///`` URL pointing to a fresh file in ``tmp_path``."""
    db_file = tmp_path / "portfolio.db"
    return f"sqlite:///{db_file}"


@pytest.fixture()
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """Configure a temporary SQLite DB, run alembic, then seed.

    Yields the :class:`pathlib.Path` to the database file. Restores the
    original environment and ``sys.modules`` on teardown so the
    conftest's session-scoped ``omaha.*`` modules stay consistent for
    tests that share them (T03 auth, T04 e2e, S03 e2e).
    """
    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-t02")

    # Snapshot the omaha.* modules so we can restore them on teardown.
    # Without this, the re-imported (env-bound) modules leak into
    # later tests and break the conftest's session-scoped DB/engine.
    saved_omaha_modules = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "omaha" or name.startswith("omaha.")
    }
    request.addfinalizer(lambda: _restore_omaha_modules(saved_omaha_modules))

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
        from omaha.models import User

        users = session.query(User).all()
        # 3 users: Italo + Ana + the password-less ``family`` owner
        # of the F07 sentinel row (F07 — Família-as-profile).
        assert len(users) == 3
        usernames = {u.username for u in users}
        assert usernames == {"Italo", "Ana", "family"}
        italo = next(u for u in users if u.username == "Italo")
        assert italo.password_hash  # bcrypt hash is non-empty
        assert italo.password_hash.startswith("$2"), "password_hash should be a bcrypt hash"

        # F07 — Ana and Italo each own exactly ONE profile (the
        # F01 ``Italo RF2`` fixture profile is retired; the canonical
        # post-F07 shape is 2 real profiles + 1 sentinel).
        profiles_by_user = {
            u.username: sorted(u.profiles, key=lambda p: p.display_order)
            for u in users
            if u.username != "family"
        }
        assert [p.name for p in profiles_by_user["Italo"]] == ["Italo"]
        assert [p.display_order for p in profiles_by_user["Italo"]] == [0]
        assert [p.name for p in profiles_by_user["Ana"]] == ["Ana"]
        # Each profile belongs to its namesake user.
        italo_user = next(u for u in users if u.username == "Italo")
        ana_user = next(u for u in users if u.username == "Ana")
        for p in profiles_by_user["Italo"]:
            assert p.user_id == italo_user.id, (
                f"profile {p.name!r} must be owned by Italo, got user_id={p.user_id}"
            )
        for p in profiles_by_user["Ana"]:
            assert p.user_id == ana_user.id, (
                f"profile {p.name!r} must be owned by Ana, got user_id={p.user_id}"
            )
        # F07 — Família sentinel exists, owned by the no-password
        # ``family`` user, with the canonical flag set.
        family_user = next(u for u in users if u.username == "family")
        assert family_user.password_hash == "", (
            "the Família sentinel user must have an empty password_hash (cannot authenticate)"
        )
        sentinel_profiles = family_user.profiles
        assert [p.name for p in sentinel_profiles] == ["Família"], (
            f"family user must own exactly the Família sentinel, "
            f"got {[p.name for p in sentinel_profiles]!r}"
        )
        assert sentinel_profiles[0].is_family_sentinel is True
        assert sentinel_profiles[0].asset_classes == [], (
            "Família sentinel must own zero AssetClass rows"
        )


def test_seed_is_idempotent(seeded_db) -> None:
    seeded_db["seed"]()
    # Second call should detect the existing users and skip inserts.
    prior = seeded_db["seed"]()
    assert prior == 3, "second seed call should report 3 prior users"

    SessionLocal = seeded_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Profile, User

        assert session.query(User).count() == 3
        # 2 canonical real profiles (Italo + Ana) + 1 Família
        # sentinel = 3 profiles (F07). No ``Italo RF2`` fixture.
        assert session.query(Profile).count() == 3
        names = sorted(p.name for p in session.query(Profile).all())
        assert names == ["Ana", "Família", "Italo"], names


def test_seed_creates_familia_sentinel(seeded_db) -> None:
    """F07 — the Família sentinel Profile row is created on the
    first seed pass (and any pre-existing ``Italo RF2`` fixture
    row is removed so the canonical ``db-reset`` state is
    exactly 2 real profiles + 1 sentinel). The sentinel is owned
    by the password-less ``family`` user.
    """
    from omaha.db import SessionLocal
    from omaha.models import User

    prior = seeded_db["seed"]()
    assert prior == 0, "fresh DB should have no users before seed"

    db = SessionLocal()
    try:
        italo = db.query(User).filter(User.username == "Italo").one()
        assert [p.name for p in italo.profiles] == ["Italo"], (
            "Italo must own exactly one profile (the F01 fixture is retired)"
        )
        ana = db.query(User).filter(User.username == "Ana").one()
        assert [p.name for p in ana.profiles] == ["Ana"], "Ana must own exactly one profile"
        family = db.query(User).filter(User.username == "family").one()
        assert family.password_hash == "", (
            "the Família sentinel user must have an empty password_hash"
        )
        assert [p.name for p in family.profiles] == ["Família"], (
            "family user must own exactly the Família sentinel profile"
        )
        sentinel = family.profiles[0]
        assert sentinel.is_family_sentinel is True
        assert sentinel.asset_classes == [], "Família sentinel must own zero AssetClass rows"
    finally:
        db.close()


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
    # F07 — Família-as-profile sentinel column (migration 0017).
    assert "is_family_sentinel" in profile_cols, profile_cols

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
