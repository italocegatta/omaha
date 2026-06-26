"""Tests for T01: Asset model, 0003 migration, and ORM semantics.

Five test cases, each backed by its own temporary SQLite database:

1. ``test_alembic_upgrade_creates_assets_table`` — running
   ``alembic upgrade head`` against a fresh DB creates the
   ``assets`` table with the expected columns, unique constraint,
   indexed ``asset_class_id`` column, and ``ON DELETE CASCADE`` FK
   to ``asset_classes``.
2. ``test_unique_constraint_rejects_duplicate_name_in_class`` —
   saving two :class:`Asset` rows with the same
   ``(asset_class_id, name)`` raises
   :class:`sqlalchemy.exc.IntegrityError` on ``commit``.
3. ``test_deleting_asset_class_cascades_to_assets`` — removing an
   :class:`AssetClass` from a session flushes its assets via the
   ``ON DELETE CASCADE`` FK and the ORM ``cascade="all,
   delete-orphan"`` relationship option.
4. ``test_deleting_profile_cascades_to_assets`` — removing a
   :class:`Profile` cascades to its classes (S02 CASCADE) and then
   to the classes' assets (S03 CASCADE), so the assets are gone
   too. Full cascade chain proof.

The DB-targeted tests use a per-test temporary SQLite file via the
``DATABASE_URL`` env var, mirroring the pattern in
``test_classes_model.py``. ``omaha.config.settings`` is rebuilt
lazily (``omaha.db`` reads ``DATABASE_URL`` at import time) so we
have to drop the cached ``omaha.*`` modules and reimport them per
test.
"""

from __future__ import annotations

import os
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


def _restore_omaha_modules(saved: dict[str, object]) -> None:
    """Re-populate ``sys.modules`` with the omaha.* modules saved before the fixture.

    Drop any modules that the fixture re-imported (so we don't keep
    stale env-bound copies in ``sys.modules``), then restore the
    pre-fixture snapshot. Without this, subsequent tests sharing the
    session-scoped ``_omaha_test_env`` get the wrong DB engine.
    """
    for name in list(sys.modules):
        if (name == "omaha" or name.startswith("omaha.")) and name not in saved:
            del sys.modules[name]
    for name, mod in saved.items():
        sys.modules[name] = mod


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
    assert result.returncode == 0, (
        f"alembic upgrade head failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    for mod_name in list(sys.modules):
        if mod_name == "omaha" or mod_name.startswith("omaha."):
            del sys.modules[mod_name]
    import omaha.config  # noqa: F401 — populates settings
    import omaha.db  # noqa: F401 — populates engine + SessionLocal
    import omaha.models  # noqa: F401 — registers tables on Base


@pytest.fixture()
def omaha_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> dict[str, object]:
    """Yield a bootstrapped ``omaha`` stack backed by a fresh SQLite file.

    Returns the SessionLocal factory, the db path, and the db URL so
    tests can inspect the schema with a fresh engine (the in-process
    engine from ``omaha.db`` is tied to the SessionLocal sessions).

    Restores the pre-existing ``omaha.*`` modules on teardown so the
    conftest's session-scoped ``_omaha_test_env`` modules are
    available for subsequent tests in the session.
    """
    saved_omaha_modules = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "omaha" or name.startswith("omaha.")
    }

    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-t01")

    _bootstrap_omaha_for_db(db_url)

    import omaha.db
    import omaha.models

    request.addfinalizer(lambda: _restore_omaha_modules(saved_omaha_modules))

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


def _make_class(session, profile, name: str = "Renda Fixa", target_pct: int = 60) -> object:
    """Create and persist a parent AssetClass row so assets have an FK target."""
    from omaha.models import AssetClass

    klass = AssetClass(profile_id=profile.id, name=name, target_pct=target_pct, display_order=0)
    session.add(klass)
    session.flush()
    return klass


