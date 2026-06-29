"""RBRX11 coupled regressions — Apêndice B.1 + B.2 ported together.

Reference explicitly requires both fixes be ported in the same change
"Replicar só o fix de Phase 2 sem o de Phase 1 não reproduz o
comportamento correto. Replicar só o de Phase 1 sem o de Phase 2 idem.
Os dois fixes devem ser portados juntos."
(``docs/portfolio-rebalance-algorithm-reference.md`` §B.2 closing
paragraph.)

The RBRX11 scenarios are constructed inline (not via
:func:`build_category_first_setup`) because the reference's setup is
specific: a slightly-underweight FII category receiving a small
contribution while FII-A sits exactly at its global target. The
``build_category_first_setup`` fixture exercises a different
intra-cat imbalance and is used by other tests.

* **B.1** — Phase 2 must not sell an asset at-or-below its global
  target when the category is receiving capital.
* **B.2** — Phase 1 must not drain an underweight category even
  when internal assets are over their intra-cat targets.
"""

from __future__ import annotations

import pandas as pd
import pytest

from omaha.rebalance.models import RebalanceValidationError
from omaha.rebalance.solver import simulate_rebalance


def _build_rbrx11_setup() -> tuple:
    """Reference RBRX11 setup: FII 15%, Outros 85% with intra weights."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "FII",
                "category_key": "fii",
                "target_weight": 0.15,
                "category_order": 0,
            },
            {
                "category_name": "Outros",
                "category_key": "outros",
                "target_weight": 0.85,
                "category_order": 1,
            },
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "Ativo FII-A",
                "asset_key": "fii-a",
                "category_name": "FII",
                "category_key": "fii",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 8 / 15,
                "target_weight": 0.08,
                "asset_order": 0,
            },
            {
                "asset_name": "Ativo FII-B",
                "asset_key": "fii-b",
                "category_name": "FII",
                "category_key": "fii",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 7 / 15,
                "target_weight": 0.07,
                "asset_order": 1,
            },
            {
                "asset_name": "Ativo Outros-A",
                "asset_key": "outros-a",
                "category_name": "Outros",
                "category_key": "outros",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.85,
                "asset_order": 2,
            },
        ]
    )
    return categories, assets


def _build_rbrx11_position() -> pd.DataFrame:
    total = 100_000.0
    fii_a_value = 8_000.0
    fii_b_value = 5_000.0
    outros_value = 87_000.0
    return pd.DataFrame(
        [
            {
                "asset_name": "Ativo FII-A",
                "asset_key": "fii-a",
                "category_name": "FII",
                "category_key": "fii",
                "quantity": 1.0,
                "invested_value": fii_a_value,
                "current_value": fii_a_value,
                "current_weight": fii_a_value / total,
            },
            {
                "asset_name": "Ativo FII-B",
                "asset_key": "fii-b",
                "category_name": "FII",
                "category_key": "fii",
                "quantity": 1.0,
                "invested_value": fii_b_value,
                "current_value": fii_b_value,
                "current_weight": fii_b_value / total,
            },
            {
                "asset_name": "Ativo Outros-A",
                "asset_key": "outros-a",
                "category_name": "Outros",
                "category_key": "outros",
                "quantity": 1.0,
                "invested_value": outros_value,
                "current_value": outros_value,
                "current_weight": outros_value / total,
            },
        ]
    )


def _build_b2_setup() -> tuple:
    """Reference B.2 setup: 60/40 split with intra overweights in class B."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "Categoria A",
                "category_key": "cat-a",
                "target_weight": 0.60,
                "category_order": 0,
            },
            {
                "category_name": "Categoria B",
                "category_key": "cat-b",
                "target_weight": 0.40,
                "category_order": 1,
            },
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "Ativo A1",
                "asset_key": "a1",
                "category_name": "Categoria A",
                "category_key": "cat-a",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.60,
                "asset_order": 0,
            },
            {
                "asset_name": "Ativo B1",
                "asset_key": "b1",
                "category_name": "Categoria B",
                "category_key": "cat-b",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.80,
                "target_weight": 0.32,
                "asset_order": 1,
            },
            {
                "asset_name": "Ativo B2",
                "asset_key": "b2",
                "category_name": "Categoria B",
                "category_key": "cat-b",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.20,
                "target_weight": 0.08,
                "asset_order": 2,
            },
        ]
    )
    return categories, assets


