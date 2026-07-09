"""Post-processing pipeline for the rebalance solver.

Ports the ``_build_rebalance_plan`` family from
``rebalancing.py:1193-1688`` — 31-column ``asset_plan``,
13-column ``category_plan``, the 28-key ``metrics`` dict, and the
PT-BR ``warnings`` tuple.

The pipeline applies, in order:

1. :func:`_clamp_projected_values_to_target_side` — keep projected
   values from crossing their target in the wrong direction.
2. Derive ``buy_amount`` / ``sell_amount`` from
   ``projected - current``.
3. :func:`_reduce_buy_overspend` — absorb excess buys when ``sum(buy)
   > contribution + sum(sell)``.
4. Zero trades under ``MIN_BUY_AMOUNT`` / ``MIN_SELL_AMOUNT``.
5. :func:`_reduce_buy_overspend` again (round 2).
6. Final clip of dust below ``DISPLAY_TOLERANCE``.
7. Recompute ``residual_cash``.
8. Build the 31-column ``asset_plan`` via column projection.
9. :func:`_enrich_asset_plan_with_market_data` — left-join quotes and
   compute ``buy_amount_usd`` / ``estimated_buy_quantity``.
10. :func:`_build_restriction_note` per row.
11. Project the 31 final columns.
12. :func:`_build_category_plan` — 13-column per-category roll-up.
13. :func:`_build_plan_warnings` — merge solver warnings with the
    constraint / quote messages.
14. :func:`_build_plan_metrics` — final 28-key dict.
"""

from __future__ import annotations

from typing import Any

import cvxpy as cp
import numpy as np
import pandas as pd

from omaha.rebalance.constants import (
    ALLOCATION_TOLERANCE,
    CONTRIBUTION_ONLY_POLICY,
    DISPLAY_TOLERANCE,
    FULL_SALES_POLICY,
    MIN_BUY_AMOUNT,
    MIN_SELL_AMOUNT,
    OVERWEIGHT_SALES_POLICY,
    PRIORITIZED_ASSET_GAP_COUNT,
    PRIORITIZED_CATEGORY_GAP_COUNT,
    SHORTFALL_RELATIVE_FLOOR_VALUE,
    TARGET_VALUE_NEUTRAL_TOLERANCE,
)
from omaha.rebalance.market_prices import (
    QUOTE_STATUS_UNAVAILABLE,
    MarketPriceLookup,
)


