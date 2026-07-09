"""Phase 1 + Phase 2 CVXPY solver for the rebalance pipeline.

A 1:1 port of the reference algorithm's solver core
(``src/portfolio_rebalancing/domain/rebalancing.py:200-1189``), adapted
to the omaha ``PortfolioSetup`` shape — the bridge output already
de-duplicates cross-class collisions and the omaha position's
``category_name`` plays the role of the reference's
``broker_category``.

The solver entry point :func:`simulate_rebalance` matches the reference
signature exactly:

    simulate_rebalance(setup, position, contribution, market_price_lookup=None) -> RebalancePlan

The returned :class:`RebalancePlan` matches the reference's native
shape:

* ``asset_plan`` — :class:`pandas.DataFrame`, 31 columns, one row per
  asset in ``setup``. The v1 wire format consumes a 9-field subset;
  the remaining 22 are exposed for future wire-format expansion
  (spec §"Output shape").
* ``category_plan`` — :class:`pandas.DataFrame`, 13 columns, one row
  per category in ``setup``.
* ``metrics`` — ``dict[str, Any]`` with ~28 keys (see spec §"Output
  shape" and reference section 8).
* ``warnings`` — ``tuple[str, ...]`` of PT-BR text messages.

The :mod:`omaha.rebalance.engine` module exposes a glue-callable
wrapper (:func:`omaha.rebalance.engine.cvxpy_solver`) that adapts this
native shape to the dataclass-list shape the existing glue expects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cvxpy as cp
import numpy as np
import pandas as pd

from omaha.rebalance.constants import (
    ALLOCATION_TOLERANCE,
    DISPLAY_TOLERANCE,
    MIN_BUY_AMOUNT,
    MIN_SELL_AMOUNT,
    PRIORITIZED_ASSET_GAP_COUNT,
    PRIORITIZED_CATEGORY_GAP_COUNT,
    SHORTFALL_RELATIVE_FLOOR_VALUE,
    TARGET_VALUE_NEUTRAL_TOLERANCE,
)
from omaha.rebalance.market_prices import (
    QUOTE_STATUS_UNAVAILABLE,
    MarketPriceLookup,
    NoopMarketPriceLookup,
)
from omaha.rebalance.models import PortfolioSetup
from omaha.rebalance.postprocessing import _build_rebalance_plan
from omaha.rebalance.validation import _validate_rebalance_inputs


@dataclass(frozen=True)
class RebalancePlan:
    """Native solver output shape — matches the reference's dataclass exactly."""

    asset_plan: pd.DataFrame
    category_plan: pd.DataFrame
    metrics: dict[str, Any]
    warnings: tuple[str, ...]


def simulate_rebalance(
    setup: PortfolioSetup,
    position: pd.DataFrame,
    contribution: float,
    market_price_lookup: MarketPriceLookup | None = None,
    *,
    min_deviation_value: float = 1000.0,
    min_deviation_pct: float = 1.0,
) -> RebalancePlan:
    """Drive validate → aggregate → simulate → cascade → assemble.

    Mirrors ``simulate_rebalance`` from the reference algorithm. The
    contract is: input (setup, position, contribution) plus an optional
    MarketPriceLookup; output ``RebalancePlan`` with the reference's
    native 31/13/metrics/warnings shape.

    Side effect: ``rebalance_policy`` and ``sales_fallback_reason`` are
    written into the returned plan's ``metrics`` dict (per reference
    convention; the v1 wire format surfaces ``applied_policy`` as a
    top-level field, which the glue derives from ``metrics``).
    """
    contribution_value = float(contribution)
    quote_lookup = market_price_lookup or NoopMarketPriceLookup()
    _validate_rebalance_inputs(setup=setup, position=position, contribution=contribution_value)

    aggregated_position = _aggregate_position(position)
    simulation_frame = _build_simulation_frame(setup=setup, position=aggregated_position)
    # Deferred import: avoids solver ↔ policy cycle. Policy functions
    # depend on ``_build_intra_category_model`` / ``_solve_category_phase1`` /
    # ``_build_optimizer_parameters``, all defined in this module.
    from omaha.rebalance.policy import _solve_hierarchical_policy

    solution = _solve_hierarchical_policy(
        simulation_frame=simulation_frame,
        categories=setup.categories,
        contribution=contribution_value,
    )
    return _build_rebalance_plan(
        simulation_frame=simulation_frame,
        categories=setup.categories,
        contribution=contribution_value,
        solution=solution,
        market_price_lookup=quote_lookup,
        min_deviation_value=min_deviation_value,
        min_deviation_pct=min_deviation_pct,
    )


