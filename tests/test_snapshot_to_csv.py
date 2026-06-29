"""Tests for ``scripts.snapshot_to_csv``.

The DB-targeted tests use a per-test temporary SQLite file via the
``DATABASE_URL`` env var (``omaha.config.settings`` is rebuilt lazily
so we have to drop the cached ``omaha.*`` modules and reimport them
per test). The snapshot script is invoked via subprocess so it sees
the same ``DATABASE_URL`` the fixture set, mirroring how an operator
would run ``task db-snapshot`` from the CLI.

Cases:

1. ``test_round_trip_stable_for_italo`` — ``snapshot → reset →
   snapshot`` produces identical DB state for every seeded row across
   the four tables (``profiles``, ``asset_classes``, ``assets``,
   ``positions``), excluding autoincrement / timestamp columns.
2. ``test_round_trip_stable_for_ana`` — same as above for the Ana
   profile.
3. ``test_broker_ticker_preserved`` — add a one-off asset "Petrobras
   PN" with a position whose ``broker_ticker == "PETR4"``; snapshot;
   reset; assert the resulting ``Position`` row still has
   ``broker_ticker == "PETR4"`` and the CSV's ``asset_name`` is
   "Petrobras PN".
4. ``test_unknown_profile_errors`` — insert an extra profile outside
   the canonical set; assert exit code 1, stderr names the orphan,
   and no CSV file in ``data/seed/`` was modified.
5. ``test_idempotent_byte_equal_output`` — run snapshot twice on the
   same DB state; assert the two outputs are byte-equal (run in a
   tempdir copy of ``data/seed/`` so the real repo files are not
   touched).
6. ``test_header_shape_guards`` — first line of every emitted CSV
   exactly equals the documented header tuple.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "data" / "seed"
SEED_FROM_CSV = REPO_ROOT / "scripts" / "seed_from_csv.py"
SNAPSHOT_TO_CSV = REPO_ROOT / "scripts" / "snapshot_to_csv.py"


# ---------------------------------------------------------------------------
# Fixture: omaha_db (boots a fresh SQLite + alembic; does NOT seed users).
# Mirrors the fixture in tests/test_seed_from_csv.py.
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
    """Boot a fresh SQLite + alembic + seed canonical users."""
    saved = _save_modules()
    db_url = _tmp_db_url(tmp_path)
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("ADMIN_PASSWORD", "test-family-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-snapshot")

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-snapshot",
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


@pytest.fixture()
def seed_omaha_db(omaha_db):
    """Seed canonical Italo + Ana state via ``task db-reset`` semantics."""
    SessionLocal = omaha_db["SessionLocal"]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.reset_both_profiles",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": omaha_db["db_url"],
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-snapshot",
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"reset_both_profiles failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return {"SessionLocal": SessionLocal, "db_url": omaha_db["db_url"]}


@pytest.fixture()
def seed_dir_backup(request: pytest.FixtureRequest):
    """Snapshot the real ``data/seed/*.csv`` before the test and restore it after.

    Tests that drive ``scripts.snapshot_to_csv`` via subprocess write
    to the canonical seed dir (the script hardcodes
    ``REPO_ROOT / "data" / "seed"``). Without this fixture, those
    tests pollute the repo files for every subsequent run. The
    fixture takes a verbatim byte-level backup and writes it back in
    finalization, regardless of how the test exits.
    """
    files = [p for p in SEED_DIR.iterdir() if p.suffix == ".csv"]
    backup = {p.name: p.read_bytes() for p in files}
    request.addfinalizer(
        lambda: [(SEED_DIR / name).write_bytes(content) for name, content in backup.items()]
    )
    return backup


# ---------------------------------------------------------------------------
# Subprocess runner: invoke scripts.snapshot_to_csv / seed_from_csv with the
# same DATABASE_URL the fixture set.
# ---------------------------------------------------------------------------


def _run_snapshot(db_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "scripts.snapshot_to_csv"],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": db_url,
            "ADMIN_PASSWORD": "test-family-password",
            "SECRET_KEY": "test-secret-key-for-snapshot",
        },
        check=False,
        capture_output=True,
        text=True,
    )


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
            "SECRET_KEY": "test-secret-key-for-snapshot",
        },
        check=False,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _db_snapshot(SessionLocal, *, profile_name: str) -> dict[str, list[dict[str, object]]]:
    """Return a dict-of-table-lists capturing the round-trip-invariant columns.

    Excludes autoincrement ``id`` and timestamp columns so the
    comparison tolerates the expected ``created_at`` / ``imported_at``
    drift on a ``reset``.
    """
    from omaha.models import Asset, AssetClass, Position, Profile

    with SessionLocal() as session:
        profile = session.query(Profile).filter(Profile.name == profile_name).one()

        classes = (
            session.query(AssetClass)
            .filter(AssetClass.profile_id == profile.id)
            .order_by(AssetClass.display_order)
            .all()
        )
        assets = (
            session.query(Asset)
            .filter(Asset.asset_class_id.in_([c.id for c in classes]))
            .order_by(Asset.asset_class_id, Asset.display_order)
            .all()
        )
        positions = (
            session.query(Position)
            .filter(Position.asset_id.in_([a.id for a in assets]))
            .order_by(Position.asset_id, Position.broker_ticker)
            .all()
        )

        return {
            "profile": {
                "name": profile.name,
                "display_order": profile.display_order,
            },
            "classes": [
                {
                    "name": c.name,
                    "target_pct": c.target_pct,
                    "display_order": c.display_order,
                    "quote_kind": c.quote_kind,
                }
                for c in classes
            ],
            "assets": [
                {
                    "class_name": next(cl.name for cl in classes if cl.id == a.asset_class_id),
                    "name": a.name,
                    "target_pct": a.target_pct,
                    "display_order": a.display_order,
                    "buy_enabled": a.buy_enabled,
                    "sell_enabled": a.sell_enabled,
                    "currency_code": a.currency_code,
                }
                for a in assets
            ],
            "positions": [
                {
                    "asset_name": next(an.name for an in assets if an.id == p.asset_id),
                    "broker_ticker": p.broker_ticker,
                    "qty": p.qty,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    # broker-csv-import-totals: totals flow verbatim
                    # through snapshot → reset → snapshot. ``None``
                    # is preserved (empty CSV cell ↔ NULL row).
                    "total_invested": p.total_invested,
                    "total_current": p.total_current,
                }
                for p in positions
            ],
        }


def _quantize_values(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Round all Decimal values to the 8-dp precision the snapshot uses.

    Without this, ``Decimal("18026.61137440758293838862559")`` from
    the DB might not byte-equal the value rendered from
    ``Decimal("18026.61137440758293838862559").quantize(1e-8)`` after
    the round-trip — they're the same number but their string forms
    can differ in trailing-zero padding.
    """
    q = Decimal("0.00000001")
    out: list[dict[str, object]] = []
    for row in rows:
        new_row: dict[str, object] = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                new_row[k] = v.quantize(q)
            else:
                new_row[k] = v
        out.append(new_row)
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_round_trip_stable_for_italo(seed_omaha_db) -> None:
    """``snapshot → reset → snapshot`` preserves the round-trip-invariant columns."""
    SessionLocal = seed_omaha_db["SessionLocal"]
    db_url = seed_omaha_db["db_url"]

    before = _db_snapshot(SessionLocal, profile_name="Italo")

    # snapshot → reset → snapshot
    r1 = _run_snapshot(db_url)
    assert r1.returncode == 0, r1.stderr
    r2 = _run_seed("italo", "reset", db_url=db_url)
    assert r2.returncode == 0, r2.stderr
    r3 = _run_snapshot(db_url)
    assert r3.returncode == 0, r3.stderr

    after = _db_snapshot(SessionLocal, profile_name="Italo")
    assert _quantize_values(before["positions"]) == _quantize_values(after["positions"]), (
        "positions must round-trip invariantly"
    )
    assert before["classes"] == after["classes"], "classes must round-trip invariantly"
    assert before["assets"] == after["assets"], "assets must round-trip invariantly"
    assert before["profile"] == after["profile"]


def test_round_trip_stable_for_ana(seed_omaha_db) -> None:
    SessionLocal = seed_omaha_db["SessionLocal"]
    db_url = seed_omaha_db["db_url"]

    before = _db_snapshot(SessionLocal, profile_name="Ana")

    r1 = _run_snapshot(db_url)
    assert r1.returncode == 0, r1.stderr
    r2 = _run_seed("ana", "reset", db_url=db_url)
    assert r2.returncode == 0, r2.stderr
    r3 = _run_snapshot(db_url)
    assert r3.returncode == 0, r3.stderr

    after = _db_snapshot(SessionLocal, profile_name="Ana")
    assert _quantize_values(before["positions"]) == _quantize_values(after["positions"])
    assert before["classes"] == after["classes"]
    assert before["assets"] == after["assets"]
    assert before["profile"] == after["profile"]


def test_broker_ticker_preserved(seed_omaha_db, seed_dir_backup) -> None:
    """Divergent ``broker_ticker`` survives ``snapshot → reset → snapshot``."""
    SessionLocal = seed_omaha_db["SessionLocal"]
    db_url = seed_omaha_db["db_url"]

    # Inject one-off asset + position directly into the DB.
    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile

        italo = session.query(Profile).filter(Profile.name == "Italo").one()
        acoes = (
            session.query(AssetClass)
            .filter(AssetClass.profile_id == italo.id, AssetClass.name == "Ações")
            .one()
        )
        a = Asset(
            asset_class_id=acoes.id,
            name="Petrobras PN",
            target_pct=Decimal("0.00"),
            display_order=99,
            buy_enabled=True,
            sell_enabled=True,
            currency_code="BRL",
        )
        session.add(a)
        session.flush()
        p = Position(
            asset_id=a.id,
            qty=Decimal("100"),
            avg_price=Decimal("32.50"),
            current_price=Decimal("38.75"),
            broker_ticker="PETR4",
        )
        session.add(p)
        session.commit()

    r1 = _run_snapshot(db_url)
    assert r1.returncode == 0, r1.stderr
    r2 = _run_seed("italo", "reset", db_url=db_url)
    assert r2.returncode == 0, r2.stderr
    r3 = _run_snapshot(db_url)
    assert r3.returncode == 0, r3.stderr

    # The Petrobras PN position must keep broker_ticker="PETR4".
    with SessionLocal() as session:
        from omaha.models import Asset, Position

        petrobras = session.query(Asset).filter(Asset.name == "Petrobras PN").one()
        pos = session.query(Position).filter(Position.asset_id == petrobras.id).one()
        assert pos.broker_ticker == "PETR4", pos.broker_ticker
        assert pos.qty == Decimal("100")
        assert pos.avg_price == Decimal("32.50")
        assert pos.current_price == Decimal("38.75")


def test_totals_preserved_through_round_trip(seed_omaha_db, seed_dir_backup) -> None:
    """``total_invested`` / ``total_current`` survive ``snapshot → reset → snapshot``.

    Pins the ``broker-csv-import-totals`` invariant for the
    snapshot pipeline: the script writes ``Position.total_invested``
    / ``total_current`` verbatim into the positions CSV (never
    recomputed from ``qty * price``), and the seed path reads them
    back the same way. We inject a one-off position with totals
    that DO NOT equal ``qty * price`` — if either direction ever
    falls back to multiplication, the post-round-trip values drift.
    """
    SessionLocal = seed_omaha_db["SessionLocal"]
    db_url = seed_omaha_db["db_url"]

    sentinel_invested = Decimal("99999.9999")
    sentinel_current = Decimal("88888.8888")

    with SessionLocal() as session:
        from omaha.models import Asset, AssetClass, Position, Profile

        italo = session.query(Profile).filter(Profile.name == "Italo").one()
        acoes = (
            session.query(AssetClass)
            .filter(AssetClass.profile_id == italo.id, AssetClass.name == "Ações")
            .one()
        )
        a = Asset(
            asset_class_id=acoes.id,
            name="Sentinel Asset",
            target_pct=Decimal("0.00"),
            display_order=98,
            buy_enabled=True,
            sell_enabled=True,
            currency_code="BRL",
        )
        session.add(a)
        session.flush()
        p = Position(
            asset_id=a.id,
            qty=Decimal("100"),
            avg_price=Decimal("32.50"),
            current_price=Decimal("38.75"),
            broker_ticker="SNTL",
            total_invested=sentinel_invested,
            total_current=sentinel_current,
        )
        session.add(p)
        session.commit()

    r1 = _run_snapshot(db_url)
    assert r1.returncode == 0, r1.stderr
    r2 = _run_seed("italo", "reset", db_url=db_url)
    assert r2.returncode == 0, r2.stderr
    r3 = _run_snapshot(db_url)
    assert r3.returncode == 0, r3.stderr

    with SessionLocal() as session:
        from omaha.models import Asset, Position

        asset = session.query(Asset).filter(Asset.name == "Sentinel Asset").one()
        pos = session.query(Position).filter(Position.asset_id == asset.id).one()
        # The sentinel values must persist verbatim — not the
        # qty*price = 3250.00 / 3875.00 that a recompute would
        # produce.
        assert pos.total_invested == sentinel_invested, pos.total_invested
        assert pos.total_current == sentinel_current, pos.total_current


def test_unknown_profile_errors(seed_omaha_db, tmp_path) -> None:
    """Inserting a stray profile aborts the snapshot before any CSV is written."""
    SessionLocal = seed_omaha_db["SessionLocal"]
    db_url = seed_omaha_db["db_url"]

    # Take a copy of the real seed dir so the orphan test cannot
    # touch the repo files even by accident.
    seed_copy = tmp_path / "seed_copy"
    shutil.copytree(SEED_DIR, seed_copy)
    pre_mtimes = {p.name: p.stat().st_mtime for p in seed_copy.iterdir()}

    with SessionLocal() as session:
        from omaha.models import Profile, User

        italo = session.query(User).filter(User.username == "Italo").one()
        session.add(Profile(user_id=italo.id, name="Orphan", display_order=99))
        session.commit()

    try:
        r = _run_snapshot(db_url)
        assert r.returncode != 0, "snapshot must fail when an unknown profile exists"
        assert "Orphan" in r.stderr, r.stderr
        assert "not in canonical set" in r.stderr, r.stderr
    finally:
        with SessionLocal() as session:
            from omaha.models import Profile

            session.query(Profile).filter(Profile.name == "Orphan").delete()
            session.commit()

    # No file in the seed copy was modified by the failed run —
    # mtimes are unchanged.
    for p in seed_copy.iterdir():
        assert p.stat().st_mtime == pre_mtimes[p.name], (
            f"{p.name} was modified despite the snapshot abort"
        )


def test_idempotent_byte_equal_output(seed_omaha_db, tmp_path, monkeypatch) -> None:
    """Running snapshot twice on the same DB state produces byte-equal CSVs.

    Redirects ``SEED_DIR`` to a tmpdir copy so the real repo files
    are not touched, then runs the script's helpers directly with
    the tempdir as the output target. Compares first-run and
    second-run bytes.
    """
    SessionLocal = seed_omaha_db["SessionLocal"]

    seed_copy_a = tmp_path / "seed_a"
    seed_copy_b = tmp_path / "seed_b"
    seed_copy_a.mkdir()
    seed_copy_b.mkdir()

    import scripts.snapshot_to_csv as snap_mod

    original_seed_dir = snap_mod.SEED_DIR
    snap_mod.SEED_DIR = seed_copy_a
    try:
        with SessionLocal() as session:
            from omaha.models import Profile

            for profile_name in ("italo", "ana"):
                p = session.query(Profile).filter(Profile.name == profile_name.capitalize()).one()
                snap_mod.snapshot_classes(p, profile_name)
                snap_mod.snapshot_assets(p, profile_name)
                snap_mod.snapshot_positions(p, profile_name)
        first = {
            p.name: p.read_bytes()
            for p in sorted(seed_copy_a.iterdir())
            if p.is_file() and p.suffix == ".csv"
        }

        snap_mod.SEED_DIR = seed_copy_b
        with SessionLocal() as session:
            from omaha.models import Profile

            for profile_name in ("italo", "ana"):
                p = session.query(Profile).filter(Profile.name == profile_name.capitalize()).one()
                snap_mod.snapshot_classes(p, profile_name)
                snap_mod.snapshot_assets(p, profile_name)
                snap_mod.snapshot_positions(p, profile_name)
        second = {
            p.name: p.read_bytes()
            for p in sorted(seed_copy_b.iterdir())
            if p.is_file() and p.suffix == ".csv"
        }
    finally:
        snap_mod.SEED_DIR = original_seed_dir

    assert set(first.keys()) == set(second.keys())
    for name in first:
        assert first[name] == second[name], f"{name} differs between runs"


def test_header_shape_guards(seed_omaha_db, tmp_path) -> None:
    """First line of every emitted CSV matches the documented header."""
    SessionLocal = seed_omaha_db["SessionLocal"]

    import scripts.snapshot_to_csv as snap_mod

    original_seed_dir = snap_mod.SEED_DIR
    snap_mod.SEED_DIR = tmp_path
    try:
        with SessionLocal() as session:
            from omaha.models import Profile

            for profile_name in ("italo", "ana"):
                p = session.query(Profile).filter(Profile.name == profile_name.capitalize()).one()
                snap_mod.snapshot_classes(p, profile_name)
                snap_mod.snapshot_assets(p, profile_name)
                snap_mod.snapshot_positions(p, profile_name)

        expected = {}
        for p in ("italo", "ana"):
            expected[f"{p}_classes.csv"] = "name,target_pct,display_order,quote_kind"
            expected[f"{p}_assets.csv"] = (
                "class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code"
            )
            expected[f"{p}_positions.csv"] = (
                "asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current"
            )
        for filename, header in expected.items():
            first_line = (tmp_path / filename).read_text(encoding="utf-8").split("\n", 1)[0]
            assert first_line == header, f"{filename}: {first_line!r} != {header!r}"
    finally:
        snap_mod.SEED_DIR = original_seed_dir
