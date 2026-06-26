"""Pydantic schemas for the v1 rebalance wire format.

These models are the contract between the native solver output
(Phase 4 ``rebalance-engine``) and the dashboard UI (Phase 3b
``rebalance-page``). They intentionally expose only the v1 subset of
the solver's full native shape — see ``openspec/changes/rebalance-route/design.md``
Decision 1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RebalanceAction = Literal["buy", "sell", "hold"]


class RebalanceAssetPlanRow(BaseModel):
    """One asset row in the v1 rebalance plan."""

    model_config = ConfigDict(extra="forbid")

    asset_key: str
    asset_name: str
    category_name: str
    current_value: float
    target_value: float
    buy_amount: float
    sell_amount: float
    projected_value: float
    action: RebalanceAction


class RebalanceCategoryPlanRow(BaseModel):
    """One asset-class row in the v1 rebalance plan."""

    model_config = ConfigDict(extra="forbid")

    category_name: str
    current_value: float
    projected_value: float
    delta: float


class RebalancePlanMetrics(BaseModel):
    """The six v1 metric keys surfaced to the UI."""

    model_config = ConfigDict(extra="forbid")

    contribution: float
    total_buy: float
    total_sell: float
    residual_cash: float
    current_deviation_pct: float
    projected_deviation_pct: float


class RebalanceWarning(BaseModel):
    """Machine-readable code plus PT-BR operator-facing message."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class RebalancePlanResponse(BaseModel):
    """Top-level response body for ``POST /api/rebalance``."""

    model_config = ConfigDict(extra="forbid")

    asset_plan: list[RebalanceAssetPlanRow]
    category_plan: list[RebalanceCategoryPlanRow]
    metrics: RebalancePlanMetrics
    warnings: list[RebalanceWarning]
    applied_policy: str


class RebalanceRequest(BaseModel):
    """Request body for ``POST /api/rebalance``."""

    contribution: float = Field(
        gt=0,
        description="Aporte em R$ a ser aplicado no rebalanceamento.",
    )
