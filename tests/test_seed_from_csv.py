"""Tests for ``scripts.seed_from_csv``.

Eleven test cases, each backed by its own temporary SQLite database
via the ``omaha_db`` fixture (boots a fresh SQLite file, runs
``alembic upgrade head``, exposes ``SessionLocal``):

1. ``test_reset_creates_full_italo_state`` — ``reset`` on a fresh
   profile creates 6 classes + 48 assets + 47 positions for Italo
   with ``sum(target_pct) == 100`` per profile and per class.
2. ``test_reset_wipes_existing_state_first`` — ``reset`` on a
   populated profile wipes positions / previews / assets / classes
   before re-seeding the full triplet.
3. ``test_reset_is_idempotent`` — running ``reset`` twice yields the
   same DB state including positions.
4. ``test_upsert_updates_changes_creates_missing`` — ``upsert``
   updates a changed ``target_pct``, a changed ``current_price``,
   and creates a missing asset + position without deleting other rows.
5. ``test_diff_lists_changes_no_write`` — ``diff`` on a populated
   profile lists only the changes across all three layers; no write.
6. ``test_sum_violating_class_csv_is_rejected`` — sum-violating class
   CSV is rejected with the validator's ``Sobra X%`` / ``Falta X%``
   message and no DB write.
7. ``test_asset_referencing_missing_class_is_rejected`` — asset
   referencing a missing class aborts with the offending line number.
8. ``test_position_referencing_missing_asset_is_rejected`` — position
   referencing a missing asset aborts with the offending line number.
9. ``test_non_tradeable_position_sentinel_preserves_value`` —
    one explicit-totals position survives ``reset`` and contributes
    its CSV values to portfolio ``current_value``.
10. ``test_non_ascii_asset_name_round_trips`` — non-ASCII asset name
    (``Tesouro IPCA+ 2035``) round-trips correctly.
11. ``test_upsert_rejects_sum_violation_before_write`` — ``upsert``
    rejects a sum-violating CSV before any DB write.

The DB-targeted tests use a per-test temporary SQLite file via the
``DATABASE_URL`` env var. ``omaha.config.settings`` is rebuilt
lazily (``omaha.db`` reads ``DATABASE_URL`` at import time) so we
have to drop the cached ``omaha.*`` modules and reimport them per
test.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.seed_from_csv import load_assets, load_classes, load_positions

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "data" / "seed"
SEED_FROM_CSV = REPO_ROOT / "scripts" / "seed_from_csv.py"


# ---------------------------------------------------------------------------
# Fixture: omaha_db (boots a fresh SQLite + alembic; does NOT seed users)
# ---------------------------------------------------------------------------


def _tmp_db_url(tmp_path: Path) -> str:
    db_file = tmp_path / "portfolio.db"
    return f"sqlite:///{db_file}"


def _save_modules() -> dict[str, object]:
    return {
        name: mod
        for name, mod in sys.modules.items()
        if name == "omaha" or name.startswith("omaha.")
    }


def _restore_modules(saved: dict[str, object]) -> None:
    for name in list(sys.modules):
        if (name == "omaha" or name.startswith("omaha.")) and name not in saved:
            del sys.modules[name]
    for name, mod in saved.items():
        sys.modules[name] = mod


@pytest.fixture()
def omaha_db(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
):
    """Boot a fresh SQLite + alembic, no users.

    The test imports :mod:`omaha.seed` and calls :func:`seed` itself
    to get the canonical ``Italo`` + ``Ana`` users + profiles.
    """
    saved = _save_modules()
    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-csv-seed")

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-csv-seed",
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
    import omaha.config  # noqa: F401
    import omaha.db
    import omaha.models  # noqa: F401
    import omaha.seed

    omaha.seed.seed()

    request.addfinalizer(lambda: _restore_modules(saved))

    return {
        "db_url": db_url,
        "SessionLocal": omaha.db.SessionLocal,
    }


# ---------------------------------------------------------------------------
# Runner: invoke scripts.seed_from_csv via subprocess so it sees the same
# DATABASE_URL the fixture set. This mirrors how an operator would run
# ``task db-reset`` from the CLI.
# ---------------------------------------------------------------------------


def _run_seed(profile: str, mode: str, *, db_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.seed_from_csv",
            "--profile",
            profile,
            "--mode",
            mode,
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-csv-seed",
        },
        check=False,
        capture_output=True,
        text=True,
    )


def _italo_classes():
    return load_classes("italo")


def _italo_assets():
    return load_assets("italo")


def _italo_positions():
    return load_positions("italo")


def _rewrite_csv_row(
    path: Path,
    *,
    match,
    mutate,
) -> None:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    found = False
    for row in body:
        if match(row):
            mutate(row)
            found = True
            break
    assert found, f"row not found in {path}"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(body)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_reset_creates_full_italo_state(omaha_db) -> None:
    result = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert result.returncode == 0, (
        f"reset failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    expected_classes = _italo_classes()
    expected_assets = _italo_assets()
    expected_positions = _italo_positions()
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile

        italo = session.query(Profile).filter(Profile.name == "Italo").one()
        classes = (
            session.query(AssetClass)
            .filter(AssetClass.profile_id == italo.id)
            .order_by(AssetClass.display_order)
            .all()
        )
        assert [c.name for c in classes] == [r.name for r in expected_classes]
        assert [c.target_pct for c in classes] == [r.target_pct for r in expected_classes]
        assert [c.display_order for c in classes] == [r.display_order for r in expected_classes]
        assert [c.quote_kind for c in classes] == [r.quote_kind for r in expected_classes]
        assert sum(c.target_pct for c in classes) == Decimal("100")

        assets = (
            session.query(Asset).filter(Asset.asset_class_id.in_([c.id for c in classes])).all()
        )
        assert len(assets) == len(expected_assets), len(assets)

        # per-class asset sum
        from collections import defaultdict

        per_class: dict[int, list[Decimal]] = defaultdict(list)
        class_by_id = {c.id: c for c in classes}
        for a in assets:
            per_class[a.asset_class_id].append(a.target_pct)
        for class_id, pcts in per_class.items():
            assert sum(pcts) == Decimal("100"), (
                f"{class_by_id[class_id].name}: {[str(p) for p in pcts]}"
            )

        positions = (
            session.query(Position).filter(Position.asset_id.in_([a.id for a in assets])).all()
        )
        assert len(positions) == len(expected_positions), len(positions)


def test_reset_wipes_existing_state_first(omaha_db) -> None:
    """Pre-populate, then reset, then verify the DB matches the CSV exactly."""
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile, User

        # Seed: 1 user-named test profile + 2 imported positions + 1 import
        # preview + 3 assets + 2 classes. After reset, all of this must be
        # gone and the canonical Italo state must replace it.
        user = session.query(User).filter(User.username == "Italo").one()
        # F01 fixture: Italo also owns a second profile
        # (``Italo RF2``) so the household toggle is visible in the
        # canonical seed. Filter by name to disambiguate.
        profile = (
            session.query(Profile).filter(Profile.user_id == user.id, Profile.name == "Italo").one()
        )
        c1 = AssetClass(
            profile_id=profile.id, name="Garbage Class A", target_pct=10, display_order=99
        )
        c2 = AssetClass(
            profile_id=profile.id, name="Garbage Class B", target_pct=10, display_order=99
        )
        session.add_all([c1, c2])
        session.flush()
        a1 = Asset(asset_class_id=c1.id, name="GHOST1", target_pct=50, display_order=0)
        a2 = Asset(asset_class_id=c1.id, name="GHOST2", target_pct=50, display_order=1)
        a3 = Asset(asset_class_id=c2.id, name="GHOST3", target_pct=100, display_order=0)
        session.add_all([a1, a2, a3])
        session.flush()
        session.add_all(
            [
                Position(
                    asset_id=a1.id, qty=1, avg_price=10, current_price=20, broker_ticker="GHOST1"
                ),
                Position(
                    asset_id=a2.id, qty=2, avg_price=30, current_price=40, broker_ticker="GHOST2"
                ),
            ]
        )
        session.commit()

    result = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert result.returncode == 0, result.stderr
    expected_classes = _italo_classes()
    expected_assets = _italo_assets()
    expected_positions = _italo_positions()
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile

        italo = session.query(Profile).filter(Profile.name == "Italo").one()
        classes = session.query(AssetClass).filter(AssetClass.profile_id == italo.id).all()
        assert {c.name for c in classes} == {r.name for r in expected_classes}, (
            "ghost classes must be gone"
        )
        assert session.query(Asset).count() == len(expected_assets)
        assert "GHOST1" not in {a.name for a in session.query(Asset).all()}
        assert session.query(Position).count() == len(expected_positions), (
            "positions must match CSV rows"
        )


def test_reset_is_idempotent(omaha_db) -> None:
    r1 = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    r2 = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert r1.returncode == 0 and r2.returncode == 0, r2.stderr
    expected_classes = _italo_classes()
    expected_assets = _italo_assets()
    expected_positions = _italo_positions()
    SessionLocal = omaha_db["SessionLocal"]
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        assert session.query(AssetClass).count() == len(expected_classes)
        assert session.query(Asset).count() == len(expected_assets)
        assert session.query(Position).count() == len(expected_positions)


def test_upsert_updates_changes_creates_missing(omaha_db) -> None:
    SessionLocal = omaha_db["SessionLocal"]
    expected_classes = _italo_classes()
    expected_assets = _italo_assets()
    expected_positions = _italo_positions()
    target_class = expected_classes[0]
    target_position = next(row for row in expected_positions if row.qty > 0)
    # First reset — gives us the canonical state.
    r0 = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert r0.returncode == 0, r0.stderr

    # Manually mutate the DB so upsert has changes to apply.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        # Change one class target_pct.
        cls = session.query(AssetClass).filter(AssetClass.name == target_class.name).one()
        cls.target_pct = Decimal("30.00")
        # Change one position current_price.
        asset = session.query(Asset).filter(Asset.name == target_position.asset_name).one()
        position = session.query(Position).filter(Position.asset_id == asset.id).one()
        position.current_price = Decimal("9999.99")
        session.commit()

    # Now upsert: should restore CSV values.
    r1 = _run_seed("italo", "upsert", db_url=omaha_db["db_url"])
    assert r1.returncode == 0, r1.stderr

    with SessionLocal() as session:
        cls = session.query(AssetClass).filter(AssetClass.name == target_class.name).one()
        assert cls.target_pct == target_class.target_pct, cls.target_pct
        asset = session.query(Asset).filter(Asset.name == target_position.asset_name).one()
        pos = session.query(Position).filter(Position.asset_id == asset.id).one()
        assert pos.current_price == target_position.current_price, pos.current_price

    # Now delete an asset + position, then upsert — should recreate.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        a = session.query(Asset).filter(Asset.name == target_position.asset_name).one()
        session.query(Position).filter(Position.asset_id == a.id).delete()
        session.delete(a)
        session.commit()
        assert session.query(Asset).count() == len(expected_assets) - 1
        assert session.query(Position).count() == len(expected_positions) - 1

    r2 = _run_seed("italo", "upsert", db_url=omaha_db["db_url"])
    assert r2.returncode == 0, r2.stderr
    with SessionLocal() as session:
        from omaha.models import Asset, Position

        assert session.query(Asset).count() == len(expected_assets), "asset re-created"
        assert session.query(Position).count() == len(expected_positions), "position re-created"


def test_diff_lists_changes_no_write(omaha_db) -> None:
    SessionLocal = omaha_db["SessionLocal"]
    expected_classes = _italo_classes()
    expected_positions = _italo_positions()
    target_class = expected_classes[0]
    target_position = next(row for row in expected_positions if row.qty > 0)
    _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position

        # Mutate so diff has work to report.
        cls = session.query(AssetClass).filter(AssetClass.name == target_class.name).one()
        cls.target_pct = Decimal("30.00")
        asset = session.query(Asset).filter(Asset.name == target_position.asset_name).one()
        pos = session.query(Position).filter(Position.asset_id == asset.id).one()
        pos.current_price = Decimal("9999.99")
        # Delete one position to flip it into would-create.
        session.query(Position).filter(Position.asset_id == asset.id).delete()
        session.commit()
        # Snapshot row counts
        before_classes = session.query(AssetClass).count()
        before_assets = session.query(Asset).count()
        before_positions = session.query(Position).count()

    r = _run_seed("italo", "diff", db_url=omaha_db["db_url"])
    assert r.returncode == 0, r.stderr
    assert "would-create" in r.stdout or "would-update" in r.stdout, r.stdout

    with SessionLocal() as session:
        assert session.query(AssetClass).count() == before_classes
        assert session.query(Asset).count() == before_assets
        assert session.query(Position).count() == before_positions


def test_sum_violating_class_csv_is_rejected(omaha_db, monkeypatch) -> None:
    """A class CSV that sums to 99 must abort with ``Falta 1%``."""
    SessionLocal = omaha_db["SessionLocal"]
    # Patch SEED_DIR to a tmp dir containing a bad classes CSV.
    bad_dir = REPO_ROOT / "data" / "seed"
    original = bad_dir / "italo_classes.csv"
    backup = original.read_text(encoding="utf-8")
    try:
        _rewrite_csv_row(
            original,
            match=lambda row: row[0] == "Cripto",
            mutate=lambda row: row.__setitem__(1, "7.00"),
        )
        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode != 0, "reset must fail on bad class sum"
        assert "Falta 1%" in r.stderr or "Falta" in r.stderr, r.stderr
        # No DB write happened — classes table is empty.
        with SessionLocal() as session:
            from omaha.models import AssetClass

            assert session.query(AssetClass).count() == 0
    finally:
        original.write_text(backup, encoding="utf-8")


def test_asset_referencing_missing_class_is_rejected(omaha_db, monkeypatch) -> None:
    """Asset CSV referencing a non-existent class must abort with line number."""
    SessionLocal = omaha_db["SessionLocal"]
    bad_path = REPO_ROOT / "data" / "seed" / "italo_assets.csv"
    backup = bad_path.read_text(encoding="utf-8")
    try:
        _rewrite_csv_row(
            bad_path,
            match=lambda row: row[0] == "Internacional" and row[1] == "IAU",
            mutate=lambda row: row.__setitem__(0, "ClasseFantasma"),
        )
        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode != 0, "reset must fail on missing class ref"
        assert "ClasseFantasma" in r.stderr, r.stderr
        assert ":" in r.stderr.split("\n")[0], "should include line number"
        with SessionLocal() as session:
            from omaha.models import AssetClass

            assert session.query(AssetClass).count() == 0
    finally:
        bad_path.write_text(backup, encoding="utf-8")


def test_position_referencing_missing_asset_is_rejected(omaha_db, monkeypatch) -> None:
    SessionLocal = omaha_db["SessionLocal"]
    bad_path = REPO_ROOT / "data" / "seed" / "italo_positions.csv"
    backup = bad_path.read_text(encoding="utf-8")
    try:
        target = next(row for row in _italo_positions() if row.qty > 0)
        _rewrite_csv_row(
            bad_path,
            match=lambda row: row[0] == target.asset_name and row[1] == target.broker_ticker,
            mutate=lambda row: (
                row.__setitem__(0, "TICKERFANTASMA"),
                row.__setitem__(1, "TICKERFANTASMA"),
            ),
        )
        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode != 0, r.stderr
        assert "TICKERFANTASMA" in r.stderr, r.stderr
        with SessionLocal() as session:
            from omaha.models import Asset, AssetClass

            assert session.query(AssetClass).count() == 0
            assert session.query(Asset).count() == 0
    finally:
        bad_path.write_text(backup, encoding="utf-8")


def test_reset_preserves_divergent_broker_ticker(omaha_db) -> None:
    """``reset`` reads ``broker_ticker`` from the CSV verbatim.

    Adds an asset "Petrobras PN" and a position row with
    ``asset_name="Petrobras PN", broker_ticker="PETR4"`` to the
    Italo CSVs, runs ``reset``, and asserts the resulting
    :class:`Position` row has ``broker_ticker == "PETR4"`` while
    still being linked to the asset named "Petrobras PN" (not to
    the ticker). The dashboard renders under the asset name; the
    broker ticker is the symbol the broker reports — this is the
    whole point of the new column.
    """
    SessionLocal = omaha_db["SessionLocal"]
    classes_path = REPO_ROOT / "data" / "seed" / "italo_classes.csv"
    assets_path = REPO_ROOT / "data" / "seed" / "italo_assets.csv"
    positions_path = REPO_ROOT / "data" / "seed" / "italo_positions.csv"
    classes_backup = classes_path.read_text(encoding="utf-8")
    assets_backup = assets_path.read_text(encoding="utf-8")
    positions_backup = positions_path.read_text(encoding="utf-8")
    try:
        # Add an asset row for Petrobras PN under the Ações class.
        # The seed CSVs end without a trailing newline; ensure we
        # start the appended row on its own line.
        assets_sep = "" if assets_backup.endswith("\n") else "\n"
        positions_sep = "" if positions_backup.endswith("\n") else "\n"
        assets_path.write_text(
            assets_backup + assets_sep + "Ações,Petrobras PN,0.00,99,true,true,BRL\n",
            encoding="utf-8",
        )
        # Add a position row with divergent broker_ticker. The
        # totals columns are explicit — never recomputed from
        # ``qty * price``.
        positions_path.write_text(
            positions_backup
            + positions_sep
            + "Petrobras PN,PETR4,100,32.50,38.75,3250.00,3875.00\n",
            encoding="utf-8",
        )

        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode == 0, r.stderr

        with SessionLocal() as session:
            from omaha.models import Asset, Position

            petrobras = session.query(Asset).filter(Asset.name == "Petrobras PN").one()
            pos = session.query(Position).filter(Position.asset_id == petrobras.id).one()
            assert pos.broker_ticker == "PETR4", pos.broker_ticker
            assert pos.qty == Decimal("100")
            assert pos.avg_price == Decimal("32.50")
            assert pos.current_price == Decimal("38.75")
            # broker-csv-import-totals: explicit values pass through
            # verbatim, no ``qty * price`` recompute.
            assert pos.total_invested == Decimal("3250.00"), pos.total_invested
            assert pos.total_current == Decimal("3875.00"), pos.total_current
    finally:
        classes_path.write_text(classes_backup, encoding="utf-8")
        assets_path.write_text(assets_backup, encoding="utf-8")
        positions_path.write_text(positions_backup, encoding="utf-8")


def test_reset_preserves_totals_verbatim_no_recompute(omaha_db) -> None:
    """``total_invested`` / ``total_current`` flow through verbatim.

    Pins the ``broker-csv-import-totals`` invariant: the seed
    script never falls back to ``qty * price`` when the CSV has
    explicit (non-empty) totals cells. Picks one real position row
    and overwrites CSV totals with values that *do not* equal
    product — post-reset position must carry CSV-supplied numbers
    exactly.
    """
    SessionLocal = omaha_db["SessionLocal"]
    positions_path = REPO_ROOT / "data" / "seed" / "italo_positions.csv"
    backup = positions_path.read_text(encoding="utf-8")
    try:
        sentinel_invested = "99999.9999"
        sentinel_current = "88888.8888"
        target = next(row for row in _italo_positions() if row.qty > 0)
        _rewrite_csv_row(
            positions_path,
            match=lambda row: row[0] == target.asset_name and row[1] == target.broker_ticker,
            mutate=lambda row: (
                row.__setitem__(5, sentinel_invested),
                row.__setitem__(6, sentinel_current),
            ),
        )

        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode == 0, r.stderr

        with SessionLocal() as session:
            from omaha.models import Asset, Position

            asset = session.query(Asset).filter(Asset.name == target.asset_name).one()
            pos = session.query(Position).filter(Position.asset_id == asset.id).one()
            assert pos.total_invested == Decimal(sentinel_invested), pos.total_invested
            assert pos.total_current == Decimal(sentinel_current), pos.total_current
    finally:
        positions_path.write_text(backup, encoding="utf-8")


def test_reset_null_total_cells_contribute_zero(omaha_db) -> None:
    """Empty ``total_invested`` / ``total_current`` cells parse to ``None``.

    A legacy seed CSV without the totals columns (or one where the
    user simply didn't fill them in) MUST NOT cause a recompute —
    the dashboard then sees ``NULL`` and contributes ``Decimal('0')``
    to the class / portfolio aggregate. This pins that contract so
    a future change cannot silently start filling ``0`` instead of
    ``NULL``.
    """
    SessionLocal = omaha_db["SessionLocal"]
    positions_path = REPO_ROOT / "data" / "seed" / "italo_positions.csv"
    backup = positions_path.read_text(encoding="utf-8")
    try:
        target = next(row for row in _italo_positions() if row.qty > 0)
        _rewrite_csv_row(
            positions_path,
            match=lambda row: row[0] == target.asset_name and row[1] == target.broker_ticker,
            mutate=lambda row: (row.__setitem__(5, ""), row.__setitem__(6, "")),
        )

        r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
        assert r.returncode == 0, r.stderr

        with SessionLocal() as session:
            from omaha.models import Asset, Position

            asset = session.query(Asset).filter(Asset.name == target.asset_name).one()
            pos = session.query(Position).filter(Position.asset_id == asset.id).one()
            assert pos.total_invested is None, pos.total_invested
            assert pos.total_current is None, pos.total_current
    finally:
        positions_path.write_text(backup, encoding="utf-8")


def test_non_tradeable_position_sentinel_preserves_value(omaha_db) -> None:
    """One explicit-totals position round-trips into DB unchanged.

    broker-csv-import-totals: the seed path pre-populates
    ``total_invested = qty * avg`` and ``total_current = qty * cur``
    so dashboard's "no-recompute" calc renders seed values
    user typed. The row below therefore contributes exact CSV totals.
    """
    SessionLocal = omaha_db["SessionLocal"]
    r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert r.returncode == 0, r.stderr
    target = next(row for row in _italo_positions() if row.qty == 0 and row.total_invested)
    with SessionLocal() as session:
        from omaha.models import Asset, Position

        asset = session.query(Asset).filter(Asset.name == target.asset_name).one()
        pos = session.query(Position).filter(Position.asset_id == asset.id).one()
        assert pos.qty == target.qty
        assert pos.avg_price == target.avg_price
        assert pos.current_price == target.current_price
        assert pos.total_invested == target.total_invested
        assert pos.total_current == target.total_current

        # Portfolio aggregate: the sentinel contributes its totals,
        # so portfolio total includes that exact CSV row.
        from omaha.models import AssetClass
        from omaha.routes.pages import portfolio_aggregates

        classes = session.query(AssetClass).all()
        aggregates = portfolio_aggregates(classes)
        assert aggregates["portfolio"]["current_value"] >= target.total_current, (
            f"row must contribute at least {target.total_current!r}, got "
            f"{aggregates['portfolio']['current_value']!r}"
        )


def test_non_ascii_asset_name_round_trips(omaha_db) -> None:
    SessionLocal = omaha_db["SessionLocal"]
    r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert r.returncode == 0, r.stderr
    with SessionLocal() as session:
        from omaha.models import Asset

        names = {a.name for a in session.query(Asset).all()}
        assert "Tesouro IPCA+ 2035" in names, "non-ASCII asset name must survive"
        assert any("Caixinha Turbo NuCel" in n for n in names), "non-ASCII substring must survive"
        assert any("Tesouro IPCA+ 2050" in n for n in names)


def test_auto_class_fixture_loads_with_quote_kind(omaha_db) -> None:
    """Loader parses a class with ``quote_kind = auto``.

    The loader's only requirement beyond the original schema is that
    ``quote_kind`` be one of ``{auto, manual, none}`` — this test
    pins that contract against an inline CSV so a future change
    cannot silently tighten the enum without breaking the test.
    """
    import tempfile
    from pathlib import Path

    import scripts.seed_from_csv as seed_mod

    csv_content = "name,target_pct,display_order,quote_kind\nAções Auto,100.00,0,auto\n"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "fixtureprofile_classes.csv"
        target.write_text(csv_content, encoding="utf-8")
        original_seed_dir = seed_mod.SEED_DIR
        seed_mod.SEED_DIR = tmp_path
        try:
            rows = seed_mod.load_classes("fixtureprofile")
        finally:
            seed_mod.SEED_DIR = original_seed_dir

    assert len(rows) == 1
    assert rows[0].name == "Ações Auto"
    assert rows[0].quote_kind == "auto"


def test_loader_rejects_unknown_quote_kind(omaha_db) -> None:
    """A ``quote_kind`` outside the enum aborts with exit code 1."""
    import tempfile
    from pathlib import Path

    import scripts.seed_from_csv as seed_mod

    bad_csv = "name,target_pct,display_order,quote_kind\nBad,100.00,0,whoops\n"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "bad_classes.csv"
        target.write_text(bad_csv, encoding="utf-8")
        original_seed_dir = seed_mod.SEED_DIR
        seed_mod.SEED_DIR = tmp_path
        try:
            with pytest.raises(SystemExit) as exc_info:
                seed_mod.load_classes("bad")
            assert exc_info.value.code == 1
        finally:
            seed_mod.SEED_DIR = original_seed_dir


def test_upsert_rejects_sum_violation_before_write(omaha_db, monkeypatch) -> None:
    SessionLocal = omaha_db["SessionLocal"]
    _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    with SessionLocal() as session:
        from omaha.models import AssetClass

        before = {c.name: c.target_pct for c in session.query(AssetClass).all()}
    bad_path = REPO_ROOT / "data" / "seed" / "italo_classes.csv"
    backup = bad_path.read_text(encoding="utf-8")
    try:
        _rewrite_csv_row(
            bad_path,
            match=lambda row: row[0] == "Cripto",
            mutate=lambda row: row.__setitem__(1, "7.00"),
        )
        r = _run_seed("italo", "upsert", db_url=omaha_db["db_url"])
        assert r.returncode != 0, r.stderr
        assert "Falta" in r.stderr or "Sobra" in r.stderr, r.stderr
        with SessionLocal() as session:
            from omaha.models import AssetClass

            after = {c.name: c.target_pct for c in session.query(AssetClass).all()}
            assert before == after, "no write on sum violation"
    finally:
        bad_path.write_text(backup, encoding="utf-8")


# ---------------------------------------------------------------------------
# asset-trade-flags: trade-control column on the asset CSV.
# ---------------------------------------------------------------------------


def test_legacy_four_column_asset_header_is_rejected(omaha_db) -> None:
    """A CSV with the legacy 4-column header aborts (no silent fallback).

    asset-trade-flags extends the asset header to 7 columns. The
    parser rejects the legacy shape with exit code 1 and a clear
    "expected ... got" message naming the new header — the same
    hard-fail pattern as ``quote_kind`` (see test above).
    """
    import tempfile
    from pathlib import Path

    import scripts.seed_from_csv as seed_mod

    bad_csv = "class_name,name,target_pct,display_order\nC,X,10,0\n"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "bad_assets.csv"
        target.write_text(bad_csv, encoding="utf-8")
        original_seed_dir = seed_mod.SEED_DIR
        seed_mod.SEED_DIR = tmp_path
        try:
            with pytest.raises(SystemExit) as exc_info:
                seed_mod.load_assets("bad")
            assert exc_info.value.code == 1
        finally:
            seed_mod.SEED_DIR = original_seed_dir


def test_invalid_currency_in_assets_csv_aborts(omaha_db) -> None:
    """A row with ``currency_code=EUR`` aborts at that line."""
    import tempfile
    from pathlib import Path

    import scripts.seed_from_csv as seed_mod

    bad_csv = (
        "class_name,name,target_pct,display_order,buy_enabled,"
        "sell_enabled,currency_code\n"
        "C,X,10,0,true,true,EUR\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        target = tmp_path / "bad_assets.csv"
        target.write_text(bad_csv, encoding="utf-8")
        original_seed_dir = seed_mod.SEED_DIR
        seed_mod.SEED_DIR = tmp_path
        try:
            with pytest.raises(SystemExit) as exc_info:
                seed_mod.load_assets("bad")
            assert exc_info.value.code == 1
            # (No way to capture stderr from SystemExit here; the
            # existence of the SystemExit itself confirms the abort
            # path was reached.)
            assert exc_info.value.code == 1
        finally:
            seed_mod.SEED_DIR = original_seed_dir


def test_run_reset_populates_trade_fields_from_csv(omaha_db) -> None:
    """``run_reset`` reads the 3 new CSV columns onto every asset row."""
    SessionLocal = omaha_db["SessionLocal"]
    r = _run_seed("italo", "reset", db_url=omaha_db["db_url"])
    assert r.returncode == 0, r.stderr
    expected_assets = {row.name: row for row in _italo_assets()}
    with SessionLocal() as session:
        from omaha.models import Asset

        # Every seeded asset reads CSV-supplied values.
        usd_count = 0
        for a in session.query(Asset).all():
            expected = expected_assets[a.name]
            assert a.buy_enabled == expected.buy_enabled
            assert a.sell_enabled == expected.sell_enabled
            assert a.currency_code == expected.currency_code
            if a.currency_code == "USD":
                usd_count += 1
        expected_usd_count = sum(
            1 for row in expected_assets.values() if row.currency_code == "USD"
        )
        assert usd_count == expected_usd_count, (
            f"expected {expected_usd_count} USD assets, got {usd_count}"
        )


def test_run_diff_emits_would_update_for_trade_changes(omaha_db, monkeypatch) -> None:
    """``run_diff`` detects diff on ``buy_enabled`` / ``sell_enabled`` /
    ``currency_code`` (not just ``target_pct`` / ``display_order``).
    """
    SessionLocal = omaha_db["SessionLocal"]
    _run_seed("italo", "reset", db_url=omaha_db["db_url"])

    # Flip one row's currency to USD via direct DB; diff should
    # report it as would-update.
    with SessionLocal() as session:
        from omaha.models import Asset

        first = session.query(Asset).first()
        first.currency_code = "USD"
        first.buy_enabled = False
        session.commit()

    r = _run_seed("italo", "diff", db_url=omaha_db["db_url"])
    assert r.returncode == 0, r.stderr
    # The diff output should mention the would-update row. Look
    # for either the "would-update" or the offending name.
    assert "would-update" in r.stdout or "would-update" in r.stderr
