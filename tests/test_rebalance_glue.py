"""Integration tests for :mod:`omaha.rebalance.glue`.

Covers the spec requirements §"Glue orchestrates profile loading,
builders, adapter, and solver", §"Solver stub returns a frozen
fixture", §"Solver is injected as a callable", §"Empty profile
returns empty plan with explanatory warning", and §"Glue
translates solver-native shape to wire format".

The DB is the session-scoped SQLite from ``tests/conftest.py``.
Each test wipes ``asset_classes`` / ``assets`` so leftover state
from sibling tests doesn't leak in.

Session-locality gotcha
-----------------------
``omaha.db.SessionLocal`` is bound at import time to the dev DB
engine. ``_omaha_test_env`` deletes ``omaha.*`` and re-imports
with the test ``DATABASE_URL`` — but this module's local
``SessionLocal`` name (imported at the top of the file) is already
bound to the OLD engine. The helpers below therefore build a
fresh engine from ``_omaha_test_env["db_url"]`` so the test sees
its own data. Mirrors the pattern in ``test_assets_trade_flags.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from omaha.models import Asset, AssetClass, Profile, QuoteKind
from omaha.rebalance.glue import run_rebalance
from omaha.rebalance.schemas import (
    RebalancePlanResponse,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _wipe_tables(_omaha_test_env: dict[str, str]) -> None:
    """Wipe classes / assets / positions before each test (fresh engine)."""
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        db.query(Asset).delete()
        db.query(AssetClass).delete()
        db.commit()
    finally:
        db.close()
        engine.dispose()
    yield


@pytest.fixture
def italo_profile(_omaha_test_env: dict[str, str]) -> Profile:
    """Return the seeded Italo profile (fresh engine)."""
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.name == "Italo").one()
        db.expunge(profile)
        return profile
    finally:
        db.close()
        engine.dispose()


@contextmanager
def _session(_omaha_test_env: dict[str, str]) -> Iterator[Session]:
    """Yield a fresh Session bound to the test DB."""
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _seed_class(
    profile_id: int,
    name: str,
    target_pct: str,
    assets: list[tuple[str, str]],
    _omaha_test_env: dict[str, str],
    quote_kind: str = QuoteKind.NONE.value,
) -> int:
    """Create a class + its assets, return the class id."""
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
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
    finally:
        db.close()
        engine.dispose()


def _refresh_profile(profile: Profile, _omaha_test_env: dict[str, str]) -> Profile:
    """Reload the profile from the test DB so eager-loading is fresh."""
    engine = create_engine(_omaha_test_env["db_url"], future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        fresh = db.query(Profile).filter(Profile.id == profile.id).one()
        db.expunge(fresh)
        return fresh
    finally:
        db.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# §"Glue orchestrates profile loading, builders, adapter, and solver"
# ---------------------------------------------------------------------------


def test_glue_returns_populated_plan_for_active_profile(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """A populated profile returns a plan with all five top-level fields.

    The stub fixture is fixture-driven (ignores the input setup), so
    the response's asset_plan length matches the fixture (5 assets)
    rather than the seeded 2. We assert fixture-shaped values here
    by explicitly opting into the stub (Phase 4's CVXPY default
    would honour the seeded shape instead). The per-asset mapping
    is exercised by ``test_glue_drops_solver_columns_not_in_v1_subset``
    below.
    """
    _seed_class(italo_profile.id, "RF", "60", [("Selic", "100")], _omaha_test_env)
    _seed_class(italo_profile.id, "RV", "40", [("PETR4", "100")], _omaha_test_env)

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    from omaha.rebalance.solver_stub import stub_solver

    with _session(_omaha_test_env) as db:
        response = run_rebalance(db, profile, contribution=5000.0, solver=stub_solver)

    assert isinstance(response, RebalancePlanResponse)
    assert len(response.asset_plan) == 5  # fixture has 5 assets
    assert len(response.category_plan) == 2  # fixture has 2 categories
    assert response.metrics.contribution == 5000.0
    assert response.applied_policy != ""


def test_glue_passes_contribution_to_solver(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """The contribution arg flows through to the solver (stub overlays it)."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")], _omaha_test_env)

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    from omaha.rebalance.solver_stub import stub_solver

    with _session(_omaha_test_env) as db:
        response = run_rebalance(db, profile, contribution=7777.0, solver=stub_solver)

    assert response.metrics.contribution == 7777.0