def _build_rebalance_plan(
    simulation_frame: pd.DataFrame,
    categories: pd.DataFrame,
    contribution: float,
    solution: dict[str, Any],
    market_price_lookup: MarketPriceLookup,
    *,
    min_deviation_value: float = 1000.0,
    min_deviation_pct: float = 1.0,
) -> Any:
    """Top-level plan builder — returns a :class:`solver.RebalancePlan`.

    Port of ``rebalancing.py:1193-1349``. Defers the dataclass import to
    runtime to avoid the ``solver.py`` import cycle.
    """
    from omaha.rebalance.solver import RebalancePlan

    total_current_value = float(simulation_frame["current_value"].sum())
    total_final_value = total_current_value + contribution
    current_values = simulation_frame["current_value"].to_numpy(dtype=float)
    target_values = simulation_frame["target_weight"].to_numpy(dtype=float) * total_final_value
    projected_values = _clamp_projected_values_to_target_side(
        current_values=current_values,
        projected_values=np.asarray(solution["projected_values"], dtype=float),
        target_values=target_values,
    )
    net_trade = projected_values - current_values
    buy_amounts = np.maximum(net_trade, 0.0)
    sell_amounts = np.maximum(-net_trade, 0.0)
    buy_amounts = _reduce_buy_overspend(
        buy_amounts=buy_amounts,
        sell_amounts=sell_amounts,
        contribution=contribution,
    )
    small_buy_mask = (buy_amounts > DISPLAY_TOLERANCE) & (buy_amounts < MIN_BUY_AMOUNT)
    small_sell_mask = (sell_amounts > DISPLAY_TOLERANCE) & (sell_amounts < MIN_SELL_AMOUNT)
    buy_amounts[small_buy_mask] = 0.0
    sell_amounts[small_sell_mask] = 0.0
    buy_amounts = _reduce_buy_overspend(
        buy_amounts=buy_amounts,
        sell_amounts=sell_amounts,
        contribution=contribution,
    )
    projected_values = current_values + buy_amounts - sell_amounts
    buy_amounts, sell_amounts = _suppress_subthreshold_trades(
        current_values=current_values,
        target_values=target_values,
        buy_amounts=buy_amounts,
        sell_amounts=sell_amounts,
        min_deviation_value=min_deviation_value,
        min_deviation_pct=min_deviation_pct,
    )
    projected_values = current_values + buy_amounts - sell_amounts
    buy_amounts[np.abs(buy_amounts) < DISPLAY_TOLERANCE] = 0.0
    sell_amounts[np.abs(sell_amounts) < DISPLAY_TOLERANCE] = 0.0
    residual_cash = max(
        contribution + float(sell_amounts.sum()) - float(buy_amounts.sum()),
        0.0,
    )

    asset_plan = simulation_frame.copy()
    asset_plan["asset_name"] = asset_plan["asset_name_target"]
    asset_plan["target_value"] = target_values
    asset_plan["buy_amount"] = buy_amounts
    asset_plan["sell_amount"] = sell_amounts
    asset_plan["trade_amount"] = asset_plan["buy_amount"] - asset_plan["sell_amount"]
    asset_plan["projected_value"] = projected_values
    asset_plan["projected_weight"] = projected_values / total_final_value
    asset_plan["current_gap_weight"] = asset_plan["current_weight"] - asset_plan["target_weight"]
    asset_plan["projected_gap_weight"] = (
        asset_plan["projected_weight"] - asset_plan["target_weight"]
    )
    asset_plan["current_shortfall_value"] = np.maximum(
        asset_plan["target_value"] - asset_plan["current_value"],
        0.0,
    )
    asset_plan["projected_shortfall_value"] = np.maximum(
        asset_plan["target_value"] - asset_plan["projected_value"],
        0.0,
    )
    asset_plan["rebalance_policy"] = str(solution.get("rebalance_policy", ""))
    asset_relative_floor = np.maximum(
        asset_plan["target_value"].to_numpy(dtype=float),
        SHORTFALL_RELATIVE_FLOOR_VALUE,
    )
    asset_plan["current_relative_shortfall"] = (
        asset_plan["current_shortfall_value"] / asset_relative_floor
    )
    asset_plan["projected_relative_shortfall"] = (
        asset_plan["projected_shortfall_value"] / asset_relative_floor
    )
    asset_plan["action"] = np.where(
        asset_plan["buy_amount"] > DISPLAY_TOLERANCE,
        "comprar",
        np.where(asset_plan["sell_amount"] > DISPLAY_TOLERANCE, "vender", "manter"),
    )
    asset_plan = _enrich_asset_plan_with_market_data(
        asset_plan=asset_plan,
        market_price_lookup=market_price_lookup,
    )
    asset_plan["restriction_note"] = asset_plan.apply(_build_restriction_note, axis=1)
    asset_plan = asset_plan[
        [
            "asset_key",
            "asset_name",
            "category_name",
            "currency_code",
            "buy_enabled",
            "sell_enabled",
            "current_value",
            "current_weight",
            "target_weight",
            "target_value",
            "buy_amount",
            "sell_amount",
            "trade_amount",
            "projected_value",
            "projected_weight",
            "current_gap_weight",
            "projected_gap_weight",
            "current_shortfall_value",
            "projected_shortfall_value",
            "current_relative_shortfall",
            "projected_relative_shortfall",
            "quote_symbol",
            "quote_price",
            "quote_currency",
            "quote_timestamp",
            "quote_status",
            "usdbrl_rate",
            "buy_amount_usd",
            "estimated_buy_quantity",
            "action",
            "restriction_note",
        ]
    ]

    category_plan = _build_category_plan(
        asset_plan=asset_plan,
        categories=categories,
        total_current_value=total_current_value,
        total_final_value=total_final_value,
    )
    warnings = _build_plan_warnings(
        asset_plan=asset_plan,
        residual_cash=residual_cash,
        solver_status=str(solution["solver_status"]),
        rebalance_policy=str(solution.get("rebalance_policy", "")),
        sales_fallback_reason=str(solution.get("sales_fallback_reason", "")),
    )
    metrics = _build_plan_metrics(
        asset_plan=asset_plan,
        category_plan=category_plan,
        total_current_value=total_current_value,
        contribution=contribution,
        total_final_value=total_final_value,
        residual_cash=residual_cash,
        objective_value=float(solution["objective_value"]),
        solver_status=str(solution["solver_status"]),
        rebalance_policy=str(solution.get("rebalance_policy", "")),
        sales_fallback_reason=str(solution.get("sales_fallback_reason", "")),
        optimizer_parameters=dict(solution.get("optimizer_parameters", {})),
        stage_values=dict(solution.get("stage_values", {})),
    )
    return RebalancePlan(
        asset_plan=asset_plan,
        category_plan=category_plan,
        metrics=metrics,
        warnings=tuple(warnings),
    )


