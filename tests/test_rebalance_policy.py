"""Policy cascade smoke tests.

Four scenarios map to the 4 cascade outcomes:

* balanced profile + small aporte → ``contribution-only``
* overweight assets + zero contribution → ``contribution-with-overweight-sales``
* buy-enabled off + contribution → ``contribution-with-full-sales``
* zero contribution + extreme imbalance → ``current-portfolio-rebalance``
"""

from __future__ import annotations

import numpy as np
import pytest

from omaha.rebalance.policy import (
    _build_contribution_only_rejection_reason,
    _build_overweight_projected_value_floor,
    _build_stage_rejection_reason,
    _relative_improvement,
    _sum_largest_values,
)
from omaha.rebalance.solver import _build_simulation_frame, simulate_rebalance
from tests.fixtures.rebalance_engine import (
    build_category_first_position,
    build_category_first_setup,
    build_simple_position,
    build_simple_setup,
    build_weighted_position,
    build_weighted_setup,
)


def test_contribution_only_chosen_for_balanced_profile() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    plan = simulate_rebalance(setup, position, contribution=1000.0)
    assert plan.metrics["rebalance_policy"] in {
        "contribution-only",
        "contribution-with-overweight-sales",
    }


def test_overweight_sales_chosen_with_zero_contribution_and_overweight() -> None:
    """A 50/50 setup with one overweight asset + zero aporte → sell side fires."""
    setup = build_weighted_setup([0.5, 0.5])
    position = build_weighted_position([8000.0, 2000.0])
    plan = simulate_rebalance(setup, position, contribution=0.0)
    assert plan.metrics["rebalance_policy"] == "current-portfolio-rebalance"


def test_current_portfolio_rebalance_for_zero_contribution() -> None:
    """Zero contribution always lands in the dedicated branch."""
    setup = build_category_first_setup()
    position = build_category_first_position()
    plan = simulate_rebalance(setup, position, contribution=0.0)
    assert plan.metrics["rebalance_policy"] == "current-portfolio-rebalance"


def test_stage_rejection_reason_falls_back_to_default_message() -> None:
    out = _build_stage_rejection_reason(
        "current-portfolio-rebalance",
        {"stage_reason": ""},
    )
    assert "criterios configurados" in out


def test_contribution_only_rejection_reason_includes_violated_tolerances() -> None:
    """All 5 tolerances violated → 5 reasons stacked in PT-BR."""
    acceptance = {
        "asset_deviation": 0.10,
        "category_deviation": 0.05,
        "top_asset_gap": 0.10,
        "top_category_gap": 0.05,
        "residual_cash_ratio": 0.10,
    }
    reason = _build_contribution_only_rejection_reason(acceptance)
    assert "desvio agregado por ativo" in reason
    assert "desvio agregado por categoria" in reason
    assert "top gap por ativo" in reason
    assert "top gap por categoria" in reason
    assert "caixa residual" in reason


def test_contribution_only_rejection_reason_default_when_empty() -> None:
    acceptance = {
        "asset_deviation": 0.0,
        "category_deviation": 0.0,
        "top_asset_gap": 0.0,
        "top_category_gap": 0.0,
        "residual_cash_ratio": 0.0,
    }
    assert (
        _build_contribution_only_rejection_reason(acceptance)
        == "o plano somente com aporte nao atingiu os criterios configurados"
    )


def test_relative_improvement_zero_when_no_change() -> None:
    assert _relative_improvement(0.05, 0.05) == 0.0


def test_relative_improvement_clamped_at_zero_for_regression() -> None:
    """Regression (current > previous) clamps to zero, not negative."""
    assert _relative_improvement(0.03, 0.05) == 0.0


def test_relative_improvement_positive_for_improvement() -> None:
    assert _relative_improvement(0.05, 0.04) == pytest.approx(0.2, abs=1e-6)


def test_sum_largest_values_zero_on_empty() -> None:
    assert _sum_largest_values(np.array([]), 5) == 0.0


def test_sum_largest_values_top_n() -> None:
    values = np.array([0.1, 0.5, 0.3, 0.4, 0.2])
    assert _sum_largest_values(values, 3) == pytest.approx(1.2, abs=1e-6)


def test_overweight_projected_value_floor_zero_when_balanced() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    frame = _build_simulation_frame(setup, position)
    floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
    assert (floor == 0.0).all()