def _aggregate_position(position: pd.DataFrame) -> pd.DataFrame:
    """Roll up multiple ``Position`` rows per ``asset_key``.

    Mirror of the reference's same-named helper
    (``rebalancing.py:200-231``) — sums ``quantity``,
    ``invested_value``, ``current_value`` per ``asset_key``, keeps
    ``asset_name`` / category fields via ``first``. ``current_weight``
    is recomputed from the aggregated total so downstream checks read
    the same number the solver uses.

    Omaha's position already arrives aggregated by
    :func:`omaha.rebalance.builders.build_position_frame`; this is a
    defensive re-aggregation that handles test fixtures that pass raw
    rows (one Position per ``broker_ticker``) and any external caller
    that imports the reference shape.
    """
    if position.empty:
        return position.copy()

    aggregate_map: dict[str, str] = {
        "asset_name": "first",
        "category_name": "first",
        "category_key": "first",
        "quantity": "sum",
        "invested_value": "sum",
        "current_value": "sum",
    }
    available_columns = {
        column: rule for column, rule in aggregate_map.items() if column in position.columns
    }
    aggregated = (
        position.groupby("asset_key", as_index=False, dropna=False)
        .agg(available_columns)
        .sort_values("asset_name")
        .reset_index(drop=True)
    )
    total = float(aggregated["current_value"].fillna(0.0).sum())
    if total > 0:
        aggregated["current_weight"] = aggregated["current_value"].fillna(0.0) / total
    else:
        aggregated["current_weight"] = 0.0
    return aggregated


def _build_simulation_frame(
    setup: PortfolioSetup,
    position: pd.DataFrame,
) -> pd.DataFrame:
    """Outer-join setup.assets with position on ``asset_key``.

    One row per asset in ``setup``. Fills missing
    ``current_value`` / ``quantity`` / ``invested_value`` with ``0``.
    Sorts by ``(asset_order, asset_name)``. Computes
    ``current_weight``. Casts ``buy_enabled`` / ``sell_enabled`` to
    ``bool`` so the LP hard locks behave.

    The reference uses ``suffixes=("_target", "_current")`` to
    disambiguate the ``asset_name`` column when both sides of the
    merge carry it. Omaha's position also carries
    ``category_name`` / ``category_key`` — same values as setup, but
    dropping them keeps the merged frame's column layout identical
    to the reference, so the downstream LP and post-processing code
    can read ``simulation_frame["category_key"]`` directly.
    """
    position_columns = [
        column
        for column in (
            "asset_key",
            "asset_name",
            "quantity",
            "invested_value",
            "current_value",
        )
        if column in position.columns
    ]
    simulation_frame = setup.assets.merge(
        position[position_columns],
        how="left",
        on="asset_key",
        suffixes=("_target", "_current"),
    )
    simulation_frame["position_asset_name"] = simulation_frame["asset_name_current"].fillna("")
    simulation_frame["current_value"] = simulation_frame["current_value"].fillna(0.0)
    simulation_frame["quantity"] = simulation_frame["quantity"].fillna(0.0)
    simulation_frame["invested_value"] = simulation_frame["invested_value"].fillna(0.0)

    total_current_value = float(simulation_frame["current_value"].sum())
    if total_current_value > 0:
        simulation_frame["current_weight"] = simulation_frame["current_value"] / total_current_value
    else:
        simulation_frame["current_weight"] = 0.0

    simulation_frame["buy_enabled"] = simulation_frame["buy_enabled"].astype(bool)
    simulation_frame["sell_enabled"] = simulation_frame["sell_enabled"].astype(bool)
    return simulation_frame.sort_values(["asset_order", "asset_name_target"]).reset_index(drop=True)


def _compute_category_buy_capacity(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    total_final_value: float,
) -> np.ndarray:
    """Max buy capacity per category — sum of `(target_value - current_value).clip(0) * buy_en`.

    Port of ``rebalancing.py:293-311``.
    """
    category_frame = categories.sort_values("category_order").reset_index(drop=True)
    target_values = simulation_frame["target_weight"].to_numpy(dtype=float) * total_final_value
    current_values = simulation_frame["current_value"].to_numpy(dtype=float)
    buy_enabled = simulation_frame["buy_enabled"].to_numpy(dtype=bool)
    gap = np.maximum(target_values - current_values, 0.0) * buy_enabled.astype(float)
    capacity = np.zeros(len(category_frame), dtype=float)
    for ci, category_key in enumerate(category_frame["category_key"]):
        mask = simulation_frame["category_key"].eq(category_key).to_numpy(dtype=bool)
        capacity[ci] = float(gap[mask].sum())
    return capacity


