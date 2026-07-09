"""Pydantic schemas for the v1 rebalance wire format.

These models are the contract between the native solver output
(Phase 4 ``rebalance-engine``) and the dashboard UI (Phase 3b
``rebalance-page``). They intentionally expose only the v1 subset of
the solver's full native shape — see ``openspec/changes/rebalance-route/design.md``
Decision 1.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RebalanceAction = Literal["buy", "sell", "hold"]
DEFAULT_MIN_DEVIATION_VALUE = 1000.0
DEFAULT_MIN_DEVIATION_PCT = 1.0


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
    trade_quantity: float | None = None
    projected_value: float
    action: RebalanceAction
    deviation_value: float = 0.0
    deviation_pct: float = 0.0


class RebalanceCategoryPlanRow(BaseModel):
    """One asset-class row in the v1 rebalance plan."""

    model_config = ConfigDict(extra="forbid")

    category_name: str
    current_value: float
    projected_value: float
    delta: float
    target_pct: float = 0.0
    current_pct: float = 0.0
    deviation_pct: float = 0.0


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
    """Request body for ``POST /api/rebalance``.

    ``contribution`` accepts any finite float (positive, zero, or
    negative). ``0`` is a valid rebalance-only case (no new money,
    just reallocation). Negative values are accepted so the page can
    experiment with withdrawals client-side in v1; the engine in
    Phase 4 (``rebalance-engine``) will interpret them properly when
    it lands. The ``finite_float`` validator rejects ``NaN`` /
    ``Infinity`` so the wire boundary returns 422 for non-finite
    values (Pydantic v2's default float field would accept them
    otherwise).
    """

    contribution: float = Field(
        default=0,
        description=(
            "Aporte em R$ a ser aplicado no rebalanceamento. Aceita "
            "0 (rebalance sem dinheiro novo) e valores negativos "
            "(saque; suporte do solver chega em rebalance-engine)."
        ),
    )
    min_deviation_value: float = Field(
        default=DEFAULT_MIN_DEVIATION_VALUE,
        description="Desvio minimo absoluto em R$ para manter compra/venda sugerida.",
    )
    min_deviation_pct: float = Field(
        default=DEFAULT_MIN_DEVIATION_PCT,
        description="Desvio minimo percentual para manter compra/venda sugerida.",
    )

    @field_validator("contribution", "min_deviation_value", "min_deviation_pct")
    @classmethod
    def _finite_float(cls, value: float) -> float:
        """Reject ``NaN`` and ``Infinity`` with a Pydantic ValidationError.

        Pydantic v2's default float field accepts non-finite values;
        the v1 contract explicitly requires 422 on those, so this
        validator enforces the finite-float guarantee at the wire
        boundary (the page's client-side gate does not protect the
        JSON route — a hand-crafted POST must still fail cleanly).
        """
        if not math.isfinite(value):
            raise ValueError("contribution deve ser um número finito (NaN/Inf não são aceitos)")
        return value

    @field_validator("min_deviation_value", "min_deviation_pct")
    @classmethod
    def _non_negative_threshold(cls, value: float) -> float:
        if value < 0:
            raise ValueError("thresholds de desvio devem ser zero ou positivos")
        return value