def _build_category_plan(
    asset_plan: pd.DataFrame,
    categories: pd.DataFrame,
    total_current_value: float,
    total_final_value: float,
) -> pd.DataFrame:
    """13-column per-category rollup.

    Port of ``rebalancing.py:1352-1424``.
    """
    aggregated = asset_plan.groupby("category_name", as_index=False)[
        [
            "current_value",
            "projected_value",
            "current_shortfall_value",
            "projected_shortfall_value",
        ]
    ].sum()
    category_plan = categories.merge(aggregated, how="left", on="category_name")
    category_plan["current_value"] = category_plan["current_value"].fillna(0.0)
    category_plan["projected_value"] = category_plan["projected_value"].fillna(0.0)
    category_plan["current_shortfall_value"] = category_plan["current_shortfall_value"].fillna(0.0)
    category_plan["projected_shortfall_value"] = category_plan["projected_shortfall_value"].fillna(
        0.0
    )
    category_plan["current_weight"] = (
        category_plan["current_value"] / total_current_value if total_current_value else 0.0
    )
    category_plan["target_value"] = category_plan["target_weight"] * total_final_value
    category_relative_floor = np.maximum(
        category_plan["target_value"].to_numpy(dtype=float),
        SHORTFALL_RELATIVE_FLOOR_VALUE,
    )
    category_plan["projected_weight"] = (
        category_plan["projected_value"] / total_final_value if total_final_value else 0.0
    )
    category_plan["current_gap_weight"] = (
        category_plan["current_weight"] - category_plan["target_weight"]
    )
    category_plan["projected_gap_weight"] = (
        category_plan["projected_weight"] - category_plan["target_weight"]
    )
    category_plan["current_relative_shortfall"] = (
        category_plan["current_shortfall_value"] / category_relative_floor
    )
    category_plan["projected_relative_shortfall"] = (
        category_plan["projected_shortfall_value"] / category_relative_floor
    )
    return category_plan.sort_values(["category_order", "category_name"]).reset_index(drop=True)[
        [
            "category_name",
            "current_value",
            "current_weight",
            "target_weight",
            "target_value",
            "projected_value",
            "projected_weight",
            "current_gap_weight",
            "projected_gap_weight",
            "current_shortfall_value",
            "projected_shortfall_value",
            "current_relative_shortfall",
            "projected_relative_shortfall",
        ]
    ]


def _suppress_subthreshold_trades(
    *,
    current_values: np.ndarray,
    target_values: np.ndarray,
    buy_amounts: np.ndarray,
    sell_amounts: np.ndarray,
    min_deviation_value: float,
    min_deviation_pct: float,
) -> tuple[np.ndarray, np.ndarray]:
    adjusted_buys = np.asarray(buy_amounts, dtype=float).copy()
    adjusted_sells = np.asarray(sell_amounts, dtype=float).copy()
    target_values_array = np.asarray(target_values, dtype=float)
    actionable = (adjusted_buys > DISPLAY_TOLERANCE) | (adjusted_sells > DISPLAY_TOLERANCE)
    deviation_value = np.abs(np.asarray(current_values, dtype=float) - target_values_array)
    deviation_pct = np.divide(
        deviation_value * 100.0,
        target_values_array,
        out=np.zeros_like(deviation_value, dtype=float),
        where=target_values_array > 0.0,
    )
    below_threshold = (deviation_value < float(min_deviation_value)) | (
        deviation_pct < float(min_deviation_pct)
    )
    suppress = actionable & below_threshold
    adjusted_buys[suppress] = 0.0
    adjusted_sells[suppress] = 0.0
    return adjusted_buys, adjusted_sells


