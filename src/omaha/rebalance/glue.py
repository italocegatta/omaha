"""Orchestration glue that runs the rebalance pipeline end-to-end.

``run_rebalance`` loads the profile, builds the solver inputs,
resolves quotes, calls the injected solver, and translates the solver's
native output into the v1 Pydantic wire format owned by
:mod:`omaha.rebalance.schemas`.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from omaha.models import Profile
from omaha.quotes.cache import QuoteCache
from omaha.rebalance.builders import (
    build_position_frame,
    build_setup_from_db,
)
from omaha.rebalance.quotes_adapter import OmahaMarketPriceLookup
from omaha.rebalance.schemas import (
    RebalanceAssetPlanRow,
    RebalanceCategoryPlanRow,
    RebalancePlanMetrics,
    RebalancePlanResponse,
    RebalanceWarning,
)
from omaha.rebalance.solver_stub import stub_solver

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
    solver: object = None,
) -> RebalancePlanResponse:
    """Build inputs, run the solver, and return the v1 wire response."""
    if solver is None:
        solver = stub_solver

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

    plan_native = solver(setup, positions, quotes, contribution)

    asset_plan = [
        RebalanceAssetPlanRow(
            asset_key=row.name.casefold(),
            asset_name=row.name,
            category_name=row.category_name,
            current_value=float(row.current_value),
            target_value=float(row.target_value),
            buy_amount=float(row.buy_amount),
            sell_amount=float(row.sell_amount),
            projected_value=float(row.projected_value),
            action=_derive_action(
                buy_amount=float(row.buy_amount),
                sell_amount=float(row.sell_amount),
            ),
        )
        for row in plan_native.asset_plan
    ]

    category_plan = [
        RebalanceCategoryPlanRow(
            category_name=row.category_name,
            current_value=float(row.current_value),
            projected_value=float(row.projected_value),
            delta=float(row.projected_value) - float(row.current_value),
        )
        for row in plan_native.category_plan
    ]

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
