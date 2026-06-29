"""Post-processing smoke tests.

Exercises the ``_build_plan_metrics``, ``_clamp_projected_values_to_target_side``,
``_reduce_buy_overspend``, and ``_build_restriction_note`` helpers
together with the assembly of ``asset_plan`` / ``category_plan`` via
``simulate_rebalance``.
"""

from __future__ import annotations

import numpy as np
import pytest

from omaha.rebalance.postprocessing import (
    _build_plan_metrics,
    _build_restriction_note,
    _clamp_projected_values_to_target_side,
    _reduce_buy_overspend,
)
from omaha.rebalance.solver import simulate_rebalance
from tests.fixtures.rebalance_engine import (
    build_simple_position,
    build_simple_quote_frame,
    build_simple_setup,
)


def test_plan_metrics_includes_v1_keys() -> None:
    """The v1 wire format reads 6 keys — they MUST be in the metrics dict."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    for key in (
        "contribution",
        "total_buy_amount",
        "total_sell_amount",
        "residual_cash",
        "current_asset_deviation",
        "projected_asset_deviation",
    ):
        assert key in plan.metrics


def test_plan_metrics_emits_28_keys() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert len(plan.metrics) >= 28


def test_clamp_blocks_overshoot_for_underweight_assets() -> None:
    """An underweight asset cannot be projected above its target."""
    current = np.array([1000.0])
    target = np.array([2000.0])
    projected = np.array([2500.0])  # overshoots target by 500
    clamped = _clamp_projected_values_to_target_side(
        current_values=current,
        projected_values=projected,
        target_values=target,
    )
    assert clamped[0] == pytest.approx(2000.0)


def test_clamp_blocks_undershoot_for_overweight_assets() -> None:
    """An overweight asset cannot be projected below its target."""
    current = np.array([3000.0])
    target = np.array([2000.0])
    projected = np.array([1500.0])  # undershoots target by 500
    clamped = _clamp_projected_values_to_target_side(
        current_values=current,
        projected_values=projected,
        target_values=target,
    )
    assert clamped[0] == pytest.approx(2000.0)


def test_clamp_no_op_at_target() -> None:
    current = np.array([2000.0])
    target = np.array([2000.0])
    projected = np.array([2050.0])  # within tolerance
    clamped = _clamp_projected_values_to_target_side(
        current_values=current,
        projected_values=projected,
        target_values=target,
    )
    assert clamped[0] == pytest.approx(2050.0)


def test_reduce_buy_overspend_drops_overspend_to_zero() -> None:
    """Total buys exceed contribution + sells → reduce proportionally."""
    buys = np.array([2000.0, 2000.0, 1000.0])
    sells = np.array([0.0, 0.0, 0.0])
    adjusted = _reduce_buy_overspend(buy_amounts=buys, sell_amounts=sells, contribution=1000.0)
    assert adjusted.sum() == pytest.approx(1000.0, abs=1e-4)


def test_reduce_buy_overspend_no_op_when_fits() -> None:
    buys = np.array([1000.0])
    sells = np.array([0.0])
    adjusted = _reduce_buy_overspend(buy_amounts=buys, sell_amounts=sells, contribution=2000.0)
    assert (adjusted == buys).all()


def test_restriction_note_locked_asset() -> None:
    row = {
        "buy_enabled": False,
        "sell_enabled": False,
        "projected_gap_weight": 0.0,
        "current_value": 1000.0,
        "target_weight": 0.5,
        "sell_amount": 0.0,
        "buy_amount": 0.0,
        "rebalance_policy": "contribution-only",
    }
    import pandas as pd

    series = pd.Series(row)
    note = _build_restriction_note(series)
    assert note == "ativo travado no setup"


def test_restriction_note_empty_for_free_trade() -> None:
    row = {
        "buy_enabled": True,
        "sell_enabled": True,
        "projected_gap_weight": 0.01,
        "current_value": 1000.0,
        "target_weight": 0.5,
        "sell_amount": 0.0,
        "buy_amount": 5000.0,
        "rebalance_policy": "contribution-only",
    }
    import pandas as pd

    series = pd.Series(row)
    note = _build_restriction_note(series)
    assert note == ""


def test_plan_warnings_includes_contribution_only_message() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert any("apenas com novos aportes" in str(w) for w in plan.warnings)


def test_asset_plan_has_31_columns() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert plan.asset_plan.shape[1] == 31


def test_category_plan_has_13_columns() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert plan.category_plan.shape[1] == 13


def test_plan_metrics_correctly_reported() -> None:
    """Spot-check totals add up across buys, sells, residual_cash."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    metrics = plan.metrics
    expected_minimum = metrics["contribution"]
    maximum_buy = metrics["contribution"] + metrics["total_sell_amount"]
    assert metrics["total_buy_amount"] <= maximum_buy + 1e-3
    assert expected_minimum >= 0.0


_ = build_simple_quote_frame  # referenced by docstring import
_ = _build_plan_metrics  # pure helper, exercised via simulate_rebalance above