def _compute_category_sell_capacity(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
) -> np.ndarray:
    """Max sell capacity per category — sum of `current_value * sell_en`.

    Port of ``rebalancing.py:314-327``.
    """
    category_frame = categories.sort_values("category_order").reset_index(drop=True)
    current_values = simulation_frame["current_value"].to_numpy(dtype=float)
    sell_enabled = simulation_frame["sell_enabled"].to_numpy(dtype=bool)
    eligible = current_values * sell_enabled.astype(float)
    capacity = np.zeros(len(category_frame), dtype=float)
    for ci, category_key in enumerate(category_frame["category_key"]):
        mask = simulation_frame["category_key"].eq(category_key).to_numpy(dtype=bool)
        capacity[ci] = float(eligible[mask].sum())
    return capacity


def _build_category_phase1_model(
    category_frame: pd.DataFrame,
    current_category_values: np.ndarray,
    contribution: float,
    max_buy_capacity: np.ndarray,
    max_sell_capacity: np.ndarray,
    *,
    allowed_sell_mask: np.ndarray,
) -> dict[str, Any]:
    """Build the Phase 1 CVXPY model that decides ``delta_c`` per category.

    Port of ``rebalancing.py:330-406``. Includes the RBRX11 B.2 fix:
    categories whose current value is already below their target value
    (``current_category_values[c] < target_category_values[c] -
    DISPLAY_TOLERANCE``) force ``delta[c] >= 0`` regardless of internal
    overweights — Phase 2 handles intra-category reallocation
    separately.

    ``allowed_sell_mask`` is a per-category boolean: ``True`` means
    sells are allowed for that category (used to gate OVERWEIGHT_SALES
    and FULL_SALES policies). A category whose ``allowed_sell_mask``
    is ``False`` is forced non-negative by the constraint loop below
    even if it is overweight.
    """
    n_categories = len(category_frame)
    delta = cp.Variable(n_categories)
    residual_cash = cp.Variable(nonneg=True)

    target_weights = category_frame["target_weight"].to_numpy(dtype=float)
    total_current_value = float(current_category_values.sum())
    total_final_value = total_current_value + contribution

    projected_category_values = current_category_values + delta
    projected_category_weights = projected_category_values / max(
        total_final_value, ALLOCATION_TOLERANCE
    )
    deviation = cp.Variable(n_categories, nonneg=True)

    constraints: list[cp.constraints.Constraint] = [
        deviation >= projected_category_weights - target_weights,
        deviation >= -(projected_category_weights - target_weights),
        cp.sum(delta) + residual_cash == contribution,
        delta <= max_buy_capacity,
        projected_category_values >= 0,
    ]

    target_category_values = target_weights * total_final_value

    for ci in range(n_categories):
        category_is_underweight = (
            current_category_values[ci] < target_category_values[ci] - DISPLAY_TOLERANCE
        )
        if not bool(allowed_sell_mask[ci]) or category_is_underweight:
            constraints.append(delta[ci] >= 0)
        else:
            constraints.append(delta[ci] >= -max_sell_capacity[ci])

    objective = cp.Minimize(cp.sum(deviation) + ALLOCATION_TOLERANCE * residual_cash)
    return {
        "delta": delta,
        "residual_cash": residual_cash,
        "constraints": constraints,
        "objective": objective,
        "projected_category_weights_expr": projected_category_weights,
        "total_final_value": total_final_value,
    }


def _solve_category_phase1(model: dict[str, Any]) -> np.ndarray:
    """Solve the Phase 1 LP; return ``delta_c`` values.

    Raises :class:`RuntimeError` if the solver does not return
    OPTIMAL / OPTIMAL_INACCURATE after the CLARABEL → SCS fallback.
    Port of ``rebalancing.py:409-418``.
    """
    problem = cp.Problem(model["objective"], model["constraints"])
    _run_problem(problem)
    if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
        raise RuntimeError(
            f"Fase 1 falhou ao resolver a alocacao por categoria; status: {problem.status}."
        )
    return np.asarray(model["delta"].value, dtype=float).reshape(-1)