def test_alembic_upgrade_creates_assets_table(omaha_db) -> None:
    """`alembic upgrade head` adds assets with the right shape.

    The migration is hand-written (matching the 0001/0002 style) so a
    schema-level inspection must see: the five expected columns, a
    UNIQUE on ``(asset_class_id, name)`` named
    ``uq_asset_asset_class_name``, an index on ``asset_class_id``,
    and a FK to ``asset_classes.id`` with ``ON DELETE CASCADE``.
    """
    db_path = omaha_db["db_path"]
    assert db_path.exists(), "alembic should have created the SQLite file"

    engine = create_engine(omaha_db["db_url"])
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
        assert {"users", "profiles", "asset_classes", "assets"}.issubset(table_names), table_names

        # Columns
        asset_cols = {c["name"] for c in inspector.get_columns("assets")}
        assert {"id", "asset_class_id", "name", "display_order", "created_at"}.issubset(
            asset_cols
        ), asset_cols
        # asset-trade-flags: three new trade-control columns land
        # via the 0016 migration; verify they made it onto the
        # table along with the rest of the columns.
        assert {"buy_enabled", "sell_enabled", "currency_code"}.issubset(asset_cols), asset_cols

        # Unique constraint
        unique_constraints = inspector.get_unique_constraints("assets")
        constraint_names = {uc["name"] for uc in unique_constraints}
        assert "uq_asset_asset_class_name" in constraint_names, unique_constraints

        # FK with ON DELETE CASCADE
        fks = inspector.get_foreign_keys("assets")
        assert any(
            fk["constrained_columns"] == ["asset_class_id"]
            and fk["referred_table"] == "asset_classes"
            and fk.get("options", {}).get("ondelete", "").upper() == "CASCADE"
            for fk in fks
        ), fks

        # Index on asset_class_id
        indexes = inspector.get_indexes("assets")
        assert any(
            idx["name"] == "ix_assets_asset_class_id" and idx["column_names"] == ["asset_class_id"]
            for idx in indexes
        ), indexes
    finally:
        engine.dispose()


def test_unique_constraint_rejects_duplicate_name_in_class(omaha_db) -> None:
    """Two assets with the same name under one class must not persist.

    The first insert goes through; the second commit raises
    ``IntegrityError`` because of ``uq_asset_asset_class_name``.
    """
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session)
        klass = _make_class(session, profile)
        from omaha.models import Asset

        session.add(
            Asset(
                asset_class_id=klass.id,
                name="Tesouro Selic 2029",
                display_order=0,
            )
        )
        session.commit()
        klass_id = klass.id

    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass

        klass_row = session.get(AssetClass, klass_id)
        assert klass_row is not None
        session.add(
            Asset(
                asset_class_id=klass_row.id,
                name="Tesouro Selic 2029",  # same name
                display_order=1,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Sanity: only the original row remains.
    with SessionLocal() as session:
        from omaha.models import Asset

        rows = session.query(Asset).all()
        assert len(rows) == 1
        assert rows[0].display_order == 0


def test_deleting_asset_class_cascades_to_assets(omaha_db) -> None:
    """Deleting an asset class must remove its assets (FK CASCADE)."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session, name="Ana Livia")
        klass = _make_class(session, profile)
        from omaha.models import Asset

        session.add_all(
            [
                Asset(
                    asset_class_id=klass.id,
                    name="Tesouro Selic 2029",
                    display_order=0,
                ),
                Asset(
                    asset_class_id=klass.id,
                    name="Tesouro IPCA 2035",
                    display_order=1,
                ),
                Asset(
                    asset_class_id=klass.id,
                    name="CDB Liquidez 2026",
                    display_order=2,
                ),
            ]
        )
        session.commit()
        class_id = klass.id

    # Re-open a session and confirm the rows exist.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass

        assert session.query(Asset).filter(Asset.asset_class_id == class_id).count() == 3

        class_row = session.get(AssetClass, class_id)
        assert class_row is not None
        session.delete(class_row)
        session.commit()

    # The asset rows for that class must be gone.
    with SessionLocal() as session:
        from omaha.models import Asset

        remaining = session.query(Asset).filter(Asset.asset_class_id == class_id).count()
        assert remaining == 0, (
            f"deleting asset_class {class_id} should cascade to assets, but {remaining} rows remain"
        )


def test_deleting_profile_cascades_to_assets(omaha_db) -> None:
    """Deleting a profile cascades → classes → assets (full chain)."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session, name="Italo")
        from omaha.models import Asset, AssetClass

        klass_a = AssetClass(
            profile_id=profile.id, name="Renda Fixa", target_pct=60, display_order=0
        )
        klass_b = AssetClass(profile_id=profile.id, name="Acoes", target_pct=30, display_order=1)
        session.add_all([klass_a, klass_b])
        session.flush()

        session.add_all(
            [
                Asset(asset_class_id=klass_a.id, name="Tesouro Selic", display_order=0),
                Asset(asset_class_id=klass_a.id, name="CDB Banco X", display_order=1),
                Asset(asset_class_id=klass_b.id, name="PETR4", display_order=0),
                Asset(asset_class_id=klass_b.id, name="IVVB11", display_order=1),
            ]
        )
        session.commit()
        profile_id = profile.id
        class_ids = (klass_a.id, klass_b.id)

    # Sanity: 2 classes and 4 assets are persisted.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Profile

        assert session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count() == 2
        assert session.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).count() == 4

        profile_row = session.get(Profile, profile_id)
        assert profile_row is not None
        session.delete(profile_row)
        session.commit()

    # All classes and all assets underneath the deleted profile are gone.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass

        assert session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count() == 0
        assert session.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).count() == 0