def _clamp_projected_values_to_target_side(
    *,
    current_values: np.ndarray,
    projected_values: np.ndarray,
    target_values: np.ndarray,
) -> np.ndarray:
    """Forbid ``projected`` from crossing ``target`` in the wrong direction.

    If an asset is currently underweight (current < target - tolerance),
    ``projected`` cannot exceed ``target``. If currently overweight
    (current > target + tolerance), ``projected`` cannot drop below
    ``target``. Port of ``rebalancing.py:1427-1442``.
    """
    clamped = np.asarray(projected_values, dtype=float).copy()
    underweight_mask = current_values < (target_values - TARGET_VALUE_NEUTRAL_TOLERANCE)
    overweight_mask = current_values > (target_values + TARGET_VALUE_NEUTRAL_TOLERANCE)
    clamped[underweight_mask] = np.minimum(
        clamped[underweight_mask], target_values[underweight_mask]
    )
    clamped[overweight_mask] = np.maximum(clamped[overweight_mask], target_values[overweight_mask])
    return clamped


def _reduce_buy_overspend(
    *,
    buy_amounts: np.ndarray,
    sell_amounts: np.ndarray,
    contribution: float,
) -> np.ndarray:
    """Reduce buys so ``sum(buy) <= contribution + sum(sell)``.

    Walk the positive buys in reverse order and decrement each until
    the overspend is absorbed. Port of ``rebalancing.py:1445-1466``.
    """
    adjusted = np.asarray(buy_amounts, dtype=float).copy()
    overspend = float(adjusted.sum()) - (
        contribution + float(np.asarray(sell_amounts, dtype=float).sum())
    )
    if overspend <= DISPLAY_TOLERANCE:
        return adjusted

    positive_buy_indices = np.flatnonzero(adjusted > DISPLAY_TOLERANCE)
    for index in positive_buy_indices[::-1]:
        reducible_amount = min(adjusted[index], overspend)
        adjusted[index] -= reducible_amount
        overspend -= reducible_amount
        if overspend <= DISPLAY_TOLERANCE:
            break
    adjusted[np.abs(adjusted) < DISPLAY_TOLERANCE] = 0.0
    return adjusted


def _build_restriction_note(asset_row: pd.Series) -> str:
    """PT-BR note explaining why an asset was clamped or held.

    Ports ``rebalancing.py:1469-1488``.
    """
    projected_gap = float(asset_row["projected_gap_weight"])
    policy = str(asset_row.get("rebalance_policy", ""))
    if not asset_row["buy_enabled"] and not asset_row["sell_enabled"]:
        return "ativo travado no setup"
    if not asset_row["buy_enabled"] and projected_gap < -DISPLAY_TOLERANCE:
        return "abaixo do alvo, mas compra bloqueada"
    if not asset_row["sell_enabled"] and projected_gap > DISPLAY_TOLERANCE:
        return "acima do alvo, mas venda bloqueada"
    if (
        float(asset_row["target_weight"]) <= ALLOCATION_TOLERANCE
        and float(asset_row["current_value"]) > DISPLAY_TOLERANCE
        and float(asset_row["sell_amount"]) <= DISPLAY_TOLERANCE
        and bool(asset_row["sell_enabled"])
        and policy == CONTRIBUTION_ONLY_POLICY
    ):
        return "alvo zero mantido porque o plano evitou vendas"
    if asset_row["buy_amount"] == 0.0 and asset_row["sell_amount"] == 0.0:
        return ""
    return ""


