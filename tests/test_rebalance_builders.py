"""Integration tests for :mod:`omaha.rebalance.builders`.

Covers the spec scenarios for ``build_setup_from_db`` (the
:class:`~omaha.rebalance.models.PortfolioSetup` builder + warnings),
``build_position_frame`` (per-asset aggregation), and the empty-class
warning rule.

The DB is the session-scoped SQLite from ``tests/conftest.py``. Each
test wipes ``asset_classes`` / ``assets`` / ``positions`` (CASCADE
order) so leftover state from S03/S04 tests doesn't leak in. The
Italo profile (seeded once per session by ``_omaha_test_env``) is
the fixture anchor.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from omaha.db import SessionLocal
from omaha.models import Asset, AssetClass, Position, Profile, QuoteKind
from omaha.rebalance.builders import build_position_frame, build_setup_from_db


# ---------------------------------------------------------------------------
# Fixture: wipe the dashboard tables before each test, expose the
# Italo profile as the fixture anchor.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_tables() -> None:
    """Wipe classes / assets / positions before each test in this module."""
    db = SessionLocal()
    try:
        db.query(Position).delete()
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def italo_profile() -> Profile:
    """Return the seeded Italo profile (created by ``_omaha_test_env``)."""
    with SessionLocal() as db:
        profile = db.query(Profile).filter(Profile.name == "Italo").one()
        # Detach so callers can use it freely without a session.
        db.expunge(profile)
        return profile


def _seed_class(
    profile_id: int,
    name: str,
    target_pct: str,
    assets: list[tuple[str, str]],
    quote_kind: str = QuoteKind.NONE.value,
) -> int:
    """Create a class + its assets, return the class id.

    ``assets`` is a list of ``(name, target_pct_str)`` tuples;
    ``display_order`` follows the list index. No positions are
    created — tests that need positions call :func:`_seed_positions`.
    """
    with SessionLocal() as db:
        klass = AssetClass(
            profile_id=profile_id,
            name=name,
            target_pct=Decimal(target_pct),
            display_order=0,
            quote_kind=quote_kind,
        )
        db.add(klass)
        db.flush()
        for index, (asset_name, asset_pct) in enumerate(assets):
            db.add(
                Asset(
                    asset_class_id=klass.id,
                    name=asset_name,
                    target_pct=Decimal(asset_pct),
                    display_order=index,
                )
            )
        db.commit()
        return klass.id


def _seed_positions(asset_id: int, rows: list[tuple[str, str, str, str, str | None, str | None]]) -> None:
    """Create positions for ``asset_id``.

    Each row is ``(broker_ticker, qty, avg_price, current_price,
    total_invested, total_current)``. ``total_invested`` /
    ``total_current`` default to ``qty * avg_price`` / ``qty *
    current_price`` when ``None`` — but tests in this module always
    pass explicit values to mirror the broker-published-totals rule.
    """
    with SessionLocal() as db:
        for ticker, qty, avg, cur, total_invested, total_current in rows:
            db.add(
                Position(
                    asset_id=asset_id,
                    qty=Decimal(qty),
                    avg_price=Decimal(avg),
                    current_price=Decimal(cur),
                    broker_ticker=ticker,
                    total_invested=Decimal(total_invested) if total_invested is not None else None,
                    total_current=Decimal(total_current) if total_current is not None else None,
                )
            )
        db.commit()


def _asset_id(klass_id: int, name: str) -> int:
    """Return the asset id for ``(klass_id, name)``."""
    with SessionLocal() as db:
        asset = (
            db.query(Asset)
            .filter(Asset.asset_class_id == klass_id, Asset.name == name)
            .one()
        )
        return asset.id


# ---------------------------------------------------------------------------
# PortfolioSetup builder tests
# ---------------------------------------------------------------------------


def test_setup_happy_path_three_classes_five_assets(italo_profile: Profile) -> None:
    """Three classes (60/30/10) × five assets → target sums to 1.0."""
    _seed_class(italo_profile.id, "RF", "60", [("Selic", "100")], quote_kind=QuoteKind.AUTO.value)
    _seed_class(
        italo_profile.id, "RV", "30",
        [("PETR4", "50"), ("VALE3", "50")],
        quote_kind=QuoteKind.AUTO.value,
    )
    _seed_class(
        italo_profile.id, "FII", "10",
        [("HGLG11", "60"), ("MXRF11", "40")],
        quote_kind=QuoteKind.AUTO.value,
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        setup, warnings = build_setup_from_db(db, profile)

    assert warnings == []
    assert len(setup.categories) == 3
    assert len(setup.assets) == 5

    assert setup.categories["target_weight"].sum() == pytest.approx(1.0, abs=1e-6)
    assert setup.assets["target_weight"].sum() == pytest.approx(1.0, abs=1e-6)

    # Per-class weight sum equals the class's target_pct/100.
    for klass_name in ("RF", "RV", "FII"):
        class_subset = setup.assets[setup.assets["category_name"] == klass_name]
        assert class_subset["target_weight_in_category"].sum() == pytest.approx(1.0, abs=1e-6)


def test_setup_empty_profile_returns_empty_dataframes_with_schema(italo_profile: Profile) -> None:
    """No classes → empty frames with the full column schema (no KeyError)."""
    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        setup, warnings = build_setup_from_db(db, profile)

    assert warnings == []
    assert isinstance(setup.categories, pd.DataFrame)
    assert isinstance(setup.assets, pd.DataFrame)
    assert list(setup.categories.columns) == [
        "category_name",
        "category_key",
        "target_weight",
        "category_order",
    ]
    assert list(setup.assets.columns) == [
        "asset_name",
        "asset_key",
        "category_name",
        "category_key",
        "currency_code",
        "buy_enabled",
        "sell_enabled",
        "target_weight_in_category",
        "target_weight",
        "asset_order",
        "quote_kind",
    ]
    assert setup.categories.empty
    assert setup.assets.empty


def test_setup_cross_class_name_collision_groups_and_warns(italo_profile: Profile) -> None:
    """Two classes with the same asset name → groupby keeps one row + warning."""
    _seed_class(
        italo_profile.id, "RF", "60",
        [("Tesouro", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    _seed_class(
        italo_profile.id, "RV", "30",
        [("Tesouro", "100")],  # same asset name, different class
        quote_kind=QuoteKind.AUTO.value,
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        setup, warnings = build_setup_from_db(db, profile)

    # Two AssetClass rows + two Asset rows collapse to ONE unique
    # ``asset_key`` after groupby → the solver sees one asset (the
    # first by class order). The warning text names both classes so
    # the operator can resolve the shadowed row in the dashboard.
    assert len(setup.assets) == 1
    assert setup.assets.iloc[0]["asset_key"] == "tesouro"
    assert len(warnings) == 1
    assert "tesouro" in warnings[0]
    # Both classes are named in the warning so the operator can resolve.
    assert "rf" in warnings[0]
    assert "rv" in warnings[0]


def test_setup_category_order_is_zero_indexed_and_contiguous(italo_profile: Profile) -> None:
    """``category_order`` is 0..N-1 regardless of ``display_order`` gaps."""
    with SessionLocal() as db:
        # Bypass _seed_class to set explicit display_order with gaps.
        for index, name, target in [
            (0, "RF", "60"),
            (5, "RV", "30"),  # gap of 4
            (12, "FII", "10"),  # another gap
        ]:
            db.add(
                AssetClass(
                    profile_id=italo_profile.id,
                    name=name,
                    target_pct=Decimal(target),
                    display_order=index,
                    quote_kind=QuoteKind.AUTO.value,
                )
            )
        db.commit()
        profile = db.merge(italo_profile)
        setup, _ = build_setup_from_db(db, profile)

    assert list(setup.categories["category_order"]) == [0, 1, 2]


def test_setup_asset_order_is_zero_indexed_per_class(italo_profile: Profile) -> None:
    """``asset_order`` re-numbers 0..N-1 per class (display_order gaps ignored)."""
    with SessionLocal() as db:
        klass = AssetClass(
            profile_id=italo_profile.id,
            name="RF",
            target_pct=Decimal("100"),
            display_order=0,
            quote_kind=QuoteKind.AUTO.value,
        )
        db.add(klass)
        db.flush()
        for asset_index, (asset_name, display_order) in enumerate(
            [("Selic", 7), ("IPCA", 3), ("CDB", 99)]  # gaps inside the class
        ):
            db.add(
                Asset(
                    asset_class_id=klass.id,
                    name=asset_name,
                    target_pct=Decimal("100"),
                    display_order=display_order,
                )
            )
        db.commit()
        profile = db.merge(italo_profile)
        setup, _ = build_setup_from_db(db, profile)

    # The builder sorts by (display_order, id), so the canonical
    # 0..N-1 numbering follows that order.
    assert list(setup.assets["asset_order"]) == [0, 1, 2]


def test_setup_warning_for_empty_class_with_target(italo_profile: Profile) -> None:
    """Empty class with ``target_pct > 0`` emits one warning per class."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")])
    _seed_class(italo_profile.id, "Crypto", "20", [])  # empty, non-zero target

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        _setup, warnings = build_setup_from_db(db, profile)

    assert len(warnings) == 1
    assert "Crypto" in warnings[0]
    assert "20.00" in warnings[0]
    assert "caixa residual" in warnings[0]


