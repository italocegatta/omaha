"""Apêndice D fixtures for the CVXPY rebalance solver.

Ports from ``investing/tests/conftest.py:23-128`` (shared builders) and
``investing/tests/test_rebalancing.py:27-278`` (test-file-scoped
builders). The shared ones live here so solver / policy / postprocessing
unit tests can all import the same DataFrame shapes; the test-file
builders stay in their respective test files for clarity.

Import as:

    from tests.fixtures.rebalance_engine import build_simple_setup, ...

All setups match the omaha ``PortfolioSetup(categories, assets)`` contract
defined in :mod:`omaha.rebalance.models`: two DataFrames with the
documented column schema. Positions match the shape produced by
:func:`omaha.rebalance.builders.build_position_frame` (an outer-join
on ``asset_key`` after the solver's ``_build_simulation_frame``).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from omaha.rebalance.market_prices import MarketPriceLookup  # noqa: F401  (Protocol re-export)
from omaha.rebalance.models import PortfolioSetup


def build_simple_setup() -> PortfolioSetup:
    """Two-asset, single-category setup with 50/50 targets, both BRL, both trade-enabled."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "target_weight": 1.0,
                "category_order": 0,
            }
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "CDB ABC",
                "asset_key": "cdb-abc",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.5,
                "target_weight": 0.5,
                "asset_order": 0,
            },
            {
                "asset_name": "Tesouro Selic",
                "asset_key": "tesouro-selic",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.5,
                "target_weight": 0.5,
                "asset_order": 1,
            },
        ]
    )
    return PortfolioSetup(categories=categories, assets=assets)


def build_simple_position(asset_a_value: float, asset_b_value: float) -> pd.DataFrame:
    """Two-asset position matching :func:`build_simple_setup`.

    ``total == 0`` is allowed (the test for "empty position triggers
    check 10" depends on it) and emits ``current_weight = 0.0`` for
    both rows — matches :func:`omaha.rebalance.builders.build_position_frame`
    behaviour when ``total_current_value == 0``.
    """
    total = asset_a_value + asset_b_value
    rows = []
    for asset_name, asset_key, value in (
        ("CDB ABC", "cdb-abc", asset_a_value),
        ("Tesouro Selic", "tesouro-selic", asset_b_value),
    ):
        rows.append(
            {
                "asset_name": asset_name,
                "asset_key": asset_key,
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": value,
                "current_value": value,
                "current_weight": 0.0 if total == 0 else value / total,
            }
        )
    return pd.DataFrame(rows)


def build_simple_quote_frame() -> pd.DataFrame:
    """Two BRL asset quote rows with ``quote_status='available'``."""
    return pd.DataFrame(
        [
            {
                "asset_key": "cdb-abc",
                "quote_symbol": "CDB-ABC.SA",
                "quote_price": 12.0,
                "quote_currency": "BRL",
                "quote_timestamp": "2026-03-31T00:00:00",
                "quote_status": "available",
                "usdbrl_rate": float("nan"),
            },
            {
                "asset_key": "tesouro-selic",
                "quote_symbol": "TESOURO-SELIC.SA",
                "quote_price": 10.0,
                "quote_currency": "BRL",
                "quote_timestamp": "2026-03-31T00:00:00",
                "quote_status": "available",
                "usdbrl_rate": float("nan"),
            },
        ]
    )


@dataclass
class StubMarketPriceLookup:
    """Stub :class:`MarketPriceLookup` that returns pre-built quotes by ``asset_key``.

    Useful in solver unit tests that need a deterministic quote frame.
    Pass the frame once at construction; ``get_quotes`` performs a
    left join on ``asset_key`` and returns the merged frame so missing
    input rows emit ``NaN`` / blank defaults.
    """

    quotes: pd.DataFrame

    def get_quotes(self, assets: pd.DataFrame) -> pd.DataFrame:
        if assets.empty:
            return self.quotes.iloc[0:0].copy()
        return assets[["asset_key"]].merge(self.quotes, how="left", on="asset_key")


def build_zero_target_setup() -> PortfolioSetup:
    """One category, two assets — A target 0 (sell-only), B target 100% (both flags on)."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "target_weight": 1.0,
                "category_order": 0,
            }
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "CDB Legado",
                "asset_key": "cdb-legado",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": False,
                "sell_enabled": True,
                "target_weight_in_category": 0.0,
                "target_weight": 0.0,
                "asset_order": 0,
            },
            {
                "asset_name": "Tesouro Selic",
                "asset_key": "tesouro-selic",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 1.0,
                "asset_order": 1,
            },
        ]
    )
    return PortfolioSetup(categories=categories, assets=assets)


def build_weighted_setup(weights: list[float]) -> PortfolioSetup:
    """One category, N assets with custom ``target_weight`` / ``target_weight_in_category``."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "target_weight": 1.0,
                "category_order": 0,
            }
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": f"Ativo {idx}",
                "asset_key": f"ativo-{idx}",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": weight,
                "target_weight": weight,
                "asset_order": idx - 1,
            }
            for idx, weight in enumerate(weights, start=1)
        ]
    )
    return PortfolioSetup(categories=categories, assets=assets)