def _enrich_asset_plan_with_market_data(
    *,
    asset_plan: pd.DataFrame,
    market_price_lookup: MarketPriceLookup,
) -> pd.DataFrame:
    """Left-join the quote frame onto ``asset_plan`` and compute derived columns.

    Ports ``rebalancing.py:1491-1551``.
    """
    quote_request = asset_plan[["asset_key", "asset_name", "currency_code"]].copy()
    quote_frame = market_price_lookup.get_quotes(quote_request)
    enriched = asset_plan.merge(quote_frame, how="left", on="asset_key")

    enriched["quote_symbol"] = enriched["quote_symbol"].fillna("")
    enriched["quote_currency"] = enriched["quote_currency"].fillna(enriched["currency_code"])
    enriched["quote_timestamp"] = enriched["quote_timestamp"].fillna("")
    enriched["quote_status"] = enriched["quote_status"].fillna("not-requested")
    enriched["quote_price"] = pd.to_numeric(enriched["quote_price"], errors="coerce")
    enriched["usdbrl_rate"] = pd.to_numeric(enriched["usdbrl_rate"], errors="coerce")

    enriched["buy_amount_usd"] = np.where(
        enriched["currency_code"].eq("USD")
        & np.isfinite(enriched["usdbrl_rate"])
        & (enriched["usdbrl_rate"] > ALLOCATION_TOLERANCE),
        enriched["buy_amount"] / enriched["usdbrl_rate"],
        np.where(enriched["currency_code"].eq("USD"), 0.0, np.nan),
    )
    has_positive_buy = enriched["buy_amount"] > DISPLAY_TOLERANCE
    has_usable_quote = (
        enriched["quote_status"].eq("available")
        & np.isfinite(enriched["quote_price"])
        & (enriched["quote_price"] > ALLOCATION_TOLERANCE)
    )

    estimated_buy_quantity = np.where(
        ~has_positive_buy,
        0.0,
        np.where(
            has_usable_quote & enriched["currency_code"].eq("USD"),
            enriched["buy_amount_usd"] / enriched["quote_price"],
            np.where(
                has_usable_quote,
                enriched["buy_amount"] / enriched["quote_price"],
                np.nan,
            ),
        ),
    )
    enriched["estimated_buy_quantity"] = estimated_buy_quantity
    unavailable = enriched["quote_status"].eq(QUOTE_STATUS_UNAVAILABLE) & has_positive_buy
    if unavailable.any():
        enriched.loc[unavailable, "buy_amount_usd"] = np.where(
            enriched.loc[unavailable, "currency_code"].eq("USD"),
            np.nan,
            enriched.loc[unavailable, "buy_amount_usd"],
        )
    return enriched


def _build_plan_warnings(
    asset_plan: pd.DataFrame,
    residual_cash: float,
    solver_status: str,
    rebalance_policy: str,
    sales_fallback_reason: str,
) -> list[str]:
    """PT-BR text warnings surfaced to the operator.

    Ports ``rebalancing.py:1554-1606``.
    """
    warnings: list[str] = []
    if rebalance_policy == CONTRIBUTION_ONLY_POLICY:
        warnings.append(
            "O plano foi resolvido apenas com novos aportes; o solver "
            "minimizou primeiro o caixa residual, depois fechou o encaixe "
            "por categoria e so entao distribuiu o ajuste entre os ativos."
        )
    elif rebalance_policy == OVERWEIGHT_SALES_POLICY:
        message = (
            "O plano precisou vender ativos acima do alvo depois que "
            "aporte puro nao foi suficiente."
        )
        if sales_fallback_reason:
            message += " Motivo para ampliar o estagio: " + sales_fallback_reason + "."
        warnings.append(message)
    elif rebalance_policy == FULL_SALES_POLICY:
        message = (
            "O plano precisou liberar vendas amplas porque os estagios "
            "mais conservadores nao entregaram melhora suficiente."
        )
        if sales_fallback_reason:
            message += " Motivo para ampliar o estagio: " + sales_fallback_reason + "."
        warnings.append(message)
    elif sales_fallback_reason:
        warnings.append(
            "Vendas foram liberadas porque o plano somente com aporte nao "
            "atingiu os criterios configurados: " + sales_fallback_reason + "."
        )
    if residual_cash > DISPLAY_TOLERANCE:
        warnings.append(
            "Parte do patrimonio final permaneceu em caixa residual porque "
            "as restricoes do problema impediram alocacao integral."
        )
    if asset_plan["restriction_note"].astype(bool).any():
        warnings.append(
            "Alguns ativos ficaram afastados do alvo por restricoes de compra ou venda."
        )
    if asset_plan["quote_status"].eq(QUOTE_STATUS_UNAVAILABLE).any():
        warnings.append(
            "Nao foi possivel consultar cotacoes em tempo real para todos "
            "os ativos; os campos de cotacao e quantidade estimada ficaram "
            "vazios onde faltou dado."
        )
    if solver_status == str(cp.OPTIMAL_INACCURATE):
        warnings.append(
            "O solver encontrou uma solucao utilizavel, mas com precisao numerica reduzida."
        )
    return warnings


