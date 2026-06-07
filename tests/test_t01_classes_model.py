"""Tests for T01: AssetClass model, 0002 migration, and ORM semantics.

Four test cases, each backed by its own temporary SQLite database:

1. ``test_alembic_upgrade_creates_asset_classes_table`` — running
   ``alembic upgrade head`` against a fresh DB creates the
   ``asset_classes`` table with the expected columns, unique
   constraint, indexed ``profile_id`` column, and ``ON DELETE
   CASCADE`` FK to ``profiles``.
2. ``test_unique_constraint_rejects_duplicate_name`` — saving two
   :class:`AssetClass` rows with the same ``(profile_id, name)``
   raises :class:`sqlalchemy.exc.IntegrityError` on ``commit``.
3. ``test_deleting_profile_cascades_to_asset_classes`` — removing a
   :class:`Profile` from a session flushes its classes via the
   ``ON DELETE CASCADE`` FK and the ORM ``cascade="all,
   delete-orphan"`` relationship option.
4. ``test_repr_round_trip`` — :meth:`AssetClass.__repr__` formats the
   class id, profile id, name, and target_pct.

The DB-targeted tests use a per-test temporary SQLite file via the
``DATABASE_URL`` env var, mirroring the pattern in
``test_t02_seed.py``. ``omaha.config.settings`` is rebuilt lazily
(``omaha.db`` reads ``DATABASE_URL`` at import time) so we have to
drop the cached ``omaha.*`` modules and reimport them per test.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

REPO_ROOT = Path(__file__).resolve().parent.parent


def _tmp_db_url(tmp_path: Path) -> str:
    """Return a ``sqlite:///`` URL pointing to a fresh file in ``tmp_path``."""
    db_file = tmp_path / "portfolio.db"
    return f"sqlite:///{db_file}"


def _bootstrap_omaha_for_db(
    db_url: str,
    *,
    admin_password: str = "test-family-password",
    secret_key: str = "test-secret-key-for-t01",
) -> None:
    """Set env vars, run ``alembic upgrade head``, then reimport omaha.

    Idempotent: drops every ``omaha.*`` entry from ``sys.modules`` so
    the next import reads the freshly-set env. The subprocess running
    ``alembic`` inherits the same env, including ``SECRET_KEY`` which
    ``omaha.config._is_test_mode`` requires to skip its pytest guard.
    """
    os.environ["DATABASE_URL"] = db_url
    os.environ["ADMIN_PASSWORD"] = admin_password
    os.environ["SECRET_KEY"] = secret_key

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": admin_password,
            "SECRET_KEY": secret_key,
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert (
        result.returncode == 0
    ), f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"

    for mod_name in list(sys.modules):
        if mod_name == "omaha" or mod_name.startswith("omaha."):
            del sys.modules[mod_name]
    import omaha.config  # noqa: F401 — populates settings
    import omaha.db  # noqa: F401 — populates engine + SessionLocal
    import omaha.models  # noqa: F401 — registers tables on Base


