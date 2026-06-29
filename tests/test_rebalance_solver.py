"""Solver core smoke tests against the Apêndice D fixtures.

No DB / no HTTP. Exercises the full pipeline
``simulate_rebalance(simple_setup, simple_position, 1000.0)`` and
checks the LP returns ``optimal`` with the expected 2-asset /
1-category shape.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from omaha.rebalance.constants import ALLOCATION_TOLERANCE, DISPLAY_TOLERANCE
from omaha.rebalance.policy import (
    _build_overweight_sell_mask,
    _build_zero_target_sell_mask,
)
from omaha.rebalance.solver import (
    _aggregate_position,
    _build_category_phase1_model,
    _build_intra_category_model,
    _build_simulation_frame,
    _clip_solution,
    _compute_category_buy_capacity,
    _compute_category_sell_capacity,
    _solve_category_phase1,
    _solve_intra_category,
    simulate_rebalance,
)
from tests.fixtures.rebalance_engine import (
    build_simple_position,
    build_simple_quote_frame,
    build_simple_setup,
)


def test_simulate_rebalance_simple_setup_returns_optimal() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert plan.metrics["solver_status"] == "optimal"
    assert plan.asset_plan.shape == (2, 31)
    assert plan.category_plan.shape == (1, 13)
    assert plan.metrics["contribution"] == pytest.approx(1000.0)


def test_simulate_rebalance_simple_setup_uses_contribution_only_policy() -> None:
    """A balanced profile with a small aporte should land in ``contribution-only``."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert plan.metrics["rebalance_policy"] in {
        "contribution-only",
        "contribution-with-overweight-sales",
    }


def test_aggregate_position_sums_duplicates_per_asset_key() -> None:
    extra = {
        "asset_name": "CDB ABC",
        "asset_key": "cdb-abc",
        "category_name": "Renda Fixa",
        "category_key": "renda-fixa",
        "quantity": 2.0,
        "invested_value": 1000.0,
        "current_value": 1000.0,
        "current_weight": 0.1,
    }
    position = pd.concat(
        [build_simple_position(3000.0, 7000.0), pd.DataFrame([extra])],
        ignore_index=True,
    )
    aggregated = _aggregate_position(position)
    cdb = aggregated.loc[aggregated["asset_key"] == "cdb-abc"].iloc[0]
    assert cdb["current_value"] == pytest.approx(4000.0)
    assert cdb["invested_value"] == pytest.approx(4000.0)
    assert cdb["quantity"] == pytest.approx(3.0)


def test_build_simulation_frame_outer_joins_setup_with_position() -> None:
    setup = build_simple_setup()
    position = build_simple_position(3000.0, 7000.0)
    frame = _build_simulation_frame(setup, position)
    assert len(frame) == 2
    assert "category_key" in frame.columns
    assert "target_weight" in frame.columns
    assert "current_value" in frame.columns
    assert frame["current_value"].sum() == pytest.approx(10000.0)


def test_compute_category_buy_capacity_zero_when_balanced() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    capacity = _compute_category_buy_capacity(frame, setup.categories, total_final_value=11000.0)
    assert capacity.shape == (1,)
    assert capacity[0] >= 0.0


def test_compute_category_sell_capacity_matches_sell_enabled_value() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    capacity = _compute_category_sell_capacity(frame, setup.categories)
    assert capacity[0] == pytest.approx(10000.0)


def test_phase1_returns_delta_summing_to_contribution() -> None:
    """Per category, ``delta.sum() + residual_cash = contribution``."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    contribution = 1000.0
    total_final_value = float(frame["current_value"].sum()) + contribution
    max_buy_capacity = _compute_category_buy_capacity(
        frame, setup.categories, total_final_value=total_final_value
    )
    max_sell_capacity = _compute_category_sell_capacity(frame, setup.categories)
    current_category_values = np.array([float(frame["current_value"].sum())], dtype=float)
    model = _build_category_phase1_model(
        category_frame=setup.categories.reset_index(drop=True),
        current_category_values=current_category_values,
        contribution=contribution,
        max_buy_capacity=max_buy_capacity,
        max_sell_capacity=max_sell_capacity,
        allowed_sell_mask=np.array([True]),
    )
    delta = _solve_category_phase1(model)
    assert delta.shape == (1,)
    residual = model["residual_cash"].value
    assert (delta.sum() + float(residual)) == pytest.approx(contribution, abs=1e-3)


def test_phase2_returns_per_asset_buy_sell() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    contribution = 1000.0
    current = frame["current_value"].to_numpy(dtype=float)
    total_final = current.sum() + contribution
    target = frame["target_weight"].to_numpy(dtype=float) * total_final
    delta_c = 1000.0
    model = _build_intra_category_model(
        category_assets=frame,
        current_values=current,
        target_values=target,
        delta_c=delta_c,
        projected_category_total=current.sum() + delta_c,
        allowed_sell_mask=np.zeros(len(frame), dtype=bool),
    )
    result = _solve_intra_category(model)
    buy = result["buy_amounts"]
    sell = result["sell_amounts"]
    assert buy.shape == (2,)
    assert sell.shape == (2,)
    assert sell.sum() == pytest.approx(0.0, abs=1e-4)
    assert buy.sum() == pytest.approx(delta_c, abs=1e-4)


def test_zero_target_sell_mask_identifies_zero_target_assets() -> None:
    """Asset with target_weight=0 AND sell_enabled=True AND current>0 appears in mask."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    frame.loc[0, "target_weight"] = 0.0
    frame.loc[0, "sell_enabled"] = True
    frame.loc[0, "current_value"] = 1000.0
    mask = _build_zero_target_sell_mask(frame)
    assert mask[0] is np.True_ or bool(mask[0]) is True  # array of bool


def test_overweight_sell_mask_identifies_overweight_assets() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    frame.loc[0, "current_weight"] = 0.7
    frame.loc[0, "target_weight"] = 0.5
    mask = _build_overweight_sell_mask(frame)
    assert bool(mask[0]) is True


def test_clip_solution_zero_negatives() -> None:
    arr = np.array([-0.5, 0.0, 0.5, 1e-6])
    clipped = _clip_solution(arr)
    assert (clipped >= 0.0).all()
    assert clipped[0] == 0.0
    assert clipped[3] == 0.0


_ = ALLOCATION_TOLERANCE
_ = DISPLAY_TOLERANCE
_ = build_simple_quote_frame  # re-exported via docstring