def _build_intra_category_model(
    category_assets: pd.DataFrame,
    current_values: np.ndarray,
    target_values: np.ndarray,
    delta_c: float,
    projected_category_total: float,
    *,
    allowed_sell_mask: np.ndarray,
) -> dict[str, Any]:
    """Build the Phase 2 CVXPY model for a single category.

    Distributes ``delta_c`` between the category's assets to minimise
    weighted-least-squares deviation from
    ``target_weight_in_category``, enforcing the buy/sell hard locks
    from the setup and the RBRX11 B.1 fix (assets at or below their
    portfolio-level target value cannot be sold when ``delta_c >= 0``).

    Port of ``rebalancing.py:421-491``.
    """
    n = len(category_assets)
    buy = cp.Variable(n, nonneg=True)
    sell = cp.Variable(n, nonneg=True)
    projected = current_values + buy - sell

    target_weights_in_cat = category_assets["target_weight_in_category"].to_numpy(dtype=float)
    buy_enabled = category_assets["buy_enabled"].to_numpy(dtype=bool)
    sell_enabled_array = category_assets["sell_enabled"].to_numpy(dtype=bool)
    effective_sell = sell_enabled_array & allowed_sell_mask.astype(bool)

    # RBRX11 B.1 fix.
    at_or_below_target = (current_values <= target_values + DISPLAY_TOLERANCE) & (delta_c >= 0)

    safe_cat_total = max(projected_category_total, ALLOCATION_TOLERANCE)
    projected_weights_in_cat = projected / safe_cat_total

    deviation = cp.Variable(n, nonneg=True)
    constraints: list[cp.constraints.Constraint] = [
        cp.sum(buy) - cp.sum(sell) == delta_c,
        projected >= 0,
        deviation >= projected_weights_in_cat - target_weights_in_cat,
        deviation >= -(projected_weights_in_cat - target_weights_in_cat),
    ]

    for i in range(n):
        if not buy_enabled[i]:
            constraints.append(buy[i] == 0)
        if not effective_sell[i] or at_or_below_target[i]:
            constraints.append(sell[i] == 0)

    objective = cp.Minimize(cp.sum(deviation))
    return {
        "buy": buy,
        "sell": sell,
        "projected": projected,
        "constraints": constraints,
        "objective": objective,
        "n": n,
    }


def _solve_intra_category(model: dict[str, Any]) -> dict[str, Any]:
    """Solve the Phase 2 LP for one category with min-trade enforcement loop.

    Iteratively re-solves the LP with extra ``buy[i] == 0`` /
    ``sell[i] == 0`` constraints for trades that landed below
    ``MIN_BUY_AMOUNT`` / ``MIN_SELL_AMOUNT``. Stops when no new
    trade-below-minimum constraint can be added.

    Returns the last feasible solution if the LP becomes infeasible
    mid-iteration; raises :class:`RuntimeError` if no solution is
    ever found. Port of ``rebalancing.py:494-567``.
    """
    buy_floor_constraints: list[cp.constraints.Constraint] = []
    buy_floor_locked: set[int] = set()
    sell_floor_constraints: list[cp.constraints.Constraint] = []
    sell_floor_locked: set[int] = set()
    last_feasible: dict[str, Any] | None = None
    last_feasible_floors: list[cp.constraints.Constraint] = []

    base_constraints = list(model["constraints"])

    while True:
        problem = cp.Problem(
            model["objective"],
            [*base_constraints, *buy_floor_constraints, *sell_floor_constraints],
        )
        _run_problem(problem)

        if problem.status not in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
            if last_feasible is not None:
                restore = cp.Problem(
                    model["objective"],
                    [*base_constraints, *last_feasible_floors],
                )
                _run_problem(restore)
                return last_feasible
            raise RuntimeError(
                f"Fase 2 falhou ao resolver alocacao intra-categoria; status: {problem.status}."
            )

        buy_vals = _clip_solution(model["buy"].value)
        sell_vals = _clip_solution(model["sell"].value)
        current_solution = {
            "buy_amounts": buy_vals,
            "sell_amounts": sell_vals,
            "solver_status": str(problem.status),
        }
        last_feasible = current_solution
        last_feasible_floors = [*buy_floor_constraints, *sell_floor_constraints]

        new_constraint_added = False
        if MIN_BUY_AMOUNT > DISPLAY_TOLERANCE:
            small_buy = np.flatnonzero(
                (buy_vals > DISPLAY_TOLERANCE) & (buy_vals < MIN_BUY_AMOUNT - DISPLAY_TOLERANCE)
            )
            for idx in small_buy.tolist():
                if idx not in buy_floor_locked:
                    buy_floor_constraints.append(model["buy"][idx] == 0)
                    buy_floor_locked.add(idx)
                    new_constraint_added = True

        if MIN_SELL_AMOUNT > DISPLAY_TOLERANCE:
            small_sell = np.flatnonzero(
                (sell_vals > DISPLAY_TOLERANCE) & (sell_vals < MIN_SELL_AMOUNT - DISPLAY_TOLERANCE)
            )
            for idx in small_sell.tolist():
                if idx not in sell_floor_locked:
                    sell_floor_constraints.append(model["sell"][idx] == 0)
                    sell_floor_locked.add(idx)
                    new_constraint_added = True

        if not new_constraint_added:
            break

    if last_feasible is None:
        raise RuntimeError("Fase 2 nao retornou solucao numerica utilizavel.")
    return last_feasible


