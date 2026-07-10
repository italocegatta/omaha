"""Glue-compatible shim around :func:`omaha.rebalance.solver.simulate_rebalance`.

The native solver returns a :class:`solver.RebalancePlan` with
``asset_plan`` / ``category_plan`` as :class:`pandas.DataFrame` (the
reference algorithm's shape — 31 columns / 13 columns respectively).

The omaha glue (:func:`omaha.rebalance.glue.run_rebalance`) was built
against the v1 stub's dataclass-list shape: each ``asset_plan`` entry
is a :class:`RebalanceAssetPlanRowNative` with ``.name``,
``.category_name``, ``.current_value``, etc. — not a DataFrame row.

This module wraps :func:`simulate_rebalance` and translates the
DataFrame output into the dataclass-list ``RebalancePlan`` that the
glue expects. The translation is mechanical: copy the v1 wire-format
subset of the 31 / 13 columns and surface the warnings / metrics
through the native dataclasses.

Internal — not exported from ``omaha.rebalance.__init__`` because
``cvxpy`` is heavy to import and the solver module is the proper
public surface for tests / scripts that want the full DataFrame
output.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from omaha.rebalance.market_prices import (
    MarketPriceLookup,
    NoopMarketPriceLookup,
)
from omaha.rebalance.solver_stub import (
    RebalanceAssetClassNative,
    RebalanceAssetPlanRowNative,
    RebalanceCategoryPlanRowNative,
    RebalancePlan,
    RebalancePlanMetricsNative,
    RebalanceWarningNative,
)


class _DataFrameMarketPriceLookup:
    """Wrap a pre-resolved quotes DataFrame in the ``MarketPriceLookup`` Protocol.

    The reference solver expects a Protocol instance with
    ``get_quotes(assets) -> DataFrame``. The glue resolves quotes
    upstream (via :class:`OmahaMarketPriceLookup`) and passes the
    resolved frame as ``quotes``. We forward it through this thin
    adapter so :func:`simulate_rebalance` finds the Protocol surface
    it needs.
    """

    def __init__(self, quotes: pd.DataFrame) -> None:
        self._quotes = quotes

    def get_quotes(self, assets: pd.DataFrame) -> pd.DataFrame:
        if assets.empty:
            return self._quotes.iloc[0:0].copy()
        return assets[["asset_key"]].merge(self._quotes, how="left", on="asset_key")


def cvxpy_solver(
    setup: object,
    positions: pd.DataFrame,
    quotes: pd.DataFrame,
    contribution: float,
    *,
    min_deviation_value: float = 1000.0,
    min_deviation_pct: float = 1.0,
) -> RebalancePlan:
    """Glue-compatible callable wrapping :func:`simulate_rebalance`.

    Signature matches ``stub_solver`` in :mod:`omaha.rebalance.solver_stub`
    so :func:`omaha.rebalance.glue.run_rebalance` can dispatch via the
    same kwarg without code edits.

    Returns the v1 wire-format-shaped ``RebalancePlan`` — same native
    dataclasses as the stub. The CVXPY output is projected through the
    9 / 4 / 6 column subset the v1 wire format consumes; the wider 31
    / 13 DataFrames are reachable via direct calls to
    :func:`simulate_rebalance`.
    """
    from omaha.rebalance.solver import simulate_rebalance

    if quotes is None or (isinstance(quotes, pd.DataFrame) and quotes.empty):
        lookup: MarketPriceLookup = NoopMarketPriceLookup()
    else:
        lookup = _DataFrameMarketPriceLookup(quotes)

    native = simulate_rebalance(
        setup=setup,
        position=positions,
        contribution=contribution,
        market_price_lookup=lookup,
        min_deviation_value=min_deviation_value,
        min_deviation_pct=min_deviation_pct,
    )

    asset_plan_rows = _translate_asset_plan(native.asset_plan)
    category_plan_rows = _translate_category_plan(native.category_plan)
    asset_classes = _translate_asset_classes(setup, native.asset_plan)
    metrics = _translate_metrics(native.metrics)
    warnings = _translate_warnings(native.warnings)
    applied_policy = str(native.metrics.get("rebalance_policy", ""))

    return RebalancePlan(
        contribution=float(native.metrics.get("contribution", contribution)),
        asset_classes=asset_classes,
        asset_plan=asset_plan_rows,
        category_plan=category_plan_rows,
        metrics=metrics,
        warnings=warnings,
        applied_policy=applied_policy,
    )


def _translate_asset_plan(asset_plan_df: pd.DataFrame) -> list[RebalanceAssetPlanRowNative]:
    rows: list[RebalanceAssetPlanRowNative] = []
    for _, row in asset_plan_df.iterrows():
        rows.append(
            RebalanceAssetPlanRowNative(
                name=str(row.get("asset_name", row.get("asset_key", ""))),
                category_name=str(row.get("category_name", "")),
                currency_code=str(row.get("currency_code", "")),
                buy_enabled=bool(row.get("buy_enabled", False)),
                current_value=float(row.get("current_value", 0.0)),
                target_value=float(row.get("target_value", 0.0)),
                buy_amount=float(row.get("buy_amount", 0.0)),
                sell_amount=float(row.get("sell_amount", 0.0)),
                quote_price=float(row.get("quote_price", np.nan)),
                usdbrl_rate=float(row.get("usdbrl_rate", np.nan)),
                quote_status=str(row.get("quote_status", "not-requested")),
                projected_value=float(row.get("projected_value", 0.0)),
            )
        )
    return rows


def _translate_category_plan(
    category_plan_df: pd.DataFrame,
) -> list[RebalanceCategoryPlanRowNative]:
    rows: list[RebalanceCategoryPlanRowNative] = []
    for _, row in category_plan_df.iterrows():
        rows.append(
            RebalanceCategoryPlanRowNative(
                category_name=str(row.get("category_name", "")),
                current_value=float(row.get("current_value", 0.0)),
                projected_value=float(row.get("projected_value", 0.0)),
            )
        )
    return rows


def _translate_asset_classes(
    setup: object, asset_plan_df: pd.DataFrame
) -> list[RebalanceAssetClassNative]:
    """Per-class target_weight roll-up derived from ``setup.categories``."""
    categories = getattr(setup, "categories", None)
    if categories is None or categories.empty:
        names = sorted(asset_plan_df.get("category_name", pd.Series(dtype=str)).unique())
        return [RebalanceAssetClassNative(name=name, target_weight=0.0) for name in names]
    rows: list[RebalanceAssetClassNative] = []
    for _, cat in categories.iterrows():
        rows.append(
            RebalanceAssetClassNative(
                name=str(cat.get("category_name", "")),
                target_weight=float(cat.get("target_weight", 0.0)),
            )
        )
    return rows


def _translate_metrics(metrics: dict) -> RebalancePlanMetricsNative:
    return RebalancePlanMetricsNative(
        contribution=float(metrics.get("contribution", 0.0)),
        total_buy=float(metrics.get("total_buy", 0.0)),
        total_sell=float(metrics.get("total_sell", 0.0)),
        residual_cash=float(metrics.get("residual_cash", 0.0)),
        current_deviation_pct=float(metrics.get("current_asset_deviation", 0.0)) * 100,
        projected_deviation_pct=float(metrics.get("projected_asset_deviation", 0.0)) * 100,
    )


def _translate_warnings(messages) -> list[RebalanceWarningNative]:
    """Map PT-BR message strings onto the v1 ``RebalanceWarningNative`` shape.

    The solver emits PT-BR text; the v1 wire format wraps each message
    in ``RebalanceWarning(code, message)`` with a derived code. The
    glue applies its own code mapper first (for builder warnings that
    carry asset-class semantics); the CVXPY-shim path applies the
    generic ``BUILDER_WARNING`` code because the messages are already
    operator-facing.
    """
    out: list[RebalanceWarningNative] = []
    if messages is None:
        return out
    for message in messages:
        out.append(
            RebalanceWarningNative(
                code="BUILDER_WARNING",
                message=str(message),
            )
        )
    return out


__all__ = ["cvxpy_solver"]


_ = np  # silence unused-import warnings (re-exported for tests that re-export cvxpy_solver)