def build_weighted_position(values: list[float]) -> pd.DataFrame:
    """N-asset position matching :func:`build_weighted_setup`."""
    total = float(sum(values))
    return pd.DataFrame(
        [
            {
                "asset_name": f"Ativo {idx}",
                "asset_key": f"ativo-{idx}",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": value,
                "current_value": value,
                "current_weight": 0.0 if total == 0 else value / total,
            }
            for idx, value in enumerate(values, start=1)
        ]
    )


def build_two_category_setup() -> PortfolioSetup:
    """Two categories (60/40), one asset per category."""
    categories = pd.DataFrame(
        [
            {
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "target_weight": 0.6,
                "category_order": 0,
            },
            {
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "target_weight": 0.4,
                "category_order": 1,
            },
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "Tesouro Selic",
                "asset_key": "tesouro-selic",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.6,
                "asset_order": 0,
            },
            {
                "asset_name": "ETF BOVA11",
                "asset_key": "etf-bova11",
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.4,
                "asset_order": 1,
            },
        ]
    )
    return PortfolioSetup(categories=categories, assets=assets)


def build_two_category_position(
    renda_fixa_value: float,
    renda_variavel_value: float,
) -> pd.DataFrame:
    """Two-asset position matching :func:`build_two_category_setup`."""
    total = renda_fixa_value + renda_variavel_value
    return pd.DataFrame(
        [
            {
                "asset_name": "Tesouro Selic",
                "asset_key": "tesouro-selic",
                "category_name": "Renda Fixa",
                "category_key": "renda-fixa",
                "quantity": 1.0,
                "invested_value": renda_fixa_value,
                "current_value": renda_fixa_value,
                "current_weight": 0.0 if total == 0 else renda_fixa_value / total,
            },
            {
                "asset_name": "ETF BOVA11",
                "asset_key": "etf-bova11",
                "category_name": "Renda Variavel",
                "category_key": "renda-variavel",
                "quantity": 1.0,
                "invested_value": renda_variavel_value,
                "current_value": renda_variavel_value,
                "current_weight": 0.0 if total == 0 else renda_variavel_value / total,
            },
        ]
    )


def build_category_first_setup() -> PortfolioSetup:
    """Two 50/50 categories. A=1 asset; B=2 assets 50/50 intra.

    Used by the RBRX11 regression tests. Class B has intra-category
    positions which the test data perturbs to create the
    "underweight-category with internal overweights" scenario.
    """
    categories = pd.DataFrame(
        [
            {
                "category_name": "Categoria A",
                "category_key": "categoria-a",
                "target_weight": 0.5,
                "category_order": 0,
            },
            {
                "category_name": "Categoria B",
                "category_key": "categoria-b",
                "target_weight": 0.5,
                "category_order": 1,
            },
        ]
    )
    assets = pd.DataFrame(
        [
            {
                "asset_name": "FII-A",
                "asset_key": "fii-a",
                "category_name": "Categoria A",
                "category_key": "categoria-a",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 1.0,
                "target_weight": 0.5,
                "asset_order": 0,
            },
            {
                "asset_name": "FII-B1",
                "asset_key": "fii-b1",
                "category_name": "Categoria B",
                "category_key": "categoria-b",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.5,
                "target_weight": 0.25,
                "asset_order": 1,
            },
            {
                "asset_name": "FII-B2",
                "asset_key": "fii-b2",
                "category_name": "Categoria B",
                "category_key": "categoria-b",
                "currency_code": "BRL",
                "buy_enabled": True,
                "sell_enabled": True,
                "target_weight_in_category": 0.5,
                "target_weight": 0.25,
                "asset_order": 2,
            },
        ]
    )
    return PortfolioSetup(categories=categories, assets=assets)


def build_category_first_position() -> pd.DataFrame:
    """Position concentrating value in FII-B1 to create overweight-intra / underweight-category."""
    values = [
        ("FII-A", "fii-a", "Categoria A", "categoria-a", 10_000.0),
        ("FII-B1", "fii-b1", "Categoria B", "categoria-b", 80_000.0),
        ("FII-B2", "fii-b2", "Categoria B", "categoria-b", 10_000.0),
    ]
    total = float(sum(value for *_, value in values))
    return pd.DataFrame(
        [
            {
                "asset_name": asset_name,
                "asset_key": asset_key,
                "category_name": category_name,
                "category_key": category_key,
                "quantity": 1.0,
                "invested_value": value,
                "current_value": value,
                "current_weight": value / total,
            }
            for asset_name, asset_key, category_name, category_key, value in values
        ]
    )


__all__ = [
    "StubMarketPriceLookup",
    "build_category_first_position",
    "build_category_first_setup",
    "build_simple_position",
    "build_simple_quote_frame",
    "build_simple_setup",
    "build_two_category_position",
    "build_two_category_setup",
    "build_weighted_position",
    "build_weighted_setup",
    "build_zero_target_setup",
]
