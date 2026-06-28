"""Integration tests for the rebalance Pydantic schemas.

Covers the spec requirements §"POST /api/rebalance returns a
RebalancePlanResponse" and §"Wire format exposes a v1 subset".
The Pydantic models are pure-function and don't touch the DB; the
``integration`` marker is carried for symmetry with the rest of
the rebalance suite so the path-based marker rule in
``tests/conftest.py`` routes the file to the integration subset.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from omaha.rebalance.schemas import (
    RebalanceAssetPlanRow,
    RebalanceCategoryPlanRow,
    RebalancePlanMetrics,
    RebalancePlanResponse,
    RebalanceRequest,
    RebalanceWarning,
)


def _sample_plan() -> RebalancePlanResponse:
    """Build a fully-populated ``RebalancePlanResponse`` for round-trip tests."""
    return RebalancePlanResponse(
        asset_plan=[
            RebalanceAssetPlanRow(
                asset_key="petr4",
                asset_name="PETR4",
                category_name="Renda Variável",
                current_value=1500.0,
                target_value=1000.0,
                buy_amount=0.0,
                sell_amount=500.0,
                projected_value=1000.0,
                action="sell",
            ),
            RebalanceAssetPlanRow(
                asset_key="cdb abc",
                asset_name="CDB ABC",
                category_name="Renda Fixa",
                current_value=3000.0,
                target_value=3200.0,
                buy_amount=200.0,
                sell_amount=0.0,
                projected_value=3200.0,
                action="buy",
            ),
        ],
        category_plan=[
            RebalanceCategoryPlanRow(
                category_name="Renda Fixa",
                current_value=5000.0,
                projected_value=5400.0,
                delta=400.0,
            ),
            RebalanceCategoryPlanRow(
                category_name="Renda Variável",
                current_value=3000.0,
                projected_value=3600.0,
                delta=600.0,
            ),
        ],
        metrics=RebalancePlanMetrics(
            contribution=1000.0,
            total_buy=1500.0,
            total_sell=500.0,
            residual_cash=0.0,
            current_deviation_pct=5.0,
            projected_deviation_pct=0.2,
        ),
        warnings=[
            RebalanceWarning(
                code="EMPTY_CLASS_NONZERO_TARGET",
                message=(
                    "Classe 'Cripto' está vazia mas com "
                    "target_pct=20.00%; solver irá alocar caixa residual."
                ),
            ),
        ],
        applied_policy="contribution-only",
    )


# ---------------------------------------------------------------------------
# §"POST /api/rebalance returns a RebalancePlanResponse"
# ---------------------------------------------------------------------------


def test_request_accepts_zero_contribution() -> None:
    """``contribution = 0`` is accepted (rebalance-only case)."""
    req = RebalanceRequest(contribution=0)
    assert req.contribution == 0


def test_request_accepts_negative_contribution() -> None:
    """``contribution < 0`` is accepted (withdrawal; gated client-side)."""
    req = RebalanceRequest(contribution=-100.0)
    assert req.contribution == -100.0


def test_request_rejects_nan_contribution() -> None:
    """``NaN`` must raise ValidationError (Pydantic finite-float guard)."""
    with pytest.raises(ValidationError):
        RebalanceRequest.model_validate({"contribution": float("nan")})


def test_request_rejects_infinity_contribution() -> None:
    """``Infinity`` and ``-Infinity`` must raise ValidationError."""
    with pytest.raises(ValidationError):
        RebalanceRequest.model_validate({"contribution": float("inf")})
    with pytest.raises(ValidationError):
        RebalanceRequest.model_validate({"contribution": float("-inf")})


def test_request_rejects_missing_field() -> None:
    """Missing ``contribution`` must raise ValidationError."""
    with pytest.raises(ValidationError):
        RebalanceRequest()  # type: ignore[call-arg]


def test_request_accepts_positive_contribution() -> None:
    """Positive contribution is accepted."""
    req = RebalanceRequest(contribution=5000.0)
    assert req.contribution == 5000.0


# ---------------------------------------------------------------------------
# §"Wire format exposes a v1 subset"
# ---------------------------------------------------------------------------


def test_asset_plan_row_carries_exactly_nine_fields() -> None:
    """``RebalanceAssetPlanRow`` has exactly the 9 v1 fields."""
    row = RebalanceAssetPlanRow(
        asset_key="x",
        asset_name="X",
        category_name="Y",
        current_value=0.0,
        target_value=0.0,
        buy_amount=0.0,
        sell_amount=0.0,
        projected_value=0.0,
        action="hold",
    )
    expected = {
        "asset_key",
        "asset_name",
        "category_name",
        "current_value",
        "target_value",
        "buy_amount",
        "sell_amount",
        "projected_value",
        "action",
    }
    assert set(row.model_dump().keys()) == expected


def test_category_plan_row_carries_exactly_four_fields() -> None:
    """``RebalanceCategoryPlanRow`` has exactly the 4 v1 fields."""
    row = RebalanceCategoryPlanRow(
        category_name="X",
        current_value=0.0,
        projected_value=0.0,
        delta=0.0,
    )
    expected = {"category_name", "current_value", "projected_value", "delta"}
    assert set(row.model_dump().keys()) == expected


def test_plan_metrics_carries_exactly_six_keys() -> None:
    """``RebalancePlanMetrics`` has exactly the 6 v1 keys."""
    metrics = RebalancePlanMetrics(
        contribution=0.0,
        total_buy=0.0,
        total_sell=0.0,
        residual_cash=0.0,
        current_deviation_pct=0.0,
        projected_deviation_pct=0.0,
    )
    expected = {
        "contribution",
        "total_buy",
        "total_sell",
        "residual_cash",
        "current_deviation_pct",
        "projected_deviation_pct",
    }
    assert set(metrics.model_dump().keys()) == expected


def test_extra_forbid_rejects_unknown_keys_on_asset_row() -> None:
    """``extra='forbid'`` rejects unknown keys so solver columns don't leak."""
    with pytest.raises(ValidationError):
        RebalanceAssetPlanRow(
            asset_key="x",
            asset_name="X",
            category_name="Y",
            current_value=0.0,
            target_value=0.0,
            buy_amount=0.0,
            sell_amount=0.0,
            projected_value=0.0,
            action="hold",
            current_weight=0.5,  # type: ignore[call-arg]
        )