def _build_b2_position() -> pd.DataFrame:
    total = 100_000.0
    a1_value = 62_000.0
    b1_value = 30_000.0
    b2_value = 8_000.0
    return pd.DataFrame(
        [
            {
                "asset_name": "Ativo A1",
                "asset_key": "a1",
                "category_name": "Categoria A",
                "category_key": "cat-a",
                "quantity": 1.0,
                "invested_value": a1_value,
                "current_value": a1_value,
                "current_weight": a1_value / total,
            },
            {
                "asset_name": "Ativo B1",
                "asset_key": "b1",
                "category_name": "Categoria B",
                "category_key": "cat-b",
                "quantity": 1.0,
                "invested_value": b1_value,
                "current_value": b1_value,
                "current_weight": b1_value / total,
            },
            {
                "asset_name": "Ativo B2",
                "asset_key": "b2",
                "category_name": "Categoria B",
                "category_key": "cat-b",
                "quantity": 1.0,
                "invested_value": b2_value,
                "current_value": b2_value,
                "current_weight": b2_value / total,
            },
        ]
    )


def test_phase2_does_not_sell_asset_at_target_when_category_receives_contribution() -> None:
    """B.1 regression (FII-A is exactly at its global target)."""
    from omaha.rebalance.models import PortfolioSetup

    categories, assets = _build_rbrx11_setup()
    setup = PortfolioSetup(categories=categories, assets=assets)
    position = _build_rbrx11_position()

    plan = simulate_rebalance(setup, position, contribution=7_000.0)

    fii_a_row = plan.asset_plan.loc[plan.asset_plan["asset_key"] == "fii-a"].iloc[0]
    fii_b_row = plan.asset_plan.loc[plan.asset_plan["asset_key"] == "fii-b"].iloc[0]

    assert float(fii_a_row["sell_amount"]) == pytest.approx(0.0, abs=1e-4), (
        "FII-A is at its global target; the RBRX11 B.1 fix must prevent a sell"
    )
    assert float(fii_b_row["sell_amount"]) == pytest.approx(0.0, abs=1e-4), (
        "FII-B is below target; Phase 2 must not sell it either"
    )
    assert float(fii_a_row["projected_value"]) >= 8_000.0 - 1.0


def test_phase1_does_not_drain_underweight_category_even_with_internal_overweights() -> None:
    """B.2 regression (class B is underweight overall but B1 is intra overweight)."""
    from omaha.rebalance.models import PortfolioSetup

    categories, assets = _build_b2_setup()
    setup = PortfolioSetup(categories=categories, assets=assets)
    position = _build_b2_position()

    plan = simulate_rebalance(setup, position, contribution=2_000.0)

    b1_row = plan.asset_plan.loc[plan.asset_plan["asset_key"] == "b1"].iloc[0]
    cat_b = plan.category_plan.loc[plan.category_plan["category_name"] == "Categoria B"].iloc[0]

    assert float(b1_row["sell_amount"]) == pytest.approx(0.0, abs=1e-4), (
        "B1 is below intra-cat target; Phase 1 must NOT extract from class B"
    )
    cat_b_current = 30_000.0 + 8_000.0
    assert float(cat_b["projected_value"]) >= cat_b_current - 1.0, (
        "Category B is underweight overall; Phase 1 must not drain it"
    )


def test_negative_contribution_rejected_by_engine() -> None:
    """Design Decision 2 — engine rejects ``contribution < 0``."""
    from omaha.rebalance.models import PortfolioSetup

    categories, assets = _build_b2_setup()
    setup = PortfolioSetup(categories=categories, assets=assets)
    position = _build_b2_position()
    with pytest.raises(RebalanceValidationError) as exc_info:
        simulate_rebalance(setup, position, contribution=-1000.0)
    assert "O aporte informado nao pode ser negativo." in str(exc_info.value)