@pytest.fixture()
def omaha_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Yield a bootstrapped ``omaha`` stack backed by a fresh SQLite file.

    Returns the SessionLocal factory, the db path, and the db URL so
    tests can inspect the schema with a fresh engine (the in-process
    engine from ``omaha.db`` is tied to the SessionLocal sessions).
    """
    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-t01")

    _bootstrap_omaha_for_db(db_url)

    import omaha.db
    import omaha.models

    return {
        "db_path": Path(urlparse(db_url).path),
        "db_url": db_url,
        "SessionLocal": omaha.db.SessionLocal,
    }


def _make_profile(session, name: str = "Italo") -> object:
    """Create and persist a parent Profile row for FK-scoped tests."""
    from omaha.models import Profile, User

    user = User(username=f"user-for-{name}", password_hash="not-a-real-hash")
    session.add(user)
    session.flush()
    profile = Profile(user_id=user.id, name=name, display_order=0)
    session.add(profile)
    session.flush()
    return profile


def test_alembic_upgrade_creates_asset_classes_table(omaha_db) -> None:
    """`alembic upgrade head` adds asset_classes with the right shape.

    The migration is hand-written (matching the 0001 style) so a
    schema-level inspection must see: the four expected columns, a
    UNIQUE on ``(profile_id, name)`` named ``uq_asset_class_profile_name``,
    an index on ``profile_id``, and a FK to ``profiles.id`` with
    ``ON DELETE CASCADE``.
    """
    db_path = omaha_db["db_path"]
    assert db_path.exists(), "alembic should have created the SQLite file"

    engine = create_engine(omaha_db["db_url"])
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
        assert {"users", "profiles", "asset_classes"}.issubset(table_names), table_names

        # Columns
        class_cols = {c["name"] for c in inspector.get_columns("asset_classes")}
        assert {"id", "profile_id", "name", "target_pct", "display_order", "created_at"}.issubset(
            class_cols
        ), class_cols

        # Numeric(5, 2) for target_pct: total 5 digits, 2 after the point.
        target_pct_col = next(
            c for c in inspector.get_columns("asset_classes") if c["name"] == "target_pct"
        )
        assert "NUMERIC" in str(target_pct_col["type"]).upper(), target_pct_col

        # Unique constraint
        unique_constraints = inspector.get_unique_constraints("asset_classes")
        constraint_names = {uc["name"] for uc in unique_constraints}
        assert "uq_asset_class_profile_name" in constraint_names, unique_constraints

        # FK with ON DELETE CASCADE
        fks = inspector.get_foreign_keys("asset_classes")
        assert any(
            fk["constrained_columns"] == ["profile_id"]
            and fk["referred_table"] == "profiles"
            and fk.get("options", {}).get("ondelete", "").upper() == "CASCADE"
            for fk in fks
        ), fks

        # Index on profile_id
        indexes = inspector.get_indexes("asset_classes")
        assert any(
            idx["name"] == "ix_asset_classes_profile_id" and idx["column_names"] == ["profile_id"]
            for idx in indexes
        ), indexes
    finally:
        engine.dispose()


def test_unique_constraint_rejects_duplicate_name(omaha_db) -> None:
    """Two classes with the same name under one profile must not persist.

    The first insert goes through; the second commit raises
    ``IntegrityError`` because of ``uq_asset_class_profile_name``.
    """
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session)
        from omaha.models import AssetClass

        session.add(
            AssetClass(
                profile_id=profile.id,
                name="Renda Fixa",
                target_pct=60,
                display_order=0,
            )
        )
        session.commit()

    with SessionLocal() as session:
        profile = session.merge(profile)  # reattach after the first commit
        from omaha.models import AssetClass

        session.add(
            AssetClass(
                profile_id=profile.id,
                name="Renda Fixa",  # same name
                target_pct=30,
                display_order=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Sanity: only the original row remains.
    with SessionLocal() as session:
        from omaha.models import AssetClass

        rows = session.query(AssetClass).all()
        assert len(rows) == 1
        assert rows[0].target_pct == 60


def test_deleting_profile_cascades_to_asset_classes(omaha_db) -> None:
    """Deleting a profile must remove its asset_classes (FK CASCADE)."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session, name="Ana Livia")
        from omaha.models import AssetClass

        session.add_all(
            [
                AssetClass(
                    profile_id=profile.id,
                    name="Renda Fixa",
                    target_pct=60,
                    display_order=0,
                ),
                AssetClass(
                    profile_id=profile.id,
                    name="Acoes",
                    target_pct=30,
                    display_order=1,
                ),
                AssetClass(
                    profile_id=profile.id,
                    name="Reserva",
                    target_pct=10,
                    display_order=2,
                ),
            ]
        )
        session.commit()
        profile_id = profile.id

    # Re-open a session and confirm the rows exist.
    with SessionLocal() as session:
        from omaha.models import AssetClass, Profile

        assert session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count() == 3

        profile_row = session.get(Profile, profile_id)
        assert profile_row is not None
        session.delete(profile_row)
        session.commit()

    # The asset_classes rows for that profile must be gone.
    with SessionLocal() as session:
        from omaha.models import AssetClass

        remaining = session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count()
        assert remaining == 0, (
            f"deleting profile {profile_id} should cascade to asset_classes, "
            f"but {remaining} rows remain"
        )


def test_repr_round_trip(omaha_db) -> None:
    """AssetClass.__repr__ must include id, profile_id, name, and target_pct."""
    instance_repr = (
        "AssetClass(id=42, profile_id=7, name='Renda Fixa', target_pct=Decimal('60.00'))"
    )
    # Build the expected string with whatever Decimal repr SQLAlchemy uses.
    from decimal import Decimal

    from omaha.models import AssetClass

    obj = AssetClass(
        id=42,
        profile_id=7,
        name="Renda Fixa",
        target_pct=Decimal("60.00"),
        display_order=0,
    )
    rendered = repr(obj)
    # Required substrings — independent of Decimal repr style and dict ordering.
    for needle in ("AssetClass(", "id=42", "profile_id=7", "name='Renda Fixa'"):
        assert needle in rendered, f"missing {needle!r} in {rendered!r}"
    # target_pct must appear in some recognisable form (60 or 60.00).
    assert re.search(r"target_pct=Decimal\(['\"]60(\.0+)?['\"]\)", rendered), rendered
    # And the canonical literal we hand-built above must equal the real repr.
    assert rendered == instance_repr, f"{rendered!r} != {instance_repr!r}"
