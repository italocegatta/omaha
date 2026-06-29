"""Hierarchical policy cascade for the rebalance solver.

Ports reference section 6 + helpers from ``rebalancing.py:705-1182``.
The four cascading policies are:

1. ``contribution-only`` — solve with sells disabled; accept if all
   five contribution-only tolerances pass.
2. ``contribution-with-overweight-sales`` — relax the sell mask to
   overweight assets only; accept if the solution materially improves
   category / top-asset gap AND does not worsen the zero-target
   residual.
3. ``contribution-with-full-sales`` — relax the sell mask further to
   any sell-enabled asset; always returned when the previous stages
   failed (acts as a deterministic fallback).
4. ``current-portfolio-rebalance`` — direct branch for
   ``contribution <= ALLOCATION_TOLERANCE`` (no aporte, sell freely).

The cascade is driven by :func:`_solve_hierarchical_policy`; every
helper it calls is exported with a leading underscore because it is
internal to the solver package.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

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
    PRIORITIZED_ASSET_GAP_COUNT,
    PRIORITIZED_CATEGORY_GAP_COUNT,
    SHORTFALL_RELATIVE_FLOOR_VALUE,
    STAGED_SALES_MIN_CATEGORY_IMPROVEMENT,
    STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT,
    ZERO_TARGET_VALUE_TOLERANCE,
)
from omaha.rebalance.solver import (
    _build_intra_category_model,
    _build_optimizer_parameters,
    _compute_category_buy_capacity,
    _compute_category_sell_capacity,
    _solve_category_phase1,
    _solve_intra_category,
)


def _solve_hierarchical_policy(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
) -> dict[str, Any]:
    """Cascade driver — runs the policy cascade and returns the chosen solution.

    Port of ``rebalancing.py:705-787``.
    """
    if contribution <= ALLOCATION_TOLERANCE:
        solution = _run_hierarchical_plan(
            simulation_frame=simulation_frame,
            categories=categories,
            contribution=contribution,
            allowed_sell_mask=simulation_frame["sell_enabled"].to_numpy(dtype=bool),
        )
        solution["rebalance_policy"] = CURRENT_PORTFOLIO_REBALANCE_POLICY
        solution["sales_fallback_reason"] = ""
        return solution

    no_sell_solution = _solve_contribution_only_rebalance(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
    )
    acceptance = _evaluate_contribution_only_solution(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
        contribution_only_solution=no_sell_solution,
    )
    if bool(acceptance["is_acceptable"]):
        no_sell_solution["rebalance_policy"] = CONTRIBUTION_ONLY_POLICY
        no_sell_solution["sales_fallback_reason"] = ""
        return no_sell_solution

    previous_stage_key = CONTRIBUTION_ONLY_POLICY
    previous_metrics = acceptance

    overweight_mask = _build_overweight_sell_mask(simulation_frame)
    zero_target_mask = _build_zero_target_sell_mask(simulation_frame)
    if overweight_mask.any():
        overweight_solution = _run_hierarchical_plan(
            simulation_frame=simulation_frame,
            categories=categories,
            contribution=contribution,
            allowed_sell_mask=overweight_mask,
        )
        overweight_acceptance = _evaluate_progressive_sales_stage_solution(
            simulation_frame=simulation_frame,
            categories=categories,
            contribution=contribution,
            stage_solution=overweight_solution,
            previous_metrics=previous_metrics,
            zero_target_mask=zero_target_mask,
            stage_name=OVERWEIGHT_SALES_POLICY,
        )
        if bool(overweight_acceptance["is_acceptable"]):
            overweight_solution["rebalance_policy"] = OVERWEIGHT_SALES_POLICY
            overweight_solution["sales_fallback_reason"] = _build_stage_rejection_reason(
                previous_stage_key,
                previous_metrics,
            )
            return overweight_solution
        previous_stage_key = OVERWEIGHT_SALES_POLICY
        previous_metrics = overweight_acceptance

    fallback_solution = _run_hierarchical_plan(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
        allowed_sell_mask=simulation_frame["sell_enabled"].to_numpy(dtype=bool),
    )
    fallback_solution["rebalance_policy"] = FULL_SALES_POLICY
    fallback_solution["sales_fallback_reason"] = _build_stage_rejection_reason(
        previous_stage_key,
        previous_metrics,
    )
    return fallback_solution


def _solve_contribution_only_rebalance(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
) -> dict[str, Any]:
    """Solve with sells disabled — first stage of the cascade."""
    return _run_hierarchical_plan(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
        allowed_sell_mask=np.zeros(len(simulation_frame), dtype=bool),
    )


def _build_zero_target_sell_mask(simulation_frame: pd.DataFrame) -> np.ndarray:
    """Per-asset mask: ``sell_enabled`` AND ``target_weight <= 1e-6`` AND ``current_value > 1e-4``.

    Used to compute the zero-target residual that the staged-sales
    acceptance check must NOT worsen. Port of
    ``rebalancing.py:803-811``.
    """
    return (
        simulation_frame["sell_enabled"].to_numpy(dtype=bool)
        & (simulation_frame["target_weight"].to_numpy(dtype=float) <= ALLOCATION_TOLERANCE)
        & (simulation_frame["current_value"].to_numpy(dtype=float) > DISPLAY_TOLERANCE)
    )


def _build_overweight_sell_mask(simulation_frame: pd.DataFrame) -> np.ndarray:
    """Per-asset mask: ``sell_enabled`` AND (target_weight <= 1e-6 OR overweight).

    Drives the ``contribution-with-overweight-sales`` stage —
    overrides the global sell ban only for assets that look
    genuinely overweight or that the operator has tagged for
    graceful exit. Port of ``rebalancing.py:814-821``.
    """
    sell_enabled = simulation_frame["sell_enabled"].to_numpy(dtype=bool)
    target_weights = simulation_frame["target_weight"].to_numpy(dtype=float)
    current_weights = simulation_frame["current_weight"].to_numpy(dtype=float)
    return sell_enabled & (
        (target_weights <= ALLOCATION_TOLERANCE)
        | (current_weights > target_weights + ALLOCATION_TOLERANCE)
    )


def _build_overweight_projected_value_floor(
    simulation_frame: pd.DataFrame,
    contribution: float,
) -> np.ndarray:
    """Projected-value floor for overweight assets in staged-sales stages.

    Not used directly by the cascade driver but exported for tests
    / future solvers that want to clamp the projected values of
    overweight assets in staged-sales stages.
    Port of ``rebalancing.py:824-844``.
    """
    total_final_value = float(simulation_frame["current_value"].sum()) + contribution
    target_values = simulation_frame["target_weight"].to_numpy(dtype=float) * total_final_value
    current_values = simulation_frame["current_value"].to_numpy(dtype=float)
    target_weights = simulation_frame["target_weight"].to_numpy(dtype=float)
    current_weights = simulation_frame["current_weight"].to_numpy(dtype=float)
    overweight_positive_target_mask = (
        (target_weights > ALLOCATION_TOLERANCE)
        & (current_weights > target_weights + ALLOCATION_TOLERANCE)
        & (current_values > DISPLAY_TOLERANCE)
    )
    projected_value_floor = np.zeros(len(simulation_frame), dtype=float)
    projected_value_floor[overweight_positive_target_mask] = (
        target_values[overweight_positive_target_mask] - DISPLAY_TOLERANCE
    )
    return np.maximum(projected_value_floor, 0.0)


def _run_hierarchical_plan(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
    *,
    allowed_sell_mask: np.ndarray,
) -> dict[str, Any]:
    """Top-level orchestration — Phase 1 + Phase 2 + per-category loop.

    Port of ``rebalancing.py:570-702``. Returns a solution dict
    compatible with the legacy format: ``projected_values``,
    ``buy_amounts``, ``sell_amounts``, ``residual_cash``,
    ``total_sell_amount``, ``solver_status``, ``objective_value``,
    ``rebalance_policy``, ``sales_fallback_reason``, ``stage_values``,
    ``optimizer_parameters``. The caller (``_solve_hierarchical_policy``)
    fills in ``rebalance_policy`` / ``sales_fallback_reason`` after
    choosing the cascade outcome.
    """
    current_values = simulation_frame["current_value"].to_numpy(dtype=float)
    total_current_value = float(current_values.sum())
    total_final_value = total_current_value + contribution

    target_weights_global = simulation_frame["target_weight"].to_numpy(dtype=float)
    target_values_global = target_weights_global * total_final_value

    category_frame = categories.sort_values("category_order").reset_index(drop=True)

    max_buy_capacity = _compute_category_buy_capacity(
        simulation_frame=simulation_frame,
        categories=category_frame,
        total_final_value=total_final_value,
    )
    max_sell_capacity = _compute_category_sell_capacity(
        simulation_frame=simulation_frame,
        categories=category_frame,
    )

    n_categories = len(category_frame)
    category_sell_allowed = np.zeros(n_categories, dtype=bool)
    for ci, category_key in enumerate(category_frame["category_key"]):
        mask = simulation_frame["category_key"].eq(category_key).to_numpy(dtype=bool)
        sell_enabled_in_cat = simulation_frame.loc[mask, "sell_enabled"].to_numpy(dtype=bool)
        allowed_in_cat = allowed_sell_mask[mask]
        category_sell_allowed[ci] = bool((sell_enabled_in_cat & allowed_in_cat).any())

    incidence = np.zeros((n_categories, len(simulation_frame)))
    for ci, category_key in enumerate(category_frame["category_key"]):
        mask = simulation_frame["category_key"].eq(category_key).to_numpy(dtype=float)
        incidence[ci, :] = mask
    current_category_values = incidence @ current_values

    phase1_model = _build_category_phase1_model_kwargs(
        category_frame=category_frame,
        current_category_values=current_category_values,
        contribution=contribution,
        max_buy_capacity=max_buy_capacity,
        max_sell_capacity=max_sell_capacity,
        allowed_sell_mask=category_sell_allowed,
    )
    delta_category = _solve_category_phase1(phase1_model)

    projected_values_global = np.zeros(len(simulation_frame), dtype=float)
    buy_amounts_global = np.zeros(len(simulation_frame), dtype=float)
    sell_amounts_global = np.zeros(len(simulation_frame), dtype=float)
    worst_solver_status = "optimal"

    for ci, category_key in enumerate(category_frame["category_key"]):
        cat_mask = simulation_frame["category_key"].eq(category_key).to_numpy(dtype=bool)
        cat_indices = np.flatnonzero(cat_mask)
        category_assets = simulation_frame.iloc[cat_indices].reset_index(drop=True)
        cat_current_values = current_values[cat_indices]

        delta_c = float(delta_category[ci])
        projected_cat_total = float(current_category_values[ci]) + delta_c

        buy_en = category_assets["buy_enabled"].to_numpy(dtype=bool)
        sell_en = (
            category_assets["sell_enabled"].to_numpy(dtype=bool) & allowed_sell_mask[cat_indices]
        )
        if not buy_en.any() and not sell_en.any():
            projected_values_global[cat_indices] = cat_current_values
            continue

        if abs(delta_c) < ALLOCATION_TOLERANCE and not sell_en.any():
            projected_values_global[cat_indices] = cat_current_values
            continue

        phase2_model = _build_intra_category_model(
            category_assets=category_assets,
            current_values=cat_current_values,
            target_values=target_values_global[cat_indices],
            delta_c=delta_c,
            projected_category_total=projected_cat_total,
            allowed_sell_mask=allowed_sell_mask[cat_indices],
        )
        phase2_result = _solve_intra_category(phase2_model)

        buy_vals = phase2_result["buy_amounts"]
        sell_vals = phase2_result["sell_amounts"]
        buy_amounts_global[cat_indices] = buy_vals
        sell_amounts_global[cat_indices] = sell_vals
        projected_values_global[cat_indices] = cat_current_values + buy_vals - sell_vals

        from cvxpy import OPTIMAL_INACCURATE  # imported lazily to avoid module-level coupling

        if str(phase2_result["solver_status"]) == str(OPTIMAL_INACCURATE):
            worst_solver_status = str(OPTIMAL_INACCURATE)

    residual_cash = max(
        contribution + float(sell_amounts_global.sum()) - float(buy_amounts_global.sum()),
        0.0,
    )

    return {
        "projected_values": projected_values_global,
        "buy_amounts": buy_amounts_global,
        "sell_amounts": sell_amounts_global,
        "residual_cash": residual_cash,
        "total_sell_amount": float(sell_amounts_global.sum()),
        "solver_status": worst_solver_status,
        "objective_value": 0.0,
        "rebalance_policy": "",
        "sales_fallback_reason": "",
        "stage_values": {},
        "optimizer_parameters": _build_optimizer_parameters(),
    }


# Lazy import of the Phase 1 builder (kept here to avoid solver.py's
# import cycle: solver.py imports this module, this module imports
# back from solver.py).
def _build_category_phase1_model_kwargs(**kwargs: Any) -> dict[str, Any]:
    from omaha.rebalance.solver import _build_category_phase1_model

    return _build_category_phase1_model(**kwargs)


def _evaluate_contribution_only_solution(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
    contribution_only_solution: dict[str, Any],
) -> dict[str, Any]:
    """Acceptance check for the contribution-only stage (5 tolerances)."""
    metrics = _collect_solution_metrics(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
        solution=contribution_only_solution,
        zero_target_mask=_build_zero_target_sell_mask(simulation_frame),
    )
    is_acceptable = (
        float(metrics["asset_deviation"])
        <= CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE
        and float(metrics["category_deviation"])
        <= CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE
        and float(metrics["top_asset_gap"])
        <= CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE + ALLOCATION_TOLERANCE
        and float(metrics["top_category_gap"])
        <= CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE + ALLOCATION_TOLERANCE
        and float(metrics["residual_cash_ratio"])
        <= CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE + ALLOCATION_TOLERANCE
    )
    metrics["is_acceptable"] = is_acceptable
    return metrics


def _evaluate_progressive_sales_stage_solution(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
    stage_solution: dict[str, Any],
    previous_metrics: dict[str, Any],
    zero_target_mask: np.ndarray,
    stage_name: str,
) -> dict[str, Any]:
    """Acceptance check for staged-sales stages (improvement + zero-target)."""
    metrics = _collect_solution_metrics(
        simulation_frame=simulation_frame,
        categories=categories,
        contribution=contribution,
        solution=stage_solution,
        zero_target_mask=zero_target_mask,
    )
    category_improvement = _relative_improvement(
        float(previous_metrics.get("category_deviation", 0.0)),
        float(metrics["category_deviation"]),
    )
    top_asset_improvement = _relative_improvement(
        float(previous_metrics.get("top_asset_gap", 0.0)),
        float(metrics["top_asset_gap"]),
    )
    zero_target_not_worse = (
        float(metrics["zero_target_residual_value"])
        <= float(
            previous_metrics.get(
                "zero_target_residual_value",
                metrics["zero_target_residual_value"],
            )
        )
        + ZERO_TARGET_VALUE_TOLERANCE
    )
    materially_better = (
        category_improvement >= STAGED_SALES_MIN_CATEGORY_IMPROVEMENT
        or top_asset_improvement >= STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT
    )
    is_acceptable = materially_better and zero_target_not_worse
    if not materially_better:
        stage_reason = (
            f"o estagio {stage_name} nao entregou melhora material "
            f"nos gaps priorizados (categoria {category_improvement:.2%}; "
            f"ativo {top_asset_improvement:.2%})"
        )
    elif not zero_target_not_worse:
        stage_reason = "o estagio ampliado reintroduziu saldo relevante em ativos com alvo zero"
    else:
        stage_reason = ""

    metrics["category_deviation_improvement"] = category_improvement
    metrics["top_asset_gap_improvement"] = top_asset_improvement
    metrics["is_acceptable"] = is_acceptable
    metrics["stage_reason"] = stage_reason
    return metrics


def _collect_solution_metrics(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
    solution: dict[str, Any],
    zero_target_mask: np.ndarray,
) -> dict[str, float]:
    """Per-stage metrics — surfaces 8 keys consumed by the acceptance checks.

    Note: this is NOT :func:`omaha.rebalance.postprocessing._build_plan_metrics`.
    The cascade accepts/rejects stages based on these 8 keys
    (``asset_deviation``, ``category_deviation``, ``top_asset_gap``,
    ``top_category_gap``, ``residual_cash_ratio``,
    ``total_sell_amount``, ``zero_target_residual_value``,
    ``zero_target_residual_share``). The plan-level metrics live in
    :mod:`omaha.rebalance.postprocessing`.

    Port of ``rebalancing.py:990-1025``.
    """
    total_final_value = float(simulation_frame["current_value"].sum()) + contribution
    projected_values = np.asarray(solution["projected_values"], dtype=float)
    asset_deviation, category_deviation = _calculate_solution_deviations(
        simulation_frame=simulation_frame,
        categories=categories,
        total_final_value=total_final_value,
        projected_values=projected_values,
    )
    top_asset_gap, top_category_gap = _calculate_solution_top_gaps(
        simulation_frame=simulation_frame,
        categories=categories,
        total_final_value=total_final_value,
        projected_values=projected_values,
    )
    zero_target_residual_value = (
        float(projected_values[zero_target_mask].sum()) if zero_target_mask.any() else 0.0
    )
    return {
        "asset_deviation": asset_deviation,
        "category_deviation": category_deviation,
        "top_asset_gap": top_asset_gap,
        "top_category_gap": top_category_gap,
        "residual_cash_ratio": float(solution["residual_cash"]) / total_final_value,
        "total_sell_amount": float(solution["total_sell_amount"]),
        "zero_target_residual_value": zero_target_residual_value,
        "zero_target_residual_share": zero_target_residual_value / total_final_value,
    }


def _calculate_solution_deviations(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    total_final_value: float,
    projected_values: np.ndarray,
) -> tuple[float, float]:
    """Per-asset and per-category deviation aggregates.

    Port of ``rebalancing.py:1028-1058``.
    """
    projected_weights = projected_values / total_final_value
    asset_deviation = float(
        np.abs(projected_weights - simulation_frame["target_weight"].to_numpy(dtype=float)).sum()
    )

    category_totals = (
        simulation_frame.assign(projected_value=projected_values)
        .groupby("category_key", as_index=False)["projected_value"]
        .sum()
    )
    category_frame = categories[["category_key", "target_weight"]].merge(
        category_totals,
        how="left",
        on="category_key",
    )
    category_frame["projected_value"] = category_frame["projected_value"].fillna(0.0)
    category_deviation = float(
        np.abs(
            category_frame["projected_value"] / total_final_value - category_frame["target_weight"]
        ).sum()
    )
    return asset_deviation, category_deviation


def _calculate_solution_top_gaps(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    total_final_value: float,
    projected_values: np.ndarray,
) -> tuple[float, float]:
    """Top-N relative shortfalls at the asset and category level.

    Port of ``rebalancing.py:1061-1104``.
    """
    target_values = simulation_frame["target_weight"].to_numpy(dtype=float) * total_final_value
    asset_shortfalls = np.maximum(target_values - projected_values, 0.0)
    asset_denominator = np.maximum(target_values, SHORTFALL_RELATIVE_FLOOR_VALUE)
    asset_relative_shortfalls = asset_shortfalls / asset_denominator

    category_totals = (
        simulation_frame.assign(projected_value=projected_values)
        .groupby("category_key", as_index=False)["projected_value"]
        .sum()
    )
    category_frame = categories[["category_key", "target_weight"]].merge(
        category_totals,
        how="left",
        on="category_key",
    )
    category_frame["projected_value"] = category_frame["projected_value"].fillna(0.0)
    target_category_values = (
        category_frame["target_weight"].to_numpy(dtype=float) * total_final_value
    )
    category_shortfalls = np.maximum(
        target_category_values - category_frame["projected_value"].to_numpy(dtype=float),
        0.0,
    )
    category_denominator = np.maximum(
        target_category_values,
        SHORTFALL_RELATIVE_FLOOR_VALUE,
    )
    category_relative_shortfalls = category_shortfalls / category_denominator

    return (
        _sum_largest_values(asset_relative_shortfalls, PRIORITIZED_ASSET_GAP_COUNT),
        _sum_largest_values(category_relative_shortfalls, PRIORITIZED_CATEGORY_GAP_COUNT),
    )


def _sum_largest_values(values: np.ndarray, count: int) -> float:
    """Sum the largest ``count`` values in ``values`` (after a sort)."""
    if values.size == 0 or count <= 0:
        return 0.0
    clipped = np.sort(np.asarray(values, dtype=float))[::-1]
    return float(clipped[: min(count, clipped.size)].sum())


def _relative_improvement(previous: float, current: float) -> float:
    """(previous - current).clip(0) / max(previous, 1e-6)."""
    baseline = max(previous, ALLOCATION_TOLERANCE)
    return max(previous - current, 0.0) / baseline


def _build_stage_rejection_reason(
    stage_name: str,
    acceptance: dict[str, Any],
) -> str:
    """PT-BR string describing why a stage was rejected."""
    if stage_name == CONTRIBUTION_ONLY_POLICY:
        return _build_contribution_only_rejection_reason(acceptance)
    reason = str(acceptance.get("stage_reason", "")).strip()
    if reason:
        return reason
    return f"o estagio {stage_name} nao atingiu os criterios configurados"


def _build_contribution_only_rejection_reason(acceptance: dict[str, Any]) -> str:
    """Concatenate a ; -separated string of every contribution-only violation."""
    reasons: list[str] = []
    if (
        float(acceptance["asset_deviation"])
        > CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE
    ):
        reasons.append(
            "desvio agregado por ativo acima da tolerancia "
            f"({float(acceptance['asset_deviation']):.2%} > "
            f"{CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE:.2%})"
        )
    if (
        float(acceptance["category_deviation"])
        > CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE + ALLOCATION_TOLERANCE
    ):
        reasons.append(
            "desvio agregado por categoria acima da tolerancia "
            f"({float(acceptance['category_deviation']):.2%} > "
            f"{CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE:.2%})"
        )
    if (
        float(acceptance["top_asset_gap"])
        > CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE + ALLOCATION_TOLERANCE
    ):
        reasons.append(
            "top gap por ativo acima da tolerancia "
            f"({float(acceptance['top_asset_gap']):.2%} > "
            f"{CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE:.2%})"
        )
    if (
        float(acceptance["top_category_gap"])
        > CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE + ALLOCATION_TOLERANCE
    ):
        reasons.append(
            "top gap por categoria acima da tolerancia "
            f"({float(acceptance['top_category_gap']):.2%} > "
            f"{CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE:.2%})"
        )
    if (
        float(acceptance["residual_cash_ratio"])
        > CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE + ALLOCATION_TOLERANCE
    ):
        reasons.append(
            "caixa residual acima do limite "
            f"({float(acceptance['residual_cash_ratio']):.2%} > "
            f"{CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE:.2%})"
        )
    if not reasons:
        return "o plano somente com aporte nao atingiu os criterios configurados"
    return "; ".join(reasons)


__all__ = [
    "CONTRIBUTION_ONLY_POLICY",
    "CURRENT_PORTFOLIO_REBALANCE_POLICY",
    "FULL_SALES_POLICY",
    "OVERWEIGHT_SALES_POLICY",
    "_build_contribution_only_rejection_reason",
    "_build_overweight_projected_value_floor",
    "_build_overweight_sell_mask",
    "_build_stage_rejection_reason",
    "_build_zero_target_sell_mask",
    "_calculate_solution_deviations",
    "_calculate_solution_top_gaps",
    "_collect_solution_metrics",
    "_evaluate_contribution_only_solution",
    "_evaluate_progressive_sales_stage_solution",
    "_relative_improvement",
    "_run_hierarchical_plan",
    "_solve_contribution_only_rebalance",
    "_solve_hierarchical_policy",
    "_sum_largest_values",
]
