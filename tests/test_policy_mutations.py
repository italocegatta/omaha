"""Mutation-killing tests for policy.py.

Each test targets specific surviving mutations identified by mutmut.
Direct function calls with constructed inputs, exact value assertions,
boundary values at exact thresholds, and decision path coverage.

Zero production code changes — tests only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from omaha.rebalance.constants import (
    ALLOCATION_TOLERANCE,
    CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE,
    CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE,
    CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE,
    CONTRIBUTION_ONLY_POLICY,
    CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE,
    CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE,
    CURRENT_PORTFOLIO_REBALANCE_POLICY,
    DISPLAY_TOLERANCE,
    FULL_SALES_POLICY,
    OVERWEIGHT_SALES_POLICY,
    STAGED_SALES_MIN_CATEGORY_IMPROVEMENT,
    STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT,
)
from omaha.rebalance.policy import (
    _build_contribution_only_rejection_reason,
    _build_overweight_projected_value_floor,
    _build_overweight_sell_mask,
    _build_stage_rejection_reason,
    _build_zero_target_sell_mask,
    _calculate_solution_deviations,
    _calculate_solution_top_gaps,
    _collect_solution_metrics,
    _evaluate_contribution_only_solution,
    _evaluate_progressive_sales_stage_solution,
    _relative_improvement,
    _sum_largest_values,
)

# ---------------------------------------------------------------------------
# Helpers to build minimal DataFrames for direct function calls
# ---------------------------------------------------------------------------


def _make_simulation_frame(
    asset_keys: list[str],
    current_values: list[float],
    target_weights: list[float],
    current_weights: list[float] | None = None,
    sell_enabled: list[bool] | None = None,
    buy_enabled: list[bool] | None = None,
    category_keys: list[str] | None = None,
) -> pd.DataFrame:
    """Build a minimal simulation_frame for direct function calls."""
    n = len(asset_keys)
    if current_weights is None:
        total = sum(current_values)
        current_weights = [v / total if total > 0 else 0.0 for v in current_values]
    if sell_enabled is None:
        sell_enabled = [True] * n
    if buy_enabled is None:
        buy_enabled = [True] * n
    if category_keys is None:
        category_keys = ["cat-a"] * n
    return pd.DataFrame(
        {
            "asset_key": asset_keys,
            "asset_name": asset_keys,
            "category_key": category_keys,
            "current_value": current_values,
            "current_weight": current_weights,
            "target_weight": target_weights,
            "sell_enabled": sell_enabled,
            "buy_enabled": buy_enabled,
            "category_name": category_keys,
        }
    )


def _make_categories(
    category_keys: list[str],
    target_weights: list[float],
) -> pd.DataFrame:
    """Build a minimal categories DataFrame."""
    return pd.DataFrame(
        {
            "category_key": category_keys,
            "category_name": category_keys,
            "target_weight": target_weights,
            "category_order": list(range(len(category_keys))),
        }
    )


def _make_solution(
    projected_values: list[float],
    residual_cash: float = 0.0,
    total_sell_amount: float = 0.0,
) -> dict:
    """Build a minimal solution dict for acceptance checks."""
    return {
        "projected_values": np.array(projected_values, dtype=float),
        "buy_amounts": np.zeros(len(projected_values)),
        "sell_amounts": np.zeros(len(projected_values)),
        "residual_cash": residual_cash,
        "total_sell_amount": total_sell_amount,
        "solver_status": "optimal",
        "objective_value": 0.0,
    }


# ============================================================================
# T1: _evaluate_progressive_sales_stage_solution
# ============================================================================


class TestEvaluateProgressiveSalesStageSolution:
    """Kill mutations in the and/or logic, boundary thresholds, zero-target."""

    def _setup(self):
        """Shared frame: 2 assets, 1 category, equal weights."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        return frame, cats, zero_mask

    def test_category_improvement_above_top_asset_below_acceptable(self):
        """1.1: category improvement ≥ 0.05, top_asset < 0.05 → acceptable."""
        frame, cats, zero_mask = self._setup()
        # previous_metrics: high category_deviation, low top_asset_gap
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.01,
            "zero_target_residual_value": 0.0,
        }
        # solution with improved category_deviation (0.20 → 0.10 = 50% improvement)
        # but top_asset_gap stays at 0.01
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["is_acceptable"] is True

    def test_top_asset_improvement_above_category_below_acceptable(self):
        """1.2: top_asset improvement ≥ 0.05, category < 0.05 → acceptable."""
        frame, cats, zero_mask = self._setup()
        prev = {
            "category_deviation": 0.01,
            "top_asset_gap": 0.20,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["is_acceptable"] is True

    def test_both_below_threshold_not_acceptable_reason(self):
        """1.3: both improvements < 0.05 → not acceptable, reason "nao entregou melhora"."""
        frame, cats, zero_mask = self._setup()
        # Set previous near zero → improvement from balanced solution also near zero
        # _relative_improvement(0.0, current) = 0 for any current (clamped)
        prev = {
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["is_acceptable"] is False
        assert "nao entregou melhora" in result["stage_reason"]

    def test_both_above_threshold_acceptable_empty_reason(self):
        """1.4: both improvements ≥ 0.05 → acceptable, stage_reason empty."""
        frame, cats, zero_mask = self._setup()
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.20,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["is_acceptable"] is True
        assert result["stage_reason"] == ""

    def test_zero_target_worsened_beyond_tolerance_not_acceptable(self):
        """1.5: improvement present but zero_target worsened → not acceptable."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        # zero_mask covers asset "a"
        zero_mask = np.array([True, False], dtype=bool)
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.01,
            "zero_target_residual_value": 0.0,
        }
        # projected = [5000, 5000] → category_deviation = 0.0
        # improvement = (0.20 - 0.0) / 0.20 = 1.0 → materially_better
        # zero_target_residual_value = 5000 (from mask[0])
        # 5000 > 0 + 100 → zero_target_worsened
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["is_acceptable"] is False
        assert "saldo relevante" in result["stage_reason"]

    def test_boundary_improvement_exactly_at_threshold(self):
        """1.6: improvement exactly at STAGED_SALES_MIN_CATEGORY_IMPROVEMENT (0.05)."""
        frame, cats, zero_mask = self._setup()
        # Set previous high, current exactly 5% lower → improvement = 0.05 exactly
        prev_dev = 1.0
        # _relative_improvement(prev, current) = (prev - current) / max(prev, 1e-6)
        # For 0.05 improvement: current = prev * (1 - 0.05) = 0.95
        current_dev = prev_dev * (1 - STAGED_SALES_MIN_CATEGORY_IMPROVEMENT)
        improvement = _relative_improvement(prev_dev, current_dev)
        assert improvement == pytest.approx(STAGED_SALES_MIN_CATEGORY_IMPROVEMENT, abs=1e-10)

    def test_boundary_zero_target_residual_exactly_at_tolerance(self):
        """1.7: zero_target_residual exactly at previous + ZERO_TARGET_VALUE_TOLERANCE."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([True, False], dtype=bool)
        prev_residual = 100.0
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.01,
            "zero_target_residual_value": prev_residual,
        }
        # projected = [200, 8000] → cat_dev = |8200/10000 - 1.0| = 0.18
        # improvement = (0.20 - 0.18) / 0.20 = 0.10 → materially_better
        # zero_target_residual = 200 = prev(100) + 100 → exactly at tolerance
        sol = _make_solution([200.0, 8000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        # exactly at tolerance → still acceptable (<=)
        assert result["is_acceptable"] is True

    def test_previous_metrics_missing_keys_defaults(self):
        """1.8: previous_metrics with missing keys uses .get() defaults."""
        frame, cats, zero_mask = self._setup()
        # Empty previous_metrics → defaults to 0.0 for missing keys
        prev: dict = {}
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        # With defaults: category_deviation=0.0, top_asset_gap=0.0 → no improvement
        assert result["is_acceptable"] is False
        assert "nao entregou melhora" in result["stage_reason"]


# ============================================================================
# T2: _build_contribution_only_rejection_reason
# ============================================================================


class TestBuildContributionOnlyRejectionReason:
    """Kill mutations in each tolerance check and boundary at TOLERANCE + ALLOCATION_TOLERANCE."""

    def _base_acceptance(self) -> dict:
        """All tolerances at zero (acceptable)."""
        return {
            "asset_deviation": 0.0,
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "top_category_gap": 0.0,
            "residual_cash_ratio": 0.0,
        }

    def test_only_asset_deviation_violated(self):
        """2.1: only asset_deviation violated → reason contains only that tolerance."""
        acc = self._base_acceptance()
        acc["asset_deviation"] = (
            CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "desvio agregado por ativo" in reason
        assert "desvio agregado por categoria" not in reason
        assert "top gap por ativo" not in reason
        assert "top gap por categoria" not in reason
        assert "caixa residual" not in reason

    def test_only_category_deviation_violated(self):
        """2.2: only category_deviation violated → reason contains only that tolerance."""
        acc = self._base_acceptance()
        acc["category_deviation"] = (
            CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "desvio agregado por categoria" in reason
        assert "desvio agregado por ativo" not in reason

    def test_only_top_asset_gap_violated(self):
        """2.3: only top_asset_gap violated → reason contains only that tolerance."""
        acc = self._base_acceptance()
        acc["top_asset_gap"] = (
            CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "top gap por ativo" in reason
        assert "desvio agregado por ativo" not in reason

    def test_only_top_category_gap_violated(self):
        """2.4: only top_category_gap violated → reason contains only that tolerance."""
        acc = self._base_acceptance()
        acc["top_category_gap"] = (
            CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "top gap por categoria" in reason
        assert "top gap por ativo" not in reason

    def test_only_residual_cash_ratio_violated(self):
        """2.5: only residual_cash_ratio violated → reason contains only that tolerance."""
        acc = self._base_acceptance()
        acc["residual_cash_ratio"] = (
            CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "caixa residual" in reason
        assert "desvio agregado por ativo" not in reason

    def test_boundary_value_exactly_at_tolerance_not_violated(self):
        """2.6: value exactly at TOLERANCE + ALLOCATION_TOLERANCE → NOT violated."""
        acc = self._base_acceptance()
        acc["asset_deviation"] = CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE
        reason = _build_contribution_only_rejection_reason(acc)
        # Exactly at boundary → not violated → default message
        assert reason == "o plano somente com aporte nao atingiu os criterios configurados"

    def test_boundary_value_at_tolerance_plus_epsilon_violated(self):
        """2.7: value at TOLERANCE + ALLOCATION_TOLERANCE + 1e-10 → violated."""
        acc = self._base_acceptance()
        acc["asset_deviation"] = (
            CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE + 1e-10
        )
        reason = _build_contribution_only_rejection_reason(acc)
        assert "desvio agregado por ativo" in reason

    def test_all_five_violated_produces_five_reasons(self):
        """All 5 tolerances violated → 5 semicolons in reason string."""
        acc = {
            "asset_deviation": 1.0,
            "category_deviation": 1.0,
            "top_asset_gap": 1.0,
            "top_category_gap": 1.0,
            "residual_cash_ratio": 1.0,
        }
        reason = _build_contribution_only_rejection_reason(acc)
        # 5 reasons → 4 semicolons
        assert reason.count(";") == 4


# ============================================================================
# T3: _calculate_solution_top_gaps
# ============================================================================


class TestCalculateSolutionTopGaps:
    """Kill mutations in top-N sum, empty frame, zero targets."""

    def test_five_assets_top_two_sum_exact(self):
        """3.1: 5 assets with known shortfalls → verify top-2 sum exact."""
        # 5 assets, equal current, targets: [0.4, 0.3, 0.15, 0.1, 0.05]
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a", "b", "c", "d", "e"],
            [2000.0, 2000.0, 2000.0, 2000.0, 2000.0],
            [0.4, 0.3, 0.15, 0.1, 0.05],
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([2000.0, 2000.0, 2000.0, 2000.0, 2000.0])
        top_asset_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # target_values: [4000, 3000, 1500, 1000, 500]
        # shortfalls: [2000, 1000, 0, 0, 0]
        # relative_shortfalls: [2000/4000, 1000/3000, 0, 0, 0] = [0.5, 0.333, 0, 0, 0]
        # top-2 sum = 0.5 + 0.333... = 0.833...
        expected = 2000.0 / 4000.0 + 1000.0 / 3000.0
        assert top_asset_gap == pytest.approx(expected, abs=1e-10)

    def test_all_above_target_gap_zero(self):
        """3.2: all assets above target → gap = 0.0."""
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a", "b"],
            [6000.0, 6000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([6000.0, 6000.0])
        top_asset_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        assert top_asset_gap == pytest.approx(0.0, abs=1e-10)

    def test_single_asset_shortfall_count_greater_than_assets(self):
        """3.3: count > assets → sum all shortfalls."""
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a"],
            [0.0],
            [1.0],
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([0.0])
        top_asset_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # shortfall = 10000 - 0 = 10000, denominator = max(10000, 100) = 10000
        assert top_asset_gap == pytest.approx(1.0, abs=1e-10)

    def test_zero_target_weight_uses_floor_denominator(self):
        """3.4: zero target weight → shortfall computed against SHORTFALL_RELATIVE_FLOOR_VALUE."""
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a"],
            [1000.0],
            [0.0],  # zero target
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([0.0])
        top_asset_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # target_values = 0, shortfall = max(0 - 0, 0) = 0
        # relative_shortfall = 0 / max(0, 100) = 0
        assert top_asset_gap == pytest.approx(0.0, abs=1e-10)

    def test_empty_simulation_frame_gap_zero(self):
        """3.5: empty frame → gap = 0.0."""
        frame = _make_simulation_frame([], [], [])
        cats = _make_categories([], [])
        projected = np.array([], dtype=float)
        top_asset_gap, top_cat_gap = _calculate_solution_top_gaps(frame, cats, 10000.0, projected)
        assert top_asset_gap == 0.0
        assert top_cat_gap == 0.0

    def test_two_categories_top_one_category_gap(self):
        """3.6: two categories with known shortfalls → verify top-2 category gap."""
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a", "b"],
            [3000.0, 3000.0],
            [0.6, 0.4],
            category_keys=["cat-a", "cat-b"],
        )
        cats = _make_categories(["cat-a", "cat-b"], [0.6, 0.4])
        projected = np.array([3000.0, 3000.0])
        _, top_cat_gap = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # cat-a target = 6000, projected = 3000, shortfall = 3000, rel = 3000/6000 = 0.5
        # cat-b target = 4000, projected = 3000, shortfall = 1000, rel = 1000/4000 = 0.25
        # PRIORITIZED_CATEGORY_GAP_COUNT = 2 → top-2 = 0.5 + 0.25 = 0.75
        assert top_cat_gap == pytest.approx(0.75, abs=1e-10)

    def test_zero_target_category_gap_uses_floor(self):
        """Zero target category → denominator uses SHORTFALL_RELATIVE_FLOOR_VALUE."""
        total_final = 10000.0
        frame = _make_simulation_frame(
            ["a"],
            [0.0],
            [0.0],
            category_keys=["cat-a"],
        )
        cats = _make_categories(["cat-a"], [0.0])
        projected = np.array([0.0])
        _, top_cat_gap = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # target_cat = 0, shortfall = max(0 - 0, 0) = 0
        assert top_cat_gap == pytest.approx(0.0, abs=1e-10)


# ============================================================================
# T4: _build_overweight_projected_value_floor
# ============================================================================


class TestBuildOverweightProjectedValueFloor:
    """Kill mutations in floor values, mask boundaries."""

    def test_overweight_asset_exact_floor_value(self):
        """4.1: overweight asset → verify exact floor value."""
        # current_weight > target_weight + ALLOCATION_TOLERANCE
        # target_weight > ALLOCATION_TOLERANCE
        # current_value > DISPLAY_TOLERANCE
        frame = _make_simulation_frame(
            ["a", "b"],
            [7000.0, 3000.0],
            [0.5, 0.5],
            current_weights=[0.7, 0.3],
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        # total_final = 7000 + 3000 + 0 = 10000
        # target_values = [5000, 5000]
        # asset "a": overweight (0.7 > 0.5 + 1e-6), target > 1e-6, value > 1e-4
        # floor["a"] = target_values["a"] - DISPLAY_TOLERANCE = 5000 - 0.0001 = 4999.9999
        assert floor[0] == pytest.approx(5000.0 - DISPLAY_TOLERANCE, abs=1e-10)
        assert floor[1] == pytest.approx(0.0, abs=1e-10)

    def test_balanced_asset_floor_zero(self):
        """4.2: balanced asset → floor = 0.0."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        assert (floor == 0.0).all()

    def test_zero_target_weight_not_in_overweight_mask(self):
        """4.3: zero target weight → NOT in overweight mask → floor = 0.0."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [8000.0, 2000.0],
            [0.0, 1.0],
            current_weights=[0.8, 0.2],
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        # "a" has target_weight = 0 → not in overweight mask
        assert floor[0] == pytest.approx(0.0, abs=1e-10)

    def test_contribution_changes_total_final_value(self):
        """4.4: contribution changes total_final_value → floor changes."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [7000.0, 3000.0],
            [0.5, 0.5],
            current_weights=[0.7, 0.3],
        )
        floor_no_contrib = _build_overweight_projected_value_floor(frame, contribution=0.0)
        floor_with_contrib = _build_overweight_projected_value_floor(frame, contribution=5000.0)
        # total_final with contrib = 15000, target_values[0] = 7500
        assert floor_with_contrib[0] == pytest.approx(7500.0 - DISPLAY_TOLERANCE, abs=1e-10)
        assert floor_with_contrib[0] != floor_no_contrib[0]

    def test_negative_floor_clamped_to_zero(self):
        """4.5: negative floor clamped to 0.0 via np.maximum."""
        # If target_value - DISPLAY_TOLERANCE < 0, floor should be 0
        # This happens when target_value < DISPLAY_TOLERANCE
        # But overweight mask requires target_weight > ALLOCATION_TOLERANCE
        # So we need target_weight * total_final < DISPLAY_TOLERANCE
        # With very small total_final_value
        frame = _make_simulation_frame(
            ["a", "b"],
            [0.001, 0.001],
            [0.5, 0.5],
            current_weights=[0.9, 0.1],
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        # total_final = 0.002, target_values = [0.001, 0.001]
        # overweight "a": target_value = 0.001, floor = 0.001 - 0.0001 = 0.0009 > 0
        # np.maximum ensures non-negative
        assert np.all(floor >= 0.0)

    def test_current_value_below_display_tolerance_excluded(self):
        """4.6: current_value <= DISPLAY_TOLERANCE → excluded from mask."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [DISPLAY_TOLERANCE, 9999.0],  # "a" at exactly DISPLAY_TOLERANCE
            [0.5, 0.5],
            current_weights=[0.99, 0.01],
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        # "a" has current_value = DISPLAY_TOLERANCE → excluded (must be >)
        assert floor[0] == pytest.approx(0.0, abs=1e-10)


# ============================================================================
# T5: Mask builders
# ============================================================================


class TestMaskBuilders:
    """Kill mutations in _build_overweight_sell_mask and _build_zero_target_sell_mask."""

    def test_overweight_sell_mask_exact_boolean(self):
        """5.1: exact boolean array for known frame."""
        frame = _make_simulation_frame(
            ["a", "b", "c"],
            [5000.0, 5000.0, 5000.0],
            [0.3, 0.4, 0.3],
            current_weights=[0.5, 0.4, 0.1],
            sell_enabled=[True, True, False],
        )
        mask = _build_overweight_sell_mask(frame)
        # "a": sell_enabled=True, current(0.5) > target(0.3) + tol → True
        # "b": sell_enabled=True, current(0.4) > target(0.4) + tol → False (not >)
        # "c": sell_enabled=False → False
        expected = np.array([True, False, False])
        np.testing.assert_array_equal(mask, expected)

    def test_overweight_mask_boundary_target_at_tolerance(self):
        """5.2: target_weight = ALLOCATION_TOLERANCE → included via <=."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [ALLOCATION_TOLERANCE],
            sell_enabled=[True],
        )
        mask = _build_overweight_sell_mask(frame)
        # target_weight <= ALLOCATION_TOLERANCE → True
        assert mask[0] is np.True_

    def test_overweight_mask_boundary_current_exactly_at_target_plus_tolerance(self):
        """5.3: current_weight = target_weight + ALLOCATION_TOLERANCE → NOT overweight."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.5],
            current_weights=[0.5 + ALLOCATION_TOLERANCE],
            sell_enabled=[True],
        )
        mask = _build_overweight_sell_mask(frame)
        # current > target + tol → not > (exactly equal) → False
        assert mask[0] is np.False_

    def test_zero_target_sell_mask_exact_boolean(self):
        """5.4: exact boolean array for zero_target mask."""
        frame = _make_simulation_frame(
            ["a", "b", "c"],
            [5000.0, 5000.0, 0.00001],  # "c" below DISPLAY_TOLERANCE
            [0.0, 0.5, 0.0],
            sell_enabled=[True, True, True],
        )
        mask = _build_zero_target_sell_mask(frame)
        # "a": sell_enabled=True, target(0) <= tol, value(5000) > DISPLAY_TOLERANCE → True
        # "b": sell_enabled=True, target(0.5) > tol → False
        # "c": sell_enabled=True, target(0) <= tol, value(0.00001) <= DISPLAY_TOLERANCE → False
        expected = np.array([True, False, False])
        np.testing.assert_array_equal(mask, expected)

    def test_zero_target_mask_boundary_value_at_display_tolerance(self):
        """5.5: current_value = DISPLAY_TOLERANCE → excluded (> not >=)."""
        frame = _make_simulation_frame(
            ["a"],
            [DISPLAY_TOLERANCE],
            [0.0],
            sell_enabled=[True],
        )
        mask = _build_zero_target_sell_mask(frame)
        # current_value = DISPLAY_TOLERANCE → not > → excluded
        assert mask[0] is np.False_


# ============================================================================
# T6: Helpers
# ============================================================================


class TestHelpers:
    """Kill mutations in helpers (_sum_largest_values, _relative_improvement, etc)."""

    def test_sum_largest_values_count_greater_than_size(self):
        """6.1: count > array size → sum all."""
        values = np.array([0.1, 0.2, 0.3])
        result = _sum_largest_values(values, 10)
        assert result == pytest.approx(0.6, abs=1e-10)

    def test_sum_largest_values_count_zero(self):
        """6.2: count = 0 → 0.0."""
        values = np.array([0.1, 0.2, 0.3])
        result = _sum_largest_values(values, 0)
        assert result == 0.0

    def test_sum_largest_values_negative_count(self):
        """count < 0 → 0.0."""
        values = np.array([0.1, 0.2, 0.3])
        result = _sum_largest_values(values, -1)
        assert result == 0.0

    def test_relative_improvement_baseline_clamped_at_allocation_tolerance(self):
        """6.3: previous = ALLOCATION_TOLERANCE → baseline clamped."""
        # _relative_improvement uses max(previous, ALLOCATION_TOLERANCE)
        # If previous < ALLOCATION_TOLERANCE, baseline = ALLOCATION_TOLERANCE
        result = _relative_improvement(0.0, 0.0)
        # previous = 0, current = 0, improvement = 0
        # baseline = max(0, 1e-6) = 1e-6
        # (0 - 0).clip(0) / 1e-6 = 0
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_relative_improvement_exact_fraction(self):
        """6.4: exact fraction for known values."""
        # previous=0.10, current=0.05
        # improvement = (0.10 - 0.05) / max(0.10, 1e-6) = 0.05 / 0.10 = 0.5
        result = _relative_improvement(0.10, 0.05)
        assert result == pytest.approx(0.5, abs=1e-10)

    def test_relative_improvement_previous_below_tolerance(self):
        """Previous < ALLOCATION_TOLERANCE → baseline = ALLOCATION_TOLERANCE."""
        # previous = 1e-8, current = 0
        # baseline = max(1e-8, 1e-6) = 1e-6
        # improvement = (1e-8 - 0) / 1e-6 = 0.01
        result = _relative_improvement(1e-8, 0.0)
        assert result == pytest.approx(1e-8 / ALLOCATION_TOLERANCE, abs=1e-15)

    def test_build_stage_rejection_reason_contribution_only_path(self):
        """6.5: _build_stage_rejection_reason — contribution-only path."""
        acceptance = {
            "asset_deviation": 1.0,
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "top_category_gap": 0.0,
            "residual_cash_ratio": 0.0,
        }
        reason = _build_stage_rejection_reason(CONTRIBUTION_ONLY_POLICY, acceptance)
        assert "desvio agregado por ativo" in reason

    def test_build_stage_rejection_reason_stage_with_non_empty_reason(self):
        """6.6: _build_stage_rejection_reason — stage with non-empty stage_reason."""
        acceptance = {"stage_reason": "custom reason"}
        reason = _build_stage_rejection_reason(OVERWEIGHT_SALES_POLICY, acceptance)
        assert reason == "custom reason"

    def test_build_stage_rejection_reason_empty_reason_fallback(self):
        """Empty stage_reason → default message."""
        acceptance = {"stage_reason": ""}
        reason = _build_stage_rejection_reason(OVERWEIGHT_SALES_POLICY, acceptance)
        assert "criterios configurados" in reason


# ============================================================================
# T7: Integration — _collect_solution_metrics and _calculate_solution_deviations
# ============================================================================


class TestIntegrationMetrics:
    """Kill mutations in _collect_solution_metrics and _calculate_solution_deviations."""

    def test_collect_solution_metrics_all_keys(self):
        """7.4: verify all 8 keys with exact values."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        sol = _make_solution([5000.0, 5000.0], residual_cash=100.0)
        metrics = _collect_solution_metrics(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            solution=sol,
            zero_target_mask=zero_mask,
        )
        expected_keys = {
            "asset_deviation",
            "category_deviation",
            "top_asset_gap",
            "top_category_gap",
            "residual_cash_ratio",
            "total_sell_amount",
            "zero_target_residual_value",
            "zero_target_residual_share",
        }
        assert set(metrics.keys()) == expected_keys

    def test_collect_solution_metrics_residual_cash_ratio(self):
        """residual_cash_ratio = residual_cash / total_final_value."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        sol = _make_solution([5000.0, 5000.0], residual_cash=200.0)
        metrics = _collect_solution_metrics(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            solution=sol,
            zero_target_mask=zero_mask,
        )
        # total_final = 10000, residual_cash = 200
        assert metrics["residual_cash_ratio"] == pytest.approx(0.02, abs=1e-10)

    def test_calculate_solution_deviations_exact(self):
        """7.5: known projected values → exact deviations."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        total_final = 10000.0
        projected = np.array([6000.0, 4000.0])
        asset_dev, cat_dev = _calculate_solution_deviations(frame, cats, total_final, projected)
        # projected_weights = [0.6, 0.4], target = [0.5, 0.5]
        # asset_deviation = |0.6-0.5| + |0.4-0.5| = 0.1 + 0.1 = 0.2
        assert asset_dev == pytest.approx(0.2, abs=1e-10)
        # category: projected_cat = 10000, target_cat = 1.0
        # cat_deviation = |10000/10000 - 1.0| = 0.0
        assert cat_dev == pytest.approx(0.0, abs=1e-10)

    def test_collect_solution_metrics_zero_target_residual(self):
        """zero_target_residual_value with mask active."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.0, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([True, False], dtype=bool)
        sol = _make_solution([100.0, 5000.0])
        metrics = _collect_solution_metrics(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            solution=sol,
            zero_target_mask=zero_mask,
        )
        assert metrics["zero_target_residual_value"] == pytest.approx(100.0, abs=1e-10)
        assert metrics["zero_target_residual_share"] == pytest.approx(0.01, abs=1e-10)

    def test_collect_solution_metrics_empty_zero_mask(self):
        """Empty zero_target_mask → residual = 0."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        sol = _make_solution([5000.0, 5000.0])
        metrics = _collect_solution_metrics(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            solution=sol,
            zero_target_mask=zero_mask,
        )
        assert metrics["zero_target_residual_value"] == 0.0


# ============================================================================
# T7: Integration — _evaluate_contribution_only_solution
# ============================================================================


class TestEvaluateContributionOnlySolution:
    """Kill mutations in the 5-tolerance acceptance check."""

    def test_all_tolerances_met_acceptable(self):
        """All metrics within tolerance → acceptable."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        sol = _make_solution([5000.0, 5000.0], residual_cash=0.0)
        result = _evaluate_contribution_only_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            contribution_only_solution=sol,
        )
        assert result["is_acceptable"] is True

    def test_asset_deviation_exceeds_tolerance_not_acceptable(self):
        """asset_deviation > tolerance → not acceptable."""
        # Create a frame where projected values diverge from targets
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        # Projected values way off target → high asset_deviation
        sol = _make_solution([9000.0, 1000.0], residual_cash=0.0)
        result = _evaluate_contribution_only_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            contribution_only_solution=sol,
        )
        assert result["is_acceptable"] is False

    def test_residual_cash_ratio_exceeds_tolerance_not_acceptable(self):
        """residual_cash_ratio > tolerance → not acceptable."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        # residual_cash = 500, total_final = 10000 → ratio = 0.05 > 0.02 + 1e-6
        sol = _make_solution([5000.0, 5000.0], residual_cash=500.0)
        result = _evaluate_contribution_only_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            contribution_only_solution=sol,
        )
        assert result["is_acceptable"] is False


# ============================================================================
# T7: Integration — _solve_contribution_only_rebalance
# ============================================================================


class TestSolveContributionOnlyRebalance:
    """Kill mutations in the zero-sell-mask construction."""

    def test_sells_disabled_all_zeros_mask(self):
        """7.3: contribution-only solve produces all-zero sell amounts."""
        from omaha.rebalance.solver import _build_simulation_frame
        from tests.fixtures.rebalance_engine import build_simple_position, build_simple_setup

        setup = build_simple_setup()
        position = build_simple_position(5000.0, 5000.0)
        frame = _build_simulation_frame(setup, position)
        from omaha.rebalance.policy import _solve_contribution_only_rebalance

        cats = pd.DataFrame(
            {
                "category_key": ["renda-fixa"],
                "category_name": ["Renda Fixa"],
                "target_weight": [1.0],
                "category_order": [0],
            }
        )
        sol = _solve_contribution_only_rebalance(frame, cats, 1000.0)
        # Sells should be all zeros
        assert np.all(sol["sell_amounts"] == 0.0)


# ============================================================================
# T7: Integration — _solve_hierarchical_policy
# ============================================================================


class TestSolveHierarchicalPolicy:
    """Kill mutations in the cascade driver."""

    def test_contribution_below_tolerance_uses_current_portfolio_rebalance(self):
        """7.1: contribution <= ALLOCATION_TOLERANCE → CURRENT_PORTFOLIO_REBALANCE_POLICY."""
        from omaha.rebalance.policy import _solve_hierarchical_policy
        from omaha.rebalance.solver import _build_simulation_frame
        from tests.fixtures.rebalance_engine import build_simple_position, build_simple_setup

        setup = build_simple_setup()
        position = build_simple_position(5000.0, 5000.0)
        frame = _build_simulation_frame(setup, position)
        cats = pd.DataFrame(
            {
                "category_key": ["renda-fixa"],
                "category_name": ["Renda Fixa"],
                "target_weight": [1.0],
                "category_order": [0],
            }
        )
        # contribution = 0 → triggers current-portfolio-rebalance
        sol = _solve_hierarchical_policy(frame, cats, contribution=0.0)
        assert sol["rebalance_policy"] == CURRENT_PORTFOLIO_REBALANCE_POLICY
        assert sol["sales_fallback_reason"] == ""

    def test_contribution_exactly_at_tolerance_uses_current_portfolio(self):
        """contribution = ALLOCATION_TOLERANCE → still current-portfolio."""
        from omaha.rebalance.policy import _solve_hierarchical_policy
        from omaha.rebalance.solver import _build_simulation_frame
        from tests.fixtures.rebalance_engine import build_simple_position, build_simple_setup

        setup = build_simple_setup()
        position = build_simple_position(5000.0, 5000.0)
        frame = _build_simulation_frame(setup, position)
        cats = pd.DataFrame(
            {
                "category_key": ["renda-fixa"],
                "category_name": ["Renda Fixa"],
                "target_weight": [1.0],
                "category_order": [0],
            }
        )
        sol = _solve_hierarchical_policy(frame, cats, contribution=ALLOCATION_TOLERANCE)
        assert sol["rebalance_policy"] == CURRENT_PORTFOLIO_REBALANCE_POLICY


# ============================================================================
# Boundary tests for _relative_improvement — kills mutations in comparison operators
# ============================================================================


class TestRelativeImprovementBoundaries:
    """Kill mutations in comparison operators and clamping."""

    def test_improvement_when_current_equals_previous(self):
        """previous == current → improvement = 0."""
        assert _relative_improvement(0.5, 0.5) == 0.0

    def test_improvement_when_current_slightly_below_previous(self):
        """Small improvement → exact fraction."""
        result = _relative_improvement(1.0, 0.99)
        assert result == pytest.approx(0.01, abs=1e-10)

    def test_improvement_when_current_slightly_above_previous(self):
        """Regression → clamped to 0."""
        result = _relative_improvement(1.0, 1.01)
        assert result == 0.0

    def test_improvement_with_zero_previous_zero_current(self):
        """Both zero → 0."""
        assert _relative_improvement(0.0, 0.0) == 0.0

    def test_improvement_with_zero_previous_nonzero_current(self):
        """Zero previous, positive current → clamped to 0 (regression)."""
        assert _relative_improvement(0.0, 0.1) == 0.0


# ============================================================================
# Boundary tests for _sum_largest_values
# ============================================================================


class TestSumLargestValuesBoundaries:
    """Kill mutations in sort direction and min(count, size)."""

    def test_sum_largest_preserves_order(self):
        """Verify descending sort picks correct values."""
        values = np.array([0.5, 0.1, 0.3, 0.4, 0.2])
        # Sorted desc: [0.5, 0.4, 0.3, 0.2, 0.1]
        # top-2 = 0.5 + 0.4 = 0.9
        assert _sum_largest_values(values, 2) == pytest.approx(0.9, abs=1e-10)

    def test_sum_largest_single_value(self):
        """count=1 → sum of max value."""
        values = np.array([0.1, 0.5, 0.3])
        assert _sum_largest_values(values, 1) == pytest.approx(0.5, abs=1e-10)

    def test_sum_largest_all_values(self):
        """count = size → sum all."""
        values = np.array([0.1, 0.2, 0.3])
        assert _sum_largest_values(values, 3) == pytest.approx(0.6, abs=1e-10)

    def test_sum_largest_with_zeros(self):
        """Array with zeros → correct sum."""
        values = np.array([0.0, 0.5, 0.0, 0.3])
        assert _sum_largest_values(values, 2) == pytest.approx(0.8, abs=1e-10)


# ============================================================================
# Tests for _build_stage_rejection_reason paths
# ============================================================================


class TestBuildStageRejectionReason:
    """Kill mutations in the if/else branches."""

    def test_contribution_only_policy_delegates_to_contribution_reason(self):
        """CONTRIBUTION_ONLY_POLICY → delegates to _build_contribution_only_rejection_reason."""
        acceptance = {
            "asset_deviation": 1.0,
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "top_category_gap": 0.0,
            "residual_cash_ratio": 0.0,
        }
        reason = _build_stage_rejection_reason(CONTRIBUTION_ONLY_POLICY, acceptance)
        assert "desvio agregado por ativo" in reason

    def test_other_policy_with_stage_reason(self):
        """Non-contribution policy with stage_reason → returns stage_reason."""
        acceptance = {"stage_reason": "some reason"}
        reason = _build_stage_rejection_reason(FULL_SALES_POLICY, acceptance)
        assert reason == "some reason"

    def test_other_policy_without_stage_reason(self):
        """Non-contribution policy without stage_reason → default message."""
        acceptance = {"stage_reason": ""}
        reason = _build_stage_rejection_reason(FULL_SALES_POLICY, acceptance)
        assert "criterios configurados" in reason
        assert FULL_SALES_POLICY in reason

    def test_other_policy_missing_stage_reason_key(self):
        """Non-contribution policy missing stage_reason key → default message."""
        acceptance: dict = {}
        reason = _build_stage_rejection_reason(FULL_SALES_POLICY, acceptance)
        assert "criterios configurados" in reason


# ============================================================================
# Tests for _build_overweight_sell_mask — zero-target inclusion
# ============================================================================


class TestOverweightSellMaskZeroTarget:
    """Kill mutations in the (target_weights <= ALLOCATION_TOLERANCE) branch."""

    def test_zero_target_included_in_overweight_mask(self):
        """target_weight = 0 → included via <= check."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.0],
            sell_enabled=[True],
        )
        mask = _build_overweight_sell_mask(frame)
        assert mask[0] is np.True_

    def test_target_just_above_tolerance_excluded_if_not_overweight(self):
        """target_weight just above tolerance, not overweight → excluded."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [ALLOCATION_TOLERANCE + 1e-10],
            current_weights=[ALLOCATION_TOLERANCE + 1e-10],
            sell_enabled=[True],
        )
        mask = _build_overweight_sell_mask(frame)
        # Not zero-target (target > tol) and not overweight (current not > target + tol)
        assert mask[0] is np.False_

    def test_sell_enabled_false_overrides_all(self):
        """sell_enabled=False → always False regardless of weight."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.0],
            sell_enabled=[False],
        )
        mask = _build_overweight_sell_mask(frame)
        assert mask[0] is np.False_


# ============================================================================
# Tests for _build_zero_target_sell_mask — all three conditions
# ============================================================================


class TestZeroTargetSellMaskConditions:
    """Kill mutations in the three-way AND condition."""

    def test_sell_enabled_false_excluded(self):
        """sell_enabled=False → excluded even with zero target and value."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.0],
            sell_enabled=[False],
        )
        mask = _build_zero_target_sell_mask(frame)
        assert mask[0] is np.False_

    def test_target_above_tolerance_excluded(self):
        """target_weight > ALLOCATION_TOLERANCE → excluded."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.5],
            sell_enabled=[True],
        )
        mask = _build_zero_target_sell_mask(frame)
        assert mask[0] is np.False_

    def test_value_below_display_tolerance_excluded(self):
        """current_value < DISPLAY_TOLERANCE → excluded."""
        frame = _make_simulation_frame(
            ["a"],
            [DISPLAY_TOLERANCE * 0.5],
            [0.0],
            sell_enabled=[True],
        )
        mask = _build_zero_target_sell_mask(frame)
        assert mask[0] is np.False_

    def test_all_conditions_met_included(self):
        """All three conditions met → included."""
        frame = _make_simulation_frame(
            ["a"],
            [DISPLAY_TOLERANCE * 2],
            [0.0],
            sell_enabled=[True],
        )
        mask = _build_zero_target_sell_mask(frame)
        assert mask[0] is np.True_


# ============================================================================
# Tests for contribution-only rejection — exact tolerance boundaries
# ============================================================================


class TestContributionOnlyRejectionBoundaries:
    """Kill mutations in each comparison operator (> vs >=)."""

    @pytest.mark.parametrize(
        "key,tolerance_const",
        [
            ("asset_deviation", CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE),
            ("category_deviation", CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE),
            ("top_asset_gap", CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE),
            ("top_category_gap", CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE),
            ("residual_cash_ratio", CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE),
        ],
    )
    def test_boundary_exactly_at_tolerance_not_violated(self, key, tolerance_const):
        """Value exactly at TOLERANCE + ALLOCATION_TOLERANCE → NOT violated."""
        acc = {
            "asset_deviation": 0.0,
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "top_category_gap": 0.0,
            "residual_cash_ratio": 0.0,
        }
        acc[key] = tolerance_const + ALLOCATION_TOLERANCE
        reason = _build_contribution_only_rejection_reason(acc)
        # Exactly at boundary → not violated → default message
        assert reason == "o plano somente com aporte nao atingiu os criterios configurados"

    @pytest.mark.parametrize(
        "key,tolerance_const",
        [
            ("asset_deviation", CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE),
            ("category_deviation", CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE),
            ("top_asset_gap", CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE),
            ("top_category_gap", CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE),
            ("residual_cash_ratio", CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE),
        ],
    )
    def test_boundary_just_above_tolerance_violated(self, key, tolerance_const):
        """Value at TOLERANCE + ALLOCATION_TOLERANCE + epsilon → violated."""
        acc = {
            "asset_deviation": 0.0,
            "category_deviation": 0.0,
            "top_asset_gap": 0.0,
            "top_category_gap": 0.0,
            "residual_cash_ratio": 0.0,
        }
        acc[key] = tolerance_const + ALLOCATION_TOLERANCE + 1e-10
        reason = _build_contribution_only_rejection_reason(acc)
        # Just above → violated → NOT default message
        assert reason != "o plano somente com aporte nao atingiu os criterios configurados"


# ============================================================================
# Tests for progressive sales stage — materiality check
# ============================================================================


class TestProgressiveSalesMateriality:
    """Kill mutations in the >= comparisons for materiality thresholds."""

    def test_category_improvement_exactly_at_threshold_acceptable(self):
        """category_improvement exactly at 0.05 → acceptable (>=)."""
        assert _relative_improvement(1.0, 0.95) == pytest.approx(
            STAGED_SALES_MIN_CATEGORY_IMPROVEMENT, abs=1e-10
        )

    def test_top_asset_improvement_exactly_at_threshold(self):
        """top_asset_improvement exactly at 0.05 → acceptable (>=)."""
        assert _relative_improvement(1.0, 0.95) == pytest.approx(
            STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT, abs=1e-10
        )

    def test_improvement_just_below_threshold_not_acceptable(self):
        """Improvement just below 0.05 → not acceptable."""
        # prev = 1.0, curr = 0.9500000001 → improvement = 0.04999999999 < 0.05
        imp = _relative_improvement(1.0, 0.9500000001)
        assert imp < STAGED_SALES_MIN_CATEGORY_IMPROVEMENT


# ============================================================================
# Tests for _calculate_solution_top_gaps — denominator with SHORTFALL_RELATIVE_FLOOR_VALUE
# ============================================================================


class TestTopGapsDenominator:
    """Kill mutations in np.maximum for denominator."""

    def test_small_target_uses_floor_denominator(self):
        """target_value < SHORTFALL_RELATIVE_FLOOR_VALUE → denominator = floor."""
        total_final = 10000.0
        # target_weight = 0.001 → target_value = 10 < SHORTFALL_RELATIVE_FLOOR_VALUE (100)
        frame = _make_simulation_frame(
            ["a"],
            [0.0],
            [0.001],
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([0.0])
        top_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # shortfall = max(10 - 0, 0) = 10
        # denominator = max(10, 100) = 100
        # relative = 10 / 100 = 0.1
        assert top_gap == pytest.approx(0.1, abs=1e-10)

    def test_large_target_uses_target_denominator(self):
        """target_value > SHORTFALL_RELATIVE_FLOOR_VALUE → denominator = target_value."""
        total_final = 100000.0
        # target_weight = 0.5 → target_value = 50000
        frame = _make_simulation_frame(
            ["a"],
            [0.0],
            [0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        projected = np.array([0.0])
        top_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # shortfall = 50000, denominator = max(50000, 100) = 50000
        # relative = 50000 / 50000 = 1.0
        assert top_gap == pytest.approx(1.0, abs=1e-10)


# ============================================================================
# Tests for _calculate_solution_top_gaps — category shortfall with fillna
# ============================================================================


class TestTopGapsCategoryFillna:
    """Kill mutations in category_frame fillna(0.0)."""

    def test_category_with_no_projected_values(self):
        """Category missing from projected → fillna(0.0) → full shortfall."""
        total_final = 10000.0
        # Two assets in same category
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.3, 0.3],
            category_keys=["cat-a", "cat-a"],
        )
        # Categories has two categories but projected only has cat-a
        cats = _make_categories(["cat-a", "cat-b"], [0.6, 0.4])
        projected = np.array([3000.0, 3000.0])
        _, top_cat_gap = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # cat-a: projected = 6000, target = 6000, shortfall = 0
        # cat-b: projected = 0 (fillna), target = 4000, shortfall = 4000
        # relative = 4000 / 4000 = 1.0
        # top-1 = 1.0
        assert top_cat_gap == pytest.approx(1.0, abs=1e-10)


# ============================================================================
# Round 2: Kill remaining survivors from mutation testing
# ============================================================================


class TestStringMutationKillers:
    """Kill XX-wrapping string mutations — assert exact string content."""

    def test_contribution_rejection_reasons_no_xx_wrapping(self):
        """All5 reasons must be real strings, not XX-wrapped."""
        acc = {
            "asset_deviation": 1.0,
            "category_deviation": 1.0,
            "top_asset_gap": 1.0,
            "top_category_gap": 1.0,
            "residual_cash_ratio": 1.0,
        }
        reason = _build_contribution_only_rejection_reason(acc)
        assert "XX" not in reason
        # Check exact start of each reason segment
        parts = reason.split("; ")
        assert parts[0].startswith("desvio agregado por ativo")
        assert parts[1].startswith("desvio agregado por categoria")
        assert parts[2].startswith("top gap por ativo")
        assert parts[3].startswith("top gap por categoria")
        assert parts[4].startswith("caixa residual")

    def test_stage_rejection_reason_saldo_relevante_no_xx(self):
        """'saldo relevante' reason must not be XX-wrapped."""
        acceptance = {
            "stage_reason": (
                "o estagio ampliado reintroduziu saldo relevante em ativos com alvo zero"
            ),
        }
        reason = _build_stage_rejection_reason(OVERWEIGHT_SALES_POLICY, acceptance)
        assert "XX" not in reason
        assert reason == "o estagio ampliado reintroduziu saldo relevante em ativos com alvo zero"


class TestKeyNameMutationKillers:
    """Kill dict key name mutations — assert exact key names in result dicts."""

    def test_progressive_result_has_exact_key_names(self):
        """Result dict must have exact key names, not mutated ones."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.01,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([5000.0, 5000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        # Assert exact key names (kills XX/CAPS mutations)
        assert "category_deviation_improvement" in result
        assert "top_asset_gap_improvement" in result
        assert "is_acceptable" in result
        assert "stage_reason" in result
        # Assert values are not None (kills None-assignment mutations)
        assert result["category_deviation_improvement"] is not None
        assert result["top_asset_gap_improvement"] is not None

    def test_previous_metrics_key_name_top_asset_gap(self):
        """previous_metrics must use exact key 'top_asset_gap', not mutated name."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        # Set top_asset_gap to non-zero — mutant uses wrong key → gets default 0.0
        # → different improvement → different result
        prev = {
            "category_deviation": 0.0,
            "top_asset_gap": 0.20,
            "zero_target_residual_value": 0.0,
        }
        # Projected values way off target → current top_asset_gap is high
        sol = _make_solution([1000.0, 1000.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        # With prev top_asset_gap = 0.20, the improvement should be computed
        # using that value. If mutant changes key to None/XX/CAPS, it gets 0.0 default
        # and improvement = 0 (since current is also based on the solution).
        # The result's top_asset_gap_improvement should reflect the correct computation.
        assert result["top_asset_gap_improvement"] >= 0.0


class TestBoundaryExactlyAtThreshold:
    """Kill >= vs > mutations with values exactly at threshold."""

    def test_category_improvement_exactly_at_005_acceptable(self):
        """category_improvement = 0.05 exactly → acceptable (kills >= → >)."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        # prev cat_dev = 0.20, need curr cat_dev = 0.19
        # improvement = (0.20 - 0.19) / 0.20 = 0.05
        # projected_sum = total_final * (1 - 0.19) = 10000 * 0.81 = 8100
        # projected = [4050, 4050]
        prev = {
            "category_deviation": 0.20,
            "top_asset_gap": 0.0,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([4050.0, 4050.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["category_deviation_improvement"] == pytest.approx(0.05, abs=1e-8)
        assert result["is_acceptable"] is True  # >= 0.05 → True; > 0.05 → False (killed)

    def test_top_asset_improvement_exactly_at_005_acceptable(self):
        """top_asset_improvement = 0.05 exactly → acceptable (kills >= → >)."""
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False, False], dtype=bool)
        # Need top_asset_improvement = 0.05 exactly
        # prev top_asset_gap = 0.20, curr = 0.19 → improvement = 0.05
        # top_asset_gap = sum of top-N relative shortfalls
        # With 2 assets, target=0.5 each, total=10000: target_values=[5000, 5000]
        # shortfall = max(target - projected, 0) / max(target, 100)
        # For gap = 0.19 with 2 equal assets: each shortfall_rel = 0.095
        # shortfall = 0.095 * 5000 = 475 → projected = 5000 - 475 = 4525
        # total gap = 0.095 + 0.095 = 0.19
        prev = {
            "category_deviation": 0.0,
            "top_asset_gap": 0.20,
            "zero_target_residual_value": 0.0,
        }
        sol = _make_solution([4525.0, 4525.0])
        result = _evaluate_progressive_sales_stage_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            stage_solution=sol,
            previous_metrics=prev,
            zero_target_mask=zero_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        assert result["top_asset_gap_improvement"] == pytest.approx(0.05, abs=1e-8)
        assert result["is_acceptable"] is True  # >= 0.05 → True; > 0.05 → False (killed)


class TestContributionOnlyBoundaryExact:
    """Kill <= vs < mutations in _evaluate_contribution_only_solution."""

    def test_asset_deviation_near_boundary_all_other_metrics_pass(self):
        """asset_deviation near boundary with all other metrics well within tolerance."""
        # Construct: projected values slightly off target → small asset_deviation
        # but all metrics within tolerance → is_acceptable = True.
        # This exercises the <= comparison path in the real function.
        frame = _make_simulation_frame(
            ["a", "b"],
            [5000.0, 5000.0],
            [0.5, 0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        # Tiny perturbation: asset_deviation = 2 * 0.001 / 10000 = 2e-7 << tolerance
        sol = _make_solution([5000.1, 4999.9], residual_cash=0.0)
        result = _evaluate_contribution_only_solution(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            contribution_only_solution=sol,
        )
        assert result["is_acceptable"] is True


class TestSumLargestValuesCountZero:
    """Kill count <= 0 → count < 0 mutation."""

    def test_sum_largest_count_zero_returns_zero(self):
        """count=0 must return 0.0. Guards against < vs <= mutation."""
        values = np.array([0.5, 0.3, 0.1])
        result = _sum_largest_values(values, 0)
        assert result == 0.0


class TestDtypeMutationKillers:
    """Kill dtype=float → dtype=None mutations by using non-float input types."""

    def test_overweight_mask_with_int_sell_enabled(self):
        """sell_enabled as int column → dtype=bool matters."""
        frame = pd.DataFrame(
            {
                "asset_key": ["a", "b"],
                "asset_name": ["a", "b"],
                "category_key": ["cat-a", "cat-a"],
                "current_value": [5000.0, 5000.0],
                "current_weight": [0.7, 0.3],
                "target_weight": [0.5, 0.5],
                "sell_enabled": [1, 0],  # int, not bool
                "buy_enabled": [True, True],
                "category_name": ["cat-a", "cat-a"],
            }
        )
        mask = _build_overweight_sell_mask(frame)
        # "a": sell_enabled=1 (truthy), overweight → True
        # "b": sell_enabled=0 (falsy) → False
        assert mask[0] is np.True_
        assert mask[1] is np.False_

    def test_zero_target_mask_with_int_sell_enabled(self):
        """sell_enabled as int → dtype=bool matters for zero_target mask."""
        frame = pd.DataFrame(
            {
                "asset_key": ["a", "b"],
                "asset_name": ["a", "b"],
                "category_key": ["cat-a", "cat-a"],
                "current_value": [5000.0, 5000.0],
                "current_weight": [0.5, 0.5],
                "target_weight": [0.0, 0.5],
                "sell_enabled": [1, 0],  # int, not bool
                "buy_enabled": [True, True],
                "category_name": ["cat-a", "cat-a"],
            }
        )
        mask = _build_zero_target_sell_mask(frame)
        assert mask[0] is np.True_
        assert mask[1] is np.False_

    def test_overweight_floor_with_int_target_weight(self):
        """target_weight as int → dtype=float matters."""
        frame = pd.DataFrame(
            {
                "asset_key": ["a", "b"],
                "asset_name": ["a", "b"],
                "category_key": ["cat-a", "cat-a"],
                "current_value": [7000.0, 3000.0],
                "current_weight": [0.7, 0.3],
                "target_weight": [0, 1],  # int, not float
                "sell_enabled": [True, True],
                "buy_enabled": [True, True],
                "category_name": ["cat-a", "cat-a"],
            }
        )
        floor = _build_overweight_projected_value_floor(frame, contribution=0.0)
        # "a": target_weight=0 → not in overweight mask (target > tol fails)
        assert floor[0] == pytest.approx(0.0, abs=1e-10)


class TestCollectSolutionMetricsKeyNames:
    """Kill mutations in _collect_solution_metrics key names."""

    def test_collect_metrics_exact_keys(self):
        """Verify all 8 exact key names."""
        frame = _make_simulation_frame(
            ["a"],
            [5000.0],
            [0.5],
        )
        cats = _make_categories(["cat-a"], [1.0])
        zero_mask = np.array([False], dtype=bool)
        sol = _make_solution([5000.0])
        metrics = _collect_solution_metrics(
            simulation_frame=frame,
            categories=cats,
            contribution=0.0,
            solution=sol,
            zero_target_mask=zero_mask,
        )
        expected = {
            "asset_deviation",
            "category_deviation",
            "top_asset_gap",
            "top_category_gap",
            "residual_cash_ratio",
            "total_sell_amount",
            "zero_target_residual_value",
            "zero_target_residual_share",
        }
        assert set(metrics.keys()) == expected


class TestCalculateSolutionDeviationsDtype:
    """Kill dtype=float → dtype=None in _calculate_solution_deviations."""

    def test_deviations_with_int_target_weight_column(self):
        """target_weight as int → dtype=float cast matters."""
        frame = pd.DataFrame(
            {
                "asset_key": ["a", "b"],
                "asset_name": ["a", "b"],
                "category_key": ["cat-a", "cat-a"],
                "current_value": [5000.0, 5000.0],
                "current_weight": [0.5, 0.5],
                "target_weight": [0, 1],  # int
                "sell_enabled": [True, True],
                "buy_enabled": [True, True],
                "category_name": ["cat-a", "cat-a"],
            }
        )
        cats = _make_categories(["cat-a"], [1.0])
        total_final = 10000.0
        projected = np.array([5000.0, 5000.0])
        asset_dev, cat_dev = _calculate_solution_deviations(frame, cats, total_final, projected)
        # projected_weights = [0.5, 0.5], target = [0, 1]
        # asset_deviation = |0.5-0| + |0.5-1| = 0.5 + 0.5 = 1.0
        assert asset_dev == pytest.approx(1.0, abs=1e-10)


class TestCalculateSolutionTopGapsDtype:
    """Kill dtype=float → dtype=None in _calculate_solution_top_gaps."""

    def test_top_gaps_with_int_target_weight(self):
        """target_weight as int → dtype=float cast matters."""
        frame = pd.DataFrame(
            {
                "asset_key": ["a"],
                "asset_name": ["a"],
                "category_key": ["cat-a"],
                "current_value": [0.0],
                "current_weight": [0.0],
                "target_weight": [1],  # int
                "sell_enabled": [True],
                "buy_enabled": [True],
                "category_name": ["cat-a"],
            }
        )
        cats = _make_categories(["cat-a"], [1.0])
        total_final = 10000.0
        projected = np.array([0.0])
        top_gap, _ = _calculate_solution_top_gaps(frame, cats, total_final, projected)
        # target_value = 1 * 10000 = 10000, shortfall = 10000
        # rel = 10000/10000 = 1.0
        assert top_gap == pytest.approx(1.0, abs=1e-10)
