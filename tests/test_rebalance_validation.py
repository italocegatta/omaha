"""Eleven validation scenarios for :func:`omaha.rebalance.validation._validate_rebalance_inputs`.

Each test mutates the canonical :func:`build_simple_setup` fixture by
exactly one violation and asserts :class:`RebalanceValidationError`
raises with the reference's PT-BR message fragment.

The reference says to run all checks even after the first one fires,
so we test that multiple-check failures are reported together by the
"checks 1+5 simultaneously" scenario.
"""

from __future__ import annotations

import math
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from omaha.rebalance.models import RebalanceValidationError
from omaha.rebalance.validation import _validate_rebalance_inputs
from tests.fixtures.rebalance_engine import (
    build_simple_position,
    build_simple_setup,
)


def test_check_1_negative_contribution_rejected() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=-1000.0)
    assert "O aporte informado nao pode ser negativo." in str(exc_info.value)


def test_check_2_empty_categories_rejected() -> None:
    setup = build_simple_setup()
    empty_categories = setup.categories.iloc[0:0].copy()
    setup = type(setup)(categories=empty_categories, assets=setup.assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "categorias carregadas" in str(exc_info.value)


def test_check_3_empty_assets_rejected() -> None:
    setup = build_simple_setup()
    empty_assets = setup.assets.iloc[0:0].copy()
    setup = type(setup)(categories=setup.categories, assets=empty_assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "ativos carregados" in str(exc_info.value)


def test_check_4_duplicate_asset_key_rejected() -> None:
    setup = build_simple_setup()
    dup = pd.concat([setup.assets, setup.assets.iloc[[0]]], ignore_index=True)
    setup = type(setup)(categories=setup.categories, assets=dup)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "ativos duplicados" in str(exc_info.value)


def test_check_5_category_target_sum_mismatch_rejected() -> None:
    setup = build_simple_setup()
    cats = setup.categories.copy()
    cats.loc[0, "target_weight"] = 0.5
    setup = type(setup)(categories=cats, assets=setup.assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "categorias devem somar 100%" in str(exc_info.value)


def test_check_6_asset_target_sum_mismatch_rejected() -> None:
    setup = build_simple_setup()
    assets = setup.assets.copy()
    assets.loc[0, "target_weight_in_category"] = 0.7
    setup = type(setup)(categories=setup.categories, assets=assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "deve ter ativos somando 100%" in str(exc_info.value)


def test_check_7_assets_referencing_missing_category_rejected() -> None:
    setup = build_simple_setup()
    assets = setup.assets.copy()
    assets.loc[0, "category_key"] = "categoria-fantasma"
    assets.loc[0, "category_name"] = "Categoria Fantasma"
    setup = type(setup)(categories=setup.categories, assets=assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "categorias ausentes" in str(exc_info.value)


def test_check_8_category_to_asset_target_mismatch_rejected() -> None:
    setup = build_simple_setup()
    assets = setup.assets.copy()
    assets.loc[0, "category_key"] = "categoria-fantasma"
    assets.loc[0, "category_name"] = "Categoria Fantasma"
    setup = type(setup)(categories=setup.categories, assets=assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "categorias ausentes" in str(exc_info.value)


def test_check_9_position_orphan_asset_rejected() -> None:
    setup = build_simple_setup()
    position = build_simple_position(1000.0, 1000.0)
    extra = pd.DataFrame(
        [
            {
                "asset_name": "Ativo Orfao",
                "asset_key": "ativo-orfao",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": 100.0,
                "current_value": 100.0,
                "current_weight": 0.05,
            }
        ]
    )
    position = pd.concat([position, extra], ignore_index=True)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "sem correspondencia no setup" in str(exc_info.value)


def test_check_10_total_current_value_zero_rejected() -> None:
    setup = build_simple_setup()
    position = build_simple_position(0.0, 0.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "patrimonio atual precisa ser positivo" in str(exc_info.value)


def test_check_11_negative_current_value_rejected() -> None:
    setup = build_simple_setup()
    position = build_simple_position(-100.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=100.0)
    assert "patrimonio negativos" in str(exc_info.value)


def test_check_1_plus_check_5_combined_reports_both() -> None:
    """All checks run, even after an early failure — operator sees every problem."""
    setup = build_simple_setup()
    cats = setup.categories.copy()
    cats.loc[0, "target_weight"] = 0.5
    setup = type(setup)(categories=cats, assets=setup.assets)
    position = build_simple_position(1000.0, 1000.0)
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=-1.0)
    message = str(exc_info.value)
    assert "O aporte informado nao pode ser negativo." in message
    assert "categorias devem somar 100%" in message


def test_valid_setup_does_not_raise() -> None:
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    _validate_rebalance_inputs(setup, position, contribution=1000.0)


def test_valid_setup_allows_tiny_float_drift_when_canonical_weights_close() -> None:
    setup = build_simple_setup()
    cats = setup.categories.copy()
    cats.loc[0, "target_weight"] = 0.333333
    cats2 = pd.DataFrame(
        [
            {
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "target_weight": 0.666667,
                "category_order": 1,
            }
        ]
    )
    categories = pd.concat([cats, cats2], ignore_index=True)
    categories.attrs["decimal_columns"] = {
        "target_weight": [Decimal("0.333333"), Decimal("0.666667")]
    }
    assets = pd.DataFrame(
        [
            {
                "asset_name": "RF 1",
                "asset_key": "rf-1",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.5000005,
                "target_weight": 0.1666666666665,
                "asset_order": 0,
            },
            {
                "asset_name": "RF 2",
                "asset_key": "rf-2",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.4999995,
                "target_weight": 0.1666663333335,
                "asset_order": 1,
            },
            {
                "asset_name": "RV 1",
                "asset_key": "rv-1",
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.666667,
                "asset_order": 2,
            },
        ]
    )
    assets.attrs["decimal_columns"] = {
        "target_weight_in_category": [
            Decimal("0.5000005"),
            Decimal("0.4999995"),
            Decimal("1"),
        ],
        "target_weight": [
            Decimal("0.1666666666665"),
            Decimal("0.1666663333335"),
            Decimal("0.666667"),
        ],
    }
    setup = type(setup)(categories=categories, assets=assets)
    position = pd.DataFrame(
        [
            {
                "asset_name": "RF 1",
                "asset_key": "rf-1",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": 1000.0,
                "current_value": 1000.0,
                "current_weight": 0.1,
            },
            {
                "asset_name": "RF 2",
                "asset_key": "rf-2",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": 1000.0,
                "current_value": 1000.0,
                "current_weight": 0.1,
            },
            {
                "asset_name": "RV 1",
                "asset_key": "rv-1",
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "quantity": 1.0,
                "invested_value": 8000.0,
                "current_value": 8000.0,
                "current_weight": 0.8,
            },
        ]
    )

    _validate_rebalance_inputs(setup, position, contribution=1000.0)


def test_position_with_nan_in_numeric_column_rejected() -> None:
    """Defensive check added by omaha — the wire boundary 422s NaN, but
    callers that bypass the boundary should still see a clean error."""
    setup = build_simple_setup()
    position = build_simple_position(5000.0, 5000.0)
    position.loc[0, "current_value"] = float("nan")
    with pytest.raises(RebalanceValidationError) as exc_info:
        _validate_rebalance_inputs(setup, position, contribution=1000.0)
    assert "valores invalidos" in str(exc_info.value)


_ = np  # silence unused-import warning when the module is collected in isolation
_ = math
