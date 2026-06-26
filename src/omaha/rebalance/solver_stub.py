"""Deterministic solver stub backed by a frozen JSON fixture.

The stub loads ``tests/fixtures/rebalance_stub_fixture.json`` and
returns it as the solver's native :class:`RebalancePlan` shape. It is
used by Phase 3 (``rebalance-route``) to exercise the HTTP contract and
glue before the real CVXPY solver lands in Phase 4
(``rebalance-engine``).

The fixture is also the golden regression baseline Phase 4 will run
against, so the stub and the real solver share one source of truth for
the expected output shape.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from omaha.rebalance.models import PortfolioSetup


@dataclass(frozen=True)
class RebalancePlanMetricsNative:
    contribution: float
    total_buy: float
    total_sell: float
    residual_cash: float
    current_deviation_pct: float
    projected_deviation_pct: float


@dataclass(frozen=True)
class RebalanceWarningNative:
    code: str
    message: str


@dataclass(frozen=True)
class RebalanceAssetPlanRowNative:
    name: str
    category_name: str
    currency_code: str
    buy_enabled: bool
    current_value: float
    target_value: float
    buy_amount: float
    sell_amount: float
    projected_value: float


@dataclass(frozen=True)
class RebalanceCategoryPlanRowNative:
    category_name: str
    current_value: float
    projected_value: float


@dataclass(frozen=True)
class RebalanceAssetClassNative:
    name: str
    target_weight: float


@dataclass(frozen=True)
class RebalancePlan:
    """Native solver output shape consumed by the rebalance glue.

    Phase 4 will ship its own ``RebalancePlan``; this minimal
    dataclass exists so the stub can return a typed object today
    without coupling the route/glue to a dictionary.
    """

    contribution: float
    asset_classes: list[RebalanceAssetClassNative]
    asset_plan: list[RebalanceAssetPlanRowNative]
    category_plan: list[RebalanceCategoryPlanRowNative]
    metrics: RebalancePlanMetricsNative
    warnings: list[RebalanceWarningNative]
    applied_policy: str


def _fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "fixtures"
        / "rebalance_stub_fixture.json"
    )


def _load_fixture() -> dict:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))


def _to_plan(data: dict) -> RebalancePlan:
    return RebalancePlan(
        contribution=float(data["contribution"]),
        asset_classes=[
            RebalanceAssetClassNative(**cls) for cls in data["asset_classes"]
        ],
        asset_plan=[
            RebalanceAssetPlanRowNative(**asset) for asset in data["assets"]
        ],
        category_plan=[
            RebalanceCategoryPlanRowNative(**cat) for cat in data["category_plan"]
        ],
        metrics=RebalancePlanMetricsNative(**data["metrics"]),
        warnings=[
            RebalanceWarningNative(**warning) for warning in data["warnings"]
        ],
        applied_policy=data["applied_policy"],
    )


def stub_solver(
    setup: PortfolioSetup,
    positions: object,
    quotes: object,
    contribution: float,
) -> RebalancePlan:
    """Return the frozen fixture as a native ``RebalancePlan``.

    ``setup.assets`` and ``setup.categories`` are expected to be
    :class:`pandas.DataFrame` instances (the shape produced by
    :func:`omaha.rebalance.builders.build_setup_from_db`). If both are
    empty, the same ``ValueError`` the real solver would raise is
    emitted so the route can treat empty profiles consistently.

    All other arguments are ignored; the fixture provides the
    deterministic output.
    """
    if setup.assets.empty and setup.categories.empty:
        raise ValueError(
            "empty profile: assets and categories are both empty"
        )

    data = _load_fixture()
    data["metrics"]["contribution"] = float(contribution)
    return _to_plan(data)


__all__ = [
    "RebalancePlan",
    "RebalancePlanMetricsNative",
    "RebalanceWarningNative",
    "RebalanceAssetPlanRowNative",
    "RebalanceCategoryPlanRowNative",
    "stub_solver",
]