def test_action_enum_rejects_unknown_value() -> None:
    """``action`` must be one of ``buy`` / ``sell`` / ``hold``."""
    with pytest.raises(ValidationError):
        RebalanceAssetPlanRow(
            asset_key="x",
            asset_name="X",
            category_name="Y",
            current_value=0.0,
            target_value=0.0,
            buy_amount=0.0,
            sell_amount=0.0,
            projected_value=0.0,
            action="liquidate",  # type: ignore[arg-type]
        )


def test_warning_carries_code_and_message() -> None:
    """``RebalanceWarning`` has ``code`` (machine-readable) + ``message`` (PT-BR)."""
    w = RebalanceWarning(code="EMPTY_PROFILE", message="Perfil vazio.")
    assert w.code == "EMPTY_PROFILE"
    assert w.message == "Perfil vazio."


def test_response_round_trips_through_model_dump() -> None:
    """A full ``RebalancePlanResponse`` serializes and re-validates cleanly."""
    plan = _sample_plan()
    dumped = plan.model_dump()
    restored = RebalancePlanResponse.model_validate(dumped)
    assert restored == plan


def test_response_top_level_has_five_fields() -> None:
    """The response carries ``asset_plan`` + ``category_plan`` + ``metrics``
    + ``warnings`` + ``applied_policy`` (top-level, not under metrics)."""
    plan = _sample_plan()
    expected = {
        "asset_plan",
        "category_plan",
        "metrics",
        "warnings",
        "applied_policy",
    }
    assert set(plan.model_dump().keys()) == expected


def test_applied_policy_echoed_at_top_level_not_metrics() -> None:
    """``applied_policy`` lives at the top of the response, not under metrics."""
    plan = _sample_plan()
    assert plan.applied_policy == "contribution-only"
    # ``metrics`` must NOT carry the policy field.
    assert "applied_policy" not in plan.metrics.model_dump()