def test_glue_translates_bridge_warnings(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """Bridge warnings appear in the response with the documented codes."""
    _seed_class(italo_profile.id, "RF", "80", [("Selic", "100")], _omaha_test_env)
    _seed_class(italo_profile.id, "Crypto", "20", [], _omaha_test_env)  # empty class

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    # Bridge warnings are emitted by the builders (not the solver).
    # The stub solver preserves them faithfully; CVXPY's warnings
    # differ in shape, so use the stub for this assertion.
    from omaha.rebalance.solver_stub import stub_solver

    with _session(_omaha_test_env) as db:
        response = run_rebalance(db, profile, contribution=1000.0, solver=stub_solver)

    codes = {w.code for w in response.warnings}
    assert "EMPTY_CLASS_NONZERO_TARGET" in codes


# ---------------------------------------------------------------------------
# §"Solver is injected as a callable"
# ---------------------------------------------------------------------------


def test_custom_solver_replaces_default(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """Injecting a sentinel solver returns the sentinel's output."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")], _omaha_test_env)

    from omaha.rebalance.solver_stub import (
        RebalanceCategoryPlanRowNative,
        RebalancePlan,
        RebalancePlanMetricsNative,
        RebalanceWarningNative,
    )

    sentinel = RebalancePlan(
        contribution=9999.0,
        asset_classes=[],
        asset_plan=[],
        category_plan=[
            RebalanceCategoryPlanRowNative(
                category_name="RF",
                current_value=0.0,
                projected_value=0.0,
            ),
        ],
        metrics=RebalancePlanMetricsNative(
            contribution=9999.0,
            total_buy=0.0,
            total_sell=0.0,
            residual_cash=0.0,
            current_deviation_pct=0.0,
            projected_deviation_pct=0.0,
        ),
        warnings=[
            RebalanceWarningNative(code="CUSTOM", message="custom sentinel"),
        ],
        applied_policy="sentinel",
    )

    def custom_solver(setup, positions, quotes, contribution):
        return sentinel

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    with _session(_omaha_test_env) as db:
        response = run_rebalance(
            db,
            profile,
            contribution=100.0,
            solver=custom_solver,
        )

    assert response.metrics.contribution == 9999.0
    assert response.applied_policy == "sentinel"
    assert any(w.code == "CUSTOM" for w in response.warnings)


@pytest.mark.skip(
    reason=(
        "Covered by tests/test_rebalance_engine_glue.py::"
        "test_cvxpy_solver_directly_returns_native_shape which "
        "tests the same behavior with isolated fixture state."
    )
)
def test_default_solver_is_cvxpy(italo_profile: Profile, _omaha_test_env: dict[str, str]) -> None:
    """Decision 7 — default solver is cvxpy_solver (the real engine)."""
    raise NotImplementedError("covered by test_rebalance_engine_glue.py")


def _seed_positions(_omaha_test_env: dict[str, str], by_asset: dict[str, float]) -> None:
    """Seed one Position per asset name. Required by Phase 4's CVXPY validator."""
    import os

    from omaha.db import SessionLocal
    from omaha.models import Position

    os.environ["DATABASE_URL"] = _omaha_test_env["db_url"]
    with SessionLocal() as db:
        for asset_name, current_value in by_asset.items():
            asset = db.query(Asset).filter(Asset.name == asset_name).one()
            pos = Position(
                asset_id=asset.id,
                broker_ticker=asset_name,
                qty=Decimal("1"),
                avg_price=Decimal(str(current_value)),
                current_price=Decimal(str(current_value)),
                total_invested=Decimal(str(current_value)),
                total_current=Decimal(str(current_value)),
            )
            db.add(pos)
        db.commit()


# ---------------------------------------------------------------------------
# §"Empty profile returns empty plan with explanatory warning"
# ---------------------------------------------------------------------------


def test_empty_profile_returns_empty_plan_with_warning(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """A profile with zero classes returns 200 + EMPTY_PROFILE warning."""
    profile = _refresh_profile(italo_profile, _omaha_test_env)
    with _session(_omaha_test_env) as db:
        response = run_rebalance(db, profile, contribution=1000.0)

    assert response.asset_plan == []
    assert response.category_plan == []
    assert response.metrics.total_buy == 0.0
    assert response.metrics.total_sell == 0.0
    assert len(response.warnings) == 1
    assert response.warnings[0].code == "EMPTY_PROFILE"


# ---------------------------------------------------------------------------
# §"Glue translates solver-native shape to wire format"
# ---------------------------------------------------------------------------


def test_glue_drops_solver_columns_not_in_v1_subset(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """The glue maps only documented wire fields per asset row."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")], _omaha_test_env)

    from omaha.rebalance.solver_stub import stub_solver

    captured: dict = {}

    def capturing_solver(setup, positions, quotes, contribution):
        captured["called"] = True
        return stub_solver(setup, positions, quotes, contribution)

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    with _session(_omaha_test_env) as db:
        response = run_rebalance(
            db,
            profile,
            contribution=1000.0,
            solver=capturing_solver,
        )

    assert captured.get("called") is True
    assert len(response.asset_plan) >= 1
    first_row = response.asset_plan[0]
    assert set(first_row.model_dump().keys()) == {
        "asset_key",
        "asset_name",
        "category_name",
        "current_value",
        "target_value",
        "buy_amount",
        "sell_amount",
        "trade_quantity",
        "projected_value",
        "action",
        "deviation_value",
        "deviation_pct",
    }


def test_action_derived_from_buy_and_sell_amounts(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """Action is derived from buy/sell amounts using DISPLAY_TOLERANCE."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")], _omaha_test_env)

    from omaha.rebalance.solver_stub import (
        RebalanceAssetPlanRowNative,
        RebalanceCategoryPlanRowNative,
        RebalancePlan,
        RebalancePlanMetricsNative,
    )

    native_plan = RebalancePlan(
        contribution=1000.0,
        asset_classes=[],
        asset_plan=[
            RebalanceAssetPlanRowNative(
                name="Buy",
                category_name="RF",
                currency_code="BRL",
                buy_enabled=True,
                current_value=100.0,
                target_value=200.0,
                buy_amount=100.0,
                sell_amount=0.0,
                projected_value=200.0,
            ),
            RebalanceAssetPlanRowNative(
                name="Sell",
                category_name="RF",
                currency_code="BRL",
                buy_enabled=True,
                current_value=200.0,
                target_value=100.0,
                buy_amount=0.0,
                sell_amount=100.0,
                projected_value=100.0,
            ),
            RebalanceAssetPlanRowNative(
                name="Hold",
                category_name="RF",
                currency_code="BRL",
                buy_enabled=True,
                current_value=100.0,
                target_value=100.0,
                buy_amount=0.00001,  # below DISPLAY_TOLERANCE = 1e-4
                sell_amount=0.0,
                projected_value=100.0,
            ),
        ],
        category_plan=[
            RebalanceCategoryPlanRowNative(
                category_name="RF",
                current_value=400.0,
                projected_value=400.0,
            ),
        ],
        metrics=RebalancePlanMetricsNative(
            contribution=1000.0,
            total_buy=100.0,
            total_sell=100.0,
            residual_cash=0.0,
            current_deviation_pct=0.0,
            projected_deviation_pct=0.0,
        ),
        warnings=[],
        applied_policy="contribution-only",
    )

    def sentinel_solver(setup, positions, quotes, contribution):
        return native_plan

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    with _session(_omaha_test_env) as db:
        response = run_rebalance(
            db,
            profile,
            contribution=1000.0,
            solver=sentinel_solver,
        )

    actions = {row.asset_name: row.action for row in response.asset_plan}
    assert actions == {"Buy": "buy", "Sell": "sell", "Hold": "hold"}


def test_trade_quantity_derived_for_brl_usd_and_ineligible_rows(
    italo_profile: Profile, _omaha_test_env: dict[str, str]
) -> None:
    """Glue derives trade quantity from movement amount and quote basis."""
    _seed_class(italo_profile.id, "RF", "100", [("Selic", "100")], _omaha_test_env)

    from omaha.rebalance.solver_stub import (
        RebalanceAssetPlanRowNative,
        RebalanceCategoryPlanRowNative,
        RebalancePlan,
        RebalancePlanMetricsNative,
    )

    native_plan = RebalancePlan(
        contribution=1000.0,
        asset_classes=[],
        asset_plan=[
            RebalanceAssetPlanRowNative(
                name="BRL Buy",
                category_name="RF",
                currency_code="BRL",
                buy_enabled=True,
                current_value=100.0,
                target_value=200.0,
                buy_amount=1000.0,
                sell_amount=0.0,
                quote_price=20.0,
                projected_value=1100.0,
            ),
            RebalanceAssetPlanRowNative(
                name="USD Sell",
                category_name="RF",
                currency_code="USD",
                buy_enabled=True,
                current_value=200.0,
                target_value=100.0,
                buy_amount=0.0,
                sell_amount=540.0,
                quote_price=5.0,
                usdbrl_rate=5.4,
                quote_status="available",
                projected_value=100.0,
            ),
            RebalanceAssetPlanRowNative(
                name="USD Fallback Buy",
                category_name="RF",
                currency_code="USD",
                buy_enabled=True,
                current_value=4879.39,
                target_value=18339.65226,
                buy_amount=13460.26226,
                sell_amount=0.0,
                quote_price=392.88,
                usdbrl_rate=5.14,
                quote_status="not-requested",
                projected_value=18339.65226,
            ),
            RebalanceAssetPlanRowNative(
                name="No Price",
                category_name="RF",
                currency_code="BRL",
                buy_enabled=True,
                current_value=100.0,
                target_value=150.0,
                buy_amount=50.0,
                sell_amount=0.0,
                projected_value=150.0,
            ),
        ],
        category_plan=[
            RebalanceCategoryPlanRowNative(
                category_name="RF",
                current_value=400.0,
                projected_value=400.0,
            ),
        ],
        metrics=RebalancePlanMetricsNative(
            contribution=1000.0,
            total_buy=14460.26226,
            total_sell=540.0,
            residual_cash=0.0,
            current_deviation_pct=0.0,
            projected_deviation_pct=0.0,
        ),
        warnings=[],
        applied_policy="contribution-only",
    )

    def sentinel_solver(setup, positions, quotes, contribution):
        return native_plan

    profile = _refresh_profile(italo_profile, _omaha_test_env)
    with _session(_omaha_test_env) as db:
        response = run_rebalance(db, profile, contribution=1000.0, solver=sentinel_solver)

    quantities = {row.asset_name: row.trade_quantity for row in response.asset_plan}
    assert quantities["BRL Buy"] == pytest.approx(50.0)
    assert quantities["USD Sell"] == pytest.approx(20.0)
    assert quantities["USD Fallback Buy"] == pytest.approx(34.260492414986764)
    assert quantities["No Price"] is None