def test_setup_no_warning_for_empty_class_with_zero_target(italo_profile: Profile) -> None:
    """Empty class with ``target_pct == 0`` does NOT warn."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")])
    _seed_class(italo_profile.id, "Empty", "0", [])  # empty, zero target

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        _setup, warnings = build_setup_from_db(db, profile)

    assert warnings == []


# ---------------------------------------------------------------------------
# Position builder tests
# ---------------------------------------------------------------------------


def test_position_three_positions_aggregate_totals(italo_profile: Profile) -> None:
    """Three positions on one asset → sums ``qty``, ``total_invested``, ``total_current``."""
    klass_id = _seed_class(
        italo_profile.id, "RV", "100",
        [("PETR4", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    asset_id = _asset_id(klass_id, "PETR4")
    # Three positions on one asset — each carries a distinct broker
    # ticker (the (asset_id, broker_ticker) unique constraint makes
    # duplicate tickers per asset an UPSERT, not three rows).
    _seed_positions(
        asset_id,
        [
            ("PETR4-A", "10", "30", "33", "100", "110"),
            ("PETR4-B", "20", "30", "33", "200", "220"),
            ("PETR4-C", "30", "30", "33", "300", "330"),
        ],
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    row = df.iloc[0]
    assert row["quantity"] == pytest.approx(60.0)
    assert row["invested_value"] == pytest.approx(600.0)
    assert row["current_value"] == pytest.approx(660.0)


def test_position_asset_with_zero_positions_yields_zero_totals(italo_profile: Profile) -> None:
    """Asset with no positions → row has qty=0, invested=0, current=0, weight=0."""
    _seed_class(
        italo_profile.id, "RV", "100",
        [("PETR4", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["quantity"] == 0.0
    assert row["invested_value"] == 0.0
    assert row["current_value"] == 0.0
    assert row["current_weight"] == 0.0


def test_position_empty_portfolio_yields_zero_weight_per_asset(italo_profile: Profile) -> None:
    """total_current == 0 → every row's current_weight is 0.0 (not NaN)."""
    klass_id = _seed_class(
        italo_profile.id, "RV", "100",
        [("PETR4", "100"), ("VALE3", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    asset_id = _asset_id(klass_id, "PETR4")
    # Zero current_value (positions exist but contribute 0).
    _seed_positions(
        asset_id,
        [("PETR4", "10", "30", "0", "300", "0")],
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    assert len(df) == 2
    assert (df["current_weight"] == 0.0).all()
    assert not df["current_weight"].isna().any()


def test_position_null_totals_treated_as_zero(italo_profile: Profile) -> None:
    """``total_invested`` / ``total_current`` NULL → contributes 0 to the sum."""
    klass_id = _seed_class(
        italo_profile.id, "RV", "100",
        [("PETR4", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    asset_id = _asset_id(klass_id, "PETR4")
    # First position carries the broker totals; second position has
    # ``NULL`` totals — the legacy shape the dashboard treats as zero
    # contribution.
    _seed_positions(
        asset_id,
        [
            ("PETR4", "10", "30", "33", "300", "330"),
            ("PETR4-LEGACY", "5", "25", "0", None, None),
        ],
    )

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    row = df.iloc[0]
    assert row["quantity"] == pytest.approx(15.0)
    assert row["invested_value"] == pytest.approx(300.0)
    assert row["current_value"] == pytest.approx(330.0)


def test_position_current_weight_normalized_to_total(italo_profile: Profile) -> None:
    """``current_weight`` is each asset's share of the portfolio's total ``current_value``."""
    rf_id = _seed_class(
        italo_profile.id, "RF", "60",
        [("Selic", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    rv_id = _seed_class(
        italo_profile.id, "RV", "40",
        [("PETR4", "100")],
        quote_kind=QuoteKind.AUTO.value,
    )
    _seed_positions(_asset_id(rf_id, "Selic"), [("SELIC", "10", "100", "120", "1000", "1200")])
    _seed_positions(_asset_id(rv_id, "PETR4"), [("PETR4", "20", "30", "40", "600", "800")])

    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    # Total current_value = 2000; Selic 1200 → 0.6; PETR4 800 → 0.4.
    weights = dict(zip(df["asset_name"], df["current_weight"]))
    assert weights["Selic"] == pytest.approx(0.6)
    assert weights["PETR4"] == pytest.approx(0.4)


def test_position_empty_profile_returns_full_schema(italo_profile: Profile) -> None:
    """Profile with no classes → empty frame with the 8 expected columns."""
    with SessionLocal() as db:
        profile = db.merge(italo_profile)
        df = build_position_frame(db, profile)

    assert df.empty
    assert list(df.columns) == [
        "asset_key",
        "asset_name",
        "category_name",
        "category_key",
        "quantity",
        "invested_value",
        "current_value",
        "current_weight",
    ]
