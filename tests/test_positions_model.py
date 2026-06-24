"""Tests for T01: Position model, 0004 migration, and ORM semantics.

Five test cases, each backed by its own temporary SQLite database:

1. ``test_alembic_upgrade_creates_positions_table`` — running
   ``alembic upgrade head`` against a fresh DB creates the
   ``positions`` table with the expected columns, unique constraint,
   indexed ``asset_id`` column, and ``ON DELETE CASCADE`` FK to
   ``assets``.
2. ``test_unique_constraint_rejects_duplicate_ticker_per_asset`` —
   saving two :class:`Position` rows with the same
   ``(asset_id, broker_ticker)`` raises
   :class:`sqlalchemy.exc.IntegrityError` on ``commit``. The
   importer's confirm handler relies on this for idempotent
   re-imports.
3. ``test_deleting_asset_cascades_to_positions`` — removing an
   :class:`Asset` from a session flushes its positions via the
   ``ON DELETE CASCADE`` FK and the ORM ``cascade="all,
   delete-orphan"`` relationship option.
4. ``test_deleting_profile_cascades_to_positions`` — removing a
   :class:`Profile` cascades to its classes (S02 CASCADE), to the
   classes' assets (S03 CASCADE), and finally to the assets'
   positions (S04 CASCADE). Full cascade chain proof.

The DB-targeted tests use a per-test temporary SQLite file via the
``DATABASE_URL`` env var, mirroring the pattern in
``test_assets_model.py``. ``omaha.config.settings`` is rebuilt
lazily (``omaha.db`` reads ``DATABASE_URL`` at import time) so we
have to drop the cached ``omaha.*`` modules and reimport them per
test.
"""

from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
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


def _make_asset(session, klass, name: str = "Tesouro Selic 2029", display_order: int = 0) -> object:
    """Create and persist a parent Asset row so positions have an FK target."""
    from omaha.models import Asset

    asset = Asset(
        asset_class_id=klass.id,
        name=name,
        display_order=display_order,
    )
    session.add(asset)
    session.flush()
    return asset


def test_alembic_upgrade_creates_positions_table(omaha_db) -> None:
    """`alembic upgrade head` adds positions with the right shape.

    The migration is hand-written (matching the 0001/0002/0003
    style) so a schema-level inspection must see: the seven expected
    columns, a UNIQUE on ``(asset_id, broker_ticker)`` named
    ``uq_position_asset_ticker``, an index on ``asset_id``, and a FK
    to ``assets.id`` with ``ON DELETE CASCADE``. ``NOT NULL`` is
    asserted for every non-id column to match the plan.
    """
    db_path = omaha_db["db_path"]
    assert db_path.exists(), "alembic should have created the SQLite file"

    engine = create_engine(omaha_db["db_url"])
    inspector = inspect(engine)
    try:
        table_names = set(inspector.get_table_names())
        assert {
            "users",
            "profiles",
            "asset_classes",
            "assets",
            "positions",
        }.issubset(table_names), table_names

        # Columns — assert the exact column set is present and that
        # every non-id column is NOT NULL (matches the plan).
        positions_cols = {c["name"]: c for c in inspector.get_columns("positions")}
        expected = {
            "id",
            "asset_id",
            "qty",
            "avg_price",
            "current_price",
            "broker_ticker",
            "imported_at",
        }
        assert expected.issubset(positions_cols.keys()), positions_cols
        for col_name in (
            "asset_id",
            "qty",
            "avg_price",
            "current_price",
            "broker_ticker",
            "imported_at",
        ):
            assert positions_cols[col_name]["nullable"] is False, (
                f"positions.{col_name} must be NOT NULL, got {positions_cols[col_name]!r}"
            )

        # Unique constraint on (asset_id, broker_ticker)
        unique_constraints = inspector.get_unique_constraints("positions")
        constraint_names = {uc["name"] for uc in unique_constraints}
        assert "uq_position_asset_ticker" in constraint_names, unique_constraints

        # FK with ON DELETE CASCADE
        fks = inspector.get_foreign_keys("positions")
        assert any(
            fk["constrained_columns"] == ["asset_id"]
            and fk["referred_table"] == "assets"
            and fk.get("options", {}).get("ondelete", "").upper() == "CASCADE"
            for fk in fks
        ), fks

        # Index on asset_id
        indexes = inspector.get_indexes("positions")
        assert any(
            idx["name"] == "ix_positions_asset_id" and idx["column_names"] == ["asset_id"]
            for idx in indexes
        ), indexes
    finally:
        engine.dispose()