def _build_optimizer_parameters() -> dict[str, Any]:
    """Snapshot of every constant that influences the LP output.

    Port of ``rebalancing.py:847-874``. Surfaced as
    ``metrics['optimizer_parameters']`` so an operator reading the
    plan can confirm the tolerances used in this run.
    """
    return {
        "min_buy_amount": MIN_BUY_AMOUNT,
        "min_sell_amount": MIN_SELL_AMOUNT,
        "allocation_tolerance": ALLOCATION_TOLERANCE,
        "display_tolerance": DISPLAY_TOLERANCE,
        "lot_size": None,
        "requires_integer_quantities": False,
        "buy_locks_enabled": True,
        "sell_locks_enabled": True,
        "target_value_neutral_tolerance": TARGET_VALUE_NEUTRAL_TOLERANCE,
        "shortfall_relative_floor_value": SHORTFALL_RELATIVE_FLOOR_VALUE,
        "prioritized_asset_gap_count": PRIORITIZED_ASSET_GAP_COUNT,
        "prioritized_category_gap_count": PRIORITIZED_CATEGORY_GAP_COUNT,
    }


def _run_problem(problem: cp.Problem) -> tuple[str | None, Exception | None]:
    """Solve a CVXPY problem with CLARABEL → SCS fallback.

    Tries CLARABEL first, then SCS with ``eps=1e-8``. Returns
    ``(solver_status, last_exception)``. The status string is one of
    ``"optimal"`` / ``"optimal_inaccurate"`` / the CLARABEL/SCS status
    string on failure. Port of ``rebalancing.py:877-892``.
    """
    solver_status: str | None = None
    last_error: Exception | None = None
    for solver in (cp.CLARABEL, cp.SCS):
        try:
            if solver == cp.SCS:
                problem.solve(solver=solver, verbose=False, eps=1e-8)
            else:
                problem.solve(solver=solver, verbose=False)
        except Exception as exc:  # defensive fallback
            last_error = exc
            continue
        solver_status = str(problem.status)
        if problem.status in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
            break
    return solver_status, last_error


def _expression_value(expression: Any) -> float:
    """Safe-cast a CVXPY expression to a scalar float.

    Handles the ``np.ndarray`` of shape ``()`` that CVXPY returns when
    you ``.value`` an expression. Port of
    ``rebalancing.py:895-901``.
    """
    value = expression.value
    if value is None:
        raise RuntimeError("Nao foi possivel avaliar a expressao do solver apos a otimizacao.")
    return float(np.asarray(value).reshape(-1)[0])


def _clip_solution(values: np.ndarray | None) -> np.ndarray:
    """Clip a CVXPY solution to ``>= 0`` (negatives are LP dust)."""
    if values is None:
        raise RuntimeError("O solver nao retornou uma solucao numerica.")
    clipped = np.maximum(np.asarray(values, dtype=float).reshape(-1), 0.0)
    clipped[np.abs(clipped) < DISPLAY_TOLERANCE] = 0.0
    return clipped


__all__ = [
    "RebalancePlan",
    "simulate_rebalance",
    "_aggregate_position",
    "_build_simulation_frame",
    "_build_category_phase1_model",
    "_build_intra_category_model",
    "_build_optimizer_parameters",
    "_clip_solution",
    "_compute_category_buy_capacity",
    "_compute_category_sell_capacity",
    "_expression_value",
    "_run_problem",
    "_solve_category_phase1",
    "_solve_intra_category",
]


_ = QUOTE_STATUS_UNAVAILABLE  # imported for the post-processing module's enrichment
