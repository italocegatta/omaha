"""Orchestration glue that runs the rebalance pipeline end-to-end.

``run_rebalance`` loads the profile, builds the solver inputs,
resolves quotes, calls the injected solver, and translates the solver's
native output into the v1 Pydantic wire format owned by
:mod:`omaha.rebalance.schemas`.
"""

from __future__ import annotations

import dataclasses
import inspect
import math
from typing import TYPE_CHECKING

from omaha.models import Profile
from omaha.quotes.cache import QuoteCache
from omaha.rebalance.builders import (
    build_position_frame,
    build_setup_from_db,
)
from omaha.rebalance.engine import cvxpy_solver
from omaha.rebalance.quotes_adapter import OmahaMarketPriceLookup
from omaha.rebalance.schemas import (
    DEFAULT_MIN_DEVIATION_PCT,
    DEFAULT_MIN_DEVIATION_VALUE,
    RebalanceAssetPlanRow,
    RebalanceCategoryPlanRow,
    RebalancePlanMetrics,
    RebalancePlanResponse,
    RebalanceWarning,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DISPLAY_TOLERANCE = 1e-4


def _derive_action(*, buy_amount: float, sell_amount: float) -> str:
    if buy_amount > DISPLAY_TOLERANCE:
        return "buy"
    if sell_amount > DISPLAY_TOLERANCE:
        return "sell"
    return "hold"


def _warning_code_from_message(message: str) -> str:
    lowered = message.lower()
    if "vazia" in lowered:
        return "EMPTY_CLASS_NONZERO_TARGET"
    if message.startswith("Ativo"):
        return "ASSET_NAME_COLLISION"
    return "BUILDER_WARNING"


def _derive_trade_quantity(
    *,
    buy_amount: float,
    sell_amount: float,
    currency_code: str,
    quote_price: float,
    usdbrl_rate: float,
) -> float | None:
    trade_amount = buy_amount if buy_amount > DISPLAY_TOLERANCE else sell_amount
    if trade_amount <= DISPLAY_TOLERANCE:
        return None
    if not math.isfinite(quote_price) or quote_price <= DISPLAY_TOLERANCE:
        return None

    if str(currency_code).strip().upper() == "USD":
        if not math.isfinite(usdbrl_rate) or usdbrl_rate <= DISPLAY_TOLERANCE:
            return None
        trade_amount = trade_amount / usdbrl_rate

    return trade_amount / quote_price


def _metrics_from_native(native_metrics: object) -> RebalancePlanMetrics:
    if isinstance(native_metrics, dict):
        kwargs = native_metrics
    else:
        kwargs = dataclasses.asdict(native_metrics)
    return RebalancePlanMetrics(**kwargs)


def run_rebalance(
    db: Session,
    profile: Profile,
    contribution: float,
    *,
    min_deviation_value: float = DEFAULT_MIN_DEVIATION_VALUE,
    min_deviation_pct: float = DEFAULT_MIN_DEVIATION_PCT,
    solver: object = None,
) -> RebalancePlanResponse:
    """Build inputs, run the solver, and return the v1 wire response."""
    if solver is None:
        solver = cvxpy_solver

    contribution = float(contribution)

    setup, builder_warnings = build_setup_from_db(db, profile)

    if setup.assets.empty and setup.categories.empty:
        return RebalancePlanResponse(
            asset_plan=[],
            category_plan=[],
            metrics=RebalancePlanMetrics(
                contribution=contribution,
                total_buy=0.0,
                total_sell=0.0,
                residual_cash=0.0,
                current_deviation_pct=0.0,
                projected_deviation_pct=0.0,
            ),
            warnings=[
                RebalanceWarning(
                    code="EMPTY_PROFILE",
                    message=(
                        "Perfil sem classes nem ativos cadastrados. "
                        "Importe um extrato ou cadastre classes/ativos "
                        "antes de rebalancear."
                    ),
                )
            ],
            applied_policy="empty-profile",
        )

    positions = build_position_frame(db, profile)
    lookup = OmahaMarketPriceLookup(cache=QuoteCache(), db=db)
    quotes = lookup.get_quotes(setup.assets)

    solver_kwargs: dict[str, float] = {}
    signature = inspect.signature(solver)
    parameters = signature.parameters
    if any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
    ) or ("min_deviation_value" in parameters and "min_deviation_pct" in parameters):
        solver_kwargs = {
            "min_deviation_value": float(min_deviation_value),
            "min_deviation_pct": float(min_deviation_pct),
        }

    plan_native = solver(setup, positions, quotes, contribution, **solver_kwargs)

    total_portfolio = sum(float(row.current_value) for row in plan_native.asset_plan)

    asset_plan = []
    for row in plan_native.asset_plan:
        cv = float(row.current_value)
        tv = float(row.target_value)
        buy_amount = float(row.buy_amount)
        sell_amount = float(row.sell_amount)
        deviation_value = cv - tv
        deviation_pct = (deviation_value / tv * 100) if tv != 0 else 0.0
        asset_plan.append(
            RebalanceAssetPlanRow(
                asset_key=row.name.casefold(),
                asset_name=row.name,
                category_name=row.category_name,
                current_value=cv,
                target_value=tv,
                buy_amount=buy_amount,
                sell_amount=sell_amount,
                trade_quantity=_derive_trade_quantity(
                    buy_amount=buy_amount,
                    sell_amount=sell_amount,
                    currency_code=str(getattr(row, "currency_code", "")),
                    quote_price=float(getattr(row, "quote_price", math.nan)),
                    usdbrl_rate=float(getattr(row, "usdbrl_rate", math.nan)),
                ),
                projected_value=float(row.projected_value),
                action=_derive_action(
                    buy_amount=buy_amount,
                    sell_amount=sell_amount,
                ),
                deviation_value=deviation_value,
                deviation_pct=deviation_pct,
            )
        )

    # Build per-category target_value sums for target_pct computation
    cat_target_sums: dict[str, float] = {}
    for row in plan_native.asset_plan:
        cat = row.category_name
        cat_target_sums[cat] = cat_target_sums.get(cat, 0.0) + float(row.target_value)

    category_plan = []
    for row in plan_native.category_plan:
        cv = float(row.current_value)
        pv = float(row.projected_value)
        delta = pv - cv
        current_pct = (cv / total_portfolio * 100) if total_portfolio > 0 else 0.0
        target_pct = (
            (cat_target_sums.get(row.category_name, 0.0) / total_portfolio * 100)
            if total_portfolio > 0
            else 0.0
        )
        deviation_pct = current_pct - target_pct
        category_plan.append(
            RebalanceCategoryPlanRow(
                category_name=row.category_name,
                current_value=cv,
                projected_value=pv,
                delta=delta,
                target_pct=target_pct,
                current_pct=current_pct,
                deviation_pct=deviation_pct,
            )
        )

    metrics = _metrics_from_native(plan_native.metrics)

    warnings: list[RebalanceWarning] = [
        RebalanceWarning(
            code=_warning_code_from_message(message),
            message=message,
        )
        for message in builder_warnings
    ]
    warnings.extend(
        RebalanceWarning(code=warning.code, message=warning.message)
        for warning in plan_native.warnings
    )

    return RebalancePlanResponse(
        asset_plan=asset_plan,
        category_plan=category_plan,
        metrics=metrics,
        warnings=warnings,
        applied_policy=plan_native.applied_policy,
    )


__all__ = ["run_rebalance"]