def test_unique_constraint_rejects_duplicate_ticker_per_asset(omaha_db) -> None:
    """Two positions with the same (asset_id, broker_ticker) must not persist.

    The first insert goes through; the second commit raises
    ``IntegrityError`` because of ``uq_position_asset_ticker``. The
    importer confirm handler depends on this for safe re-imports of
    the same CSV — duplicates must collapse to a single row per
    (asset, ticker) pair.
    """
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session)
        klass = _make_class(session, profile)
        asset = _make_asset(session, klass)
        from omaha.models import Position

        session.add(
            Position(
                asset_id=asset.id,
                qty=Decimal("10.0000"),
                avg_price=Decimal("100.0000"),
                current_price=Decimal("105.0000"),
                broker_ticker="PETR4",
            )
        )
        session.commit()
        asset_id = asset.id

    with SessionLocal() as session:
        from omaha.models import Asset, Position

        asset_row = session.get(Asset, asset_id)
        assert asset_row is not None
        session.add(
            Position(
                asset_id=asset_row.id,
                qty=Decimal("20.0000"),  # different qty
                avg_price=Decimal("200.0000"),
                current_price=Decimal("210.0000"),
                broker_ticker="PETR4",  # same broker_ticker under same asset
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Sanity: only the original row remains, with the original qty.
    with SessionLocal() as session:
        from omaha.models import Position

        rows = session.query(Position).all()
        assert len(rows) == 1
        assert rows[0].qty == Decimal("10.0000")
        assert rows[0].broker_ticker == "PETR4"

    # And the same broker_ticker is allowed for a *different* asset.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        # Re-attach the existing class and create a sibling asset
        # under the same class so we have a second FK target.
        klass_row = session.get(AssetClass, klass.id)
        assert klass_row is not None
        other_asset = Asset(asset_class_id=klass_row.id, name="IVVB11", display_order=1)
        session.add(other_asset)
        session.flush()

        session.add(
            Position(
                asset_id=other_asset.id,
                qty=Decimal("5.0000"),
                avg_price=Decimal("300.0000"),
                current_price=Decimal("310.0000"),
                broker_ticker="PETR4",  # same ticker, different asset
            )
        )
        session.commit()

    with SessionLocal() as session:
        from omaha.models import Position

        assert session.query(Position).count() == 2


def test_deleting_asset_cascades_to_positions(omaha_db) -> None:
    """Deleting an asset must remove its positions (FK CASCADE)."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session, name="Ana Livia")
        klass = _make_class(session, profile)
        asset = _make_asset(session, klass)
        from omaha.models import Position

        session.add_all(
            [
                Position(
                    asset_id=asset.id,
                    qty=Decimal("10.0000"),
                    avg_price=Decimal("100.0000"),
                    current_price=Decimal("105.0000"),
                    broker_ticker="TICKER_A",
                ),
                Position(
                    asset_id=asset.id,
                    qty=Decimal("20.0000"),
                    avg_price=Decimal("200.0000"),
                    current_price=Decimal("210.0000"),
                    broker_ticker="TICKER_B",
                ),
                Position(
                    asset_id=asset.id,
                    qty=Decimal("30.0000"),
                    avg_price=Decimal("300.0000"),
                    current_price=Decimal("315.0000"),
                    broker_ticker="TICKER_C",
                ),
            ]
        )
        session.commit()
        asset_id = asset.id

    # Re-open a session and confirm the rows exist.
    with SessionLocal() as session:
        from omaha.models import Asset, Position

        assert session.query(Position).filter(Position.asset_id == asset_id).count() == 3

        asset_row = session.get(Asset, asset_id)
        assert asset_row is not None
        session.delete(asset_row)
        session.commit()

    # The position rows for that asset must be gone.
    with SessionLocal() as session:
        from omaha.models import Position

        remaining = session.query(Position).filter(Position.asset_id == asset_id).count()
        assert remaining == 0, (
            f"deleting asset {asset_id} should cascade to positions, but {remaining} rows remain"
        )


def test_deleting_profile_cascades_to_positions(omaha_db) -> None:
    """Deleting a profile cascades → classes → assets → positions (full chain)."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        profile = _make_profile(session, name="Italo")
        from omaha.models import Asset, AssetClass, Position

        klass_a = AssetClass(
            profile_id=profile.id, name="Renda Fixa", target_pct=60, display_order=0
        )
        klass_b = AssetClass(profile_id=profile.id, name="Acoes", target_pct=30, display_order=1)
        session.add_all([klass_a, klass_b])
        session.flush()

        asset_rf_1 = Asset(asset_class_id=klass_a.id, name="Tesouro Selic", display_order=0)
        asset_rf_2 = Asset(asset_class_id=klass_a.id, name="CDB Banco X", display_order=1)
        asset_ac_1 = Asset(asset_class_id=klass_b.id, name="PETR4", display_order=0)
        asset_ac_2 = Asset(asset_class_id=klass_b.id, name="IVVB11", display_order=1)
        session.add_all([asset_rf_1, asset_rf_2, asset_ac_1, asset_ac_2])
        session.flush()

        # 5 positions across 4 assets — one asset gets two positions
        # so we also exercise the "re-import as upsert" surface from
        # the same broker.
        session.add_all(
            [
                Position(
                    asset_id=asset_rf_1.id,
                    qty=Decimal("10.0000"),
                    avg_price=Decimal("100.0000"),
                    current_price=Decimal("105.0000"),
                    broker_ticker="TES_SELIC_2029",
                ),
                Position(
                    asset_id=asset_rf_2.id,
                    qty=Decimal("20.0000"),
                    avg_price=Decimal("200.0000"),
                    current_price=Decimal("210.0000"),
                    broker_ticker="CDB_BX_LIQ",
                ),
                Position(
                    asset_id=asset_ac_1.id,
                    qty=Decimal("30.0000"),
                    avg_price=Decimal("30.0000"),
                    current_price=Decimal("35.0000"),
                    broker_ticker="PETR4",
                ),
                Position(
                    asset_id=asset_ac_2.id,
                    qty=Decimal("40.0000"),
                    avg_price=Decimal("300.0000"),
                    current_price=Decimal("310.0000"),
                    broker_ticker="IVVB11",
                ),
                Position(
                    asset_id=asset_ac_1.id,
                    qty=Decimal("5.0000"),
                    avg_price=Decimal("29.5000"),
                    current_price=Decimal("35.0000"),
                    broker_ticker="PETR4_F",
                ),
            ]
        )
        session.commit()
        profile_id = profile.id
        class_ids = (klass_a.id, klass_b.id)
        asset_ids = (asset_rf_1.id, asset_rf_2.id, asset_ac_1.id, asset_ac_2.id)

    # Sanity: 2 classes, 4 assets, 5 positions are persisted.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile

        assert session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count() == 2
        assert session.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).count() == 4
        assert session.query(Position).filter(Position.asset_id.in_(asset_ids)).count() == 5

        profile_row = session.get(Profile, profile_id)
        assert profile_row is not None
        session.delete(profile_row)
        session.commit()

    # Everything underneath the deleted profile is gone: classes,
    # assets, and positions.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        assert session.query(AssetClass).filter(AssetClass.profile_id == profile_id).count() == 0
        assert session.query(Asset).filter(Asset.asset_class_id.in_(class_ids)).count() == 0
        assert session.query(Position).filter(Position.asset_id.in_(asset_ids)).count() == 0