def _build_plan_metrics(
    asset_plan: pd.DataFrame,
    category_plan: pd.DataFrame,
    total_current_value: float,
    contribution: float,
    total_final_value: float,
    residual_cash: float,
    objective_value: float,
    solver_status: str,
    rebalance_policy: str,
    sales_fallback_reason: str,
    optimizer_parameters: dict[str, Any],
    stage_values: dict[str, float],
) -> dict[str, Any]:
    """Final 28-key metrics dict surfaced to the dashboard / tests.

    Ports ``rebalancing.py:1609-1688``. Note: the v1 wire format only
    consumes 6 of these keys; the rest are exposed for future
    expansion.
    """
    current_asset_deviation = float(np.abs(asset_plan["current_gap_weight"]).sum())
    projected_asset_deviation = float(np.abs(asset_plan["projected_gap_weight"]).sum())
    current_category_deviation = float(np.abs(category_plan["current_gap_weight"]).sum())
    projected_category_deviation = float(np.abs(category_plan["projected_gap_weight"]).sum())

    def _sum_top(values: np.ndarray, count: int) -> float:
        if values.size == 0 or count <= 0:
            return 0.0
        return float(
            np.sort(np.asarray(values, dtype=float))[::-1][: min(count, values.size)].sum()
        )

    current_top_asset_gap = _sum_top(
        asset_plan["current_relative_shortfall"].to_numpy(dtype=float),
        PRIORITIZED_ASSET_GAP_COUNT,
    )
    projected_top_asset_gap = _sum_top(
        asset_plan["projected_relative_shortfall"].to_numpy(dtype=float),
        PRIORITIZED_ASSET_GAP_COUNT,
    )
    current_top_category_gap = _sum_top(
        category_plan["current_relative_shortfall"].to_numpy(dtype=float),
        PRIORITIZED_CATEGORY_GAP_COUNT,
    )
    projected_top_category_gap = _sum_top(
        category_plan["projected_relative_shortfall"].to_numpy(dtype=float),
        PRIORITIZED_CATEGORY_GAP_COUNT,
    )

    return {
        "total_current_value": total_current_value,
        "contribution": contribution,
        "total_final_value": total_final_value,
        "total_invested_after_rebalance": float(asset_plan["projected_value"].sum()),
        "residual_cash": residual_cash,
        "residual_cash_share": residual_cash / total_final_value if total_final_value else 0.0,
        "total_buy_amount": float(asset_plan["buy_amount"].sum()),
        "total_sell_amount": float(asset_plan["sell_amount"].sum()),
        "trade_count": int(
            (
                (asset_plan["buy_amount"] > DISPLAY_TOLERANCE)
                | (asset_plan["sell_amount"] > DISPLAY_TOLERANCE)
            ).sum()
        ),
        "current_asset_deviation": current_asset_deviation,
        "projected_asset_deviation": projected_asset_deviation,
        "current_category_deviation": current_category_deviation,
        "projected_category_deviation": projected_category_deviation,
        "current_top_asset_gap": current_top_asset_gap,
        "projected_top_asset_gap": projected_top_asset_gap,
        "current_top_category_gap": current_top_category_gap,
        "projected_top_category_gap": projected_top_category_gap,
        "restriction_count": int(asset_plan["restriction_note"].astype(bool).sum()),
        "solver_status": solver_status,
        "objective_value": objective_value,
        "stage_values": stage_values,
        "optimizer_parameters": optimizer_parameters,
        "rebalance_policy": rebalance_policy,
        "sales_fallback_reason": sales_fallback_reason,
        "improves_asset_deviation": projected_asset_deviation <= current_asset_deviation,
        "improves_category_deviation": (projected_category_deviation <= current_category_deviation),
        "improves_top_asset_gap": projected_top_asset_gap <= current_top_asset_gap,
        "improves_top_category_gap": projected_top_category_gap <= current_top_category_gap,
    }


__all__ = [
    "_build_category_plan",
    "_build_plan_metrics",
    "_build_plan_warnings",
    "_build_rebalance_plan",
    "_build_restriction_note",
    "_clamp_projected_values_to_target_side",
    "_enrich_asset_plan_with_market_data",
    "_reduce_buy_overspend",
    "_suppress_subthreshold_trades",
]
