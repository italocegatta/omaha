"""Protocol + helpers that the CVXPY solver imports verbatim.

This is a thin port of
``~/github/investing/src/portfolio_rebalancing/domain/market_prices.py``.
The reference module defines:

* :class:`MarketPriceLookup` — Protocol that the solver type-checks
  against. ``get_quotes(assets: DataFrame) -> DataFrame`` with the
  seven output columns documented in
  spec §"OmahaMarketPriceLookup satisfies the Protocol".
* :class:`NoopMarketPriceLookup` — an implementation that returns the
  empty frame with all rows marked ``quote_status = self.status``.
  Used by tests and by callers that don't want live quote resolution.
* :func:`resolve_quote_symbol` — maps an asset's broker ticker +
  currency to a yfinance-compatible symbol. ``BRL`` tickers get
  ``.SA`` appended (idempotent on already-suffixed tickers); ``USD``
  tickers pass through verbatim; empty names produce empty symbols.
* :func:`build_empty_quote_frame` — builds the seven-column output
  frame from an input assets frame (one row per asset, NaN prices,
  the requested default status).
* :class:`QuoteSnapshot` — internal helper used by the reference's
  yfinance path. Omaha doesn't use it directly, but it's exported
  here so Phase 4 can import the same dataclass the reference
  defines (keeps the algorithm import-compatible).
* :func:`is_queryable_quote_symbol` — pattern check
  (``^[A-Z0-9.\\-=\\^]+$``) for symbols safe to send to yfinance. Used
  by the reference's downloader to filter junk tickers; the omaha
  adapter inherits the same guard via the cache lookup.
* :func:`_resolve_quote_status` — the freshness + FX dependency
  decision: ``unavailable`` if price is non-finite OR (USD asset AND
  ``BRL=X`` not available); otherwise ``available``. Exposed via
  :func:`quote_status_for` so the adapter doesn't have to import a
  private symbol from the reference's perspective.

What was NOT ported
-------------------
``YFinanceMarketPriceLookup`` and the ``_download_recent_history`` /
``_extract_symbol_history`` / ``_select_symbol_history`` helpers —
omaha reads quotes from :class:`~omaha.quotes.cache.QuoteCache` (a
DB-backed cache populated by :class:`~omaha.quotes.service.QuoteService`),
not from yfinance on the request path. The cache lookup is in
:mod:`omaha.rebalance.quotes_adapter`; this module only owns the
contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd

QUOTE_STATUS_AVAILABLE = "available"
QUOTE_STATUS_UNAVAILABLE = "unavailable"
QUOTE_STATUS_NOT_REQUESTED = "not-requested"
USD_BRL_QUOTE_SYMBOL = "BRL=X"
DEFAULT_QUOTE_LOOKBACK_PERIOD = "5d"
DEFAULT_QUOTE_TIMEOUT_SECONDS = 2.0
QUERYABLE_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-=\^]+$")


class MarketPriceLookup(Protocol):
    """Protocol the CVXPY solver type-checks against.

    Implementations take an assets DataFrame (must contain at minimum
    ``asset_key``, ``asset_name``, and ``currency_code`` columns) and
    return a DataFrame with the seven columns documented in spec
    §"OmahaMarketPriceLookup satisfies the Protocol", one row per
    input asset.
    """

    def get_quotes(self, assets: pd.DataFrame) -> pd.DataFrame:
        """Return normalized quote metadata for the provided assets."""


@dataclass(frozen=True)
class NoopMarketPriceLookup:
    """Inert :class:`MarketPriceLookup` implementation.

    Returns the empty frame with every row's ``quote_status`` set to
    :attr:`status` (default: ``"not-requested"``). Used by tests that
    don't care about quote resolution and by callers building solver
    inputs offline (e.g. a backtest harness that hard-codes asset
    prices).
    """

    status: str = QUOTE_STATUS_NOT_REQUESTED

    def get_quotes(self, assets: pd.DataFrame) -> pd.DataFrame:
        return build_empty_quote_frame(assets, status=self.status)


@dataclass(frozen=True)
class QuoteSnapshot:
    """A point-in-time quote snapshot used by the reference algorithm.

    The reference yfinance path constructs one of these per symbol
    from the yfinance ``history`` DataFrame. Omaha's adapter does not
    construct them directly — the cache stores price + currency +
    timestamp as separate columns — but the dataclass is exported
    so Phase 4 can import the same symbol the reference defines and
    avoid a fork in the algorithm's internal helpers.

    ``price`` is ``None`` for missing/stale snapshots; ``is_available``
    folds that into a single boolean (``price is not None AND
    np.isfinite(price)``).
    """

    price: float | None
    timestamp: str

    @property
    def is_available(self) -> bool:
        return self.price is not None and np.isfinite(self.price)


def resolve_quote_symbol(asset_name: str, currency_code: str) -> str:
    """Map an asset's broker ticker + currency to a yfinance-compatible symbol.

    Rules:

    * Empty ``asset_name`` (stripped) returns ``""`` — caller should
      treat that as "no symbol, do not query the cache".
    * ``currency_code == "BRL"`` appends ``.SA`` when not already
      present. ``"PETR4"`` → ``"PETR4.SA"``; ``"PETR4.SA"`` →
      ``"PETR4.SA"`` (idempotent).
    * Any other currency (``USD``, future values) returns the ticker
      verbatim.

    Both inputs are upper-cased + stripped before the comparison so
    ``"PETR4 "`` / ``"petr4"`` / ``" brl "`` behave the same as the
    canonical form.
    """
    ticker = str(asset_name).strip().upper()
    currency = str(currency_code).strip().upper()
    if not ticker:
        return ""
    if currency == "BRL" and not ticker.endswith(".SA"):
        return f"{ticker}.SA"
    return ticker


def build_empty_quote_frame(assets: pd.DataFrame, *, status: str) -> pd.DataFrame:
    """Build the seven-column quote frame for ``assets`` with default values.

    Returns an empty frame (full schema, zero rows) when ``assets`` is
    empty. Otherwise returns one row per input asset with:

    * ``quote_symbol`` — :func:`resolve_quote_symbol` output
    * ``quote_price`` — ``NaN``
    * ``quote_currency`` — copied from ``assets.currency_code``
    * ``quote_timestamp`` — empty string
    * ``quote_status`` — ``status`` (caller's default; usually
      ``"unavailable"`` for cache-miss, ``"not-requested"`` for the
      noop lookup)
    * ``usdbrl_rate`` — ``NaN`` (caller fills per-row from the BRL=X
      cache lookup when an asset is USD)

    The column order matches the reference module so Phase 4 can
    concatenate / merge frames without an extra reindex step.
    """
    columns = [
        "asset_key",
        "quote_symbol",
        "quote_price",
        "quote_currency",
        "quote_timestamp",
        "quote_status",
        "usdbrl_rate",
    ]
    if assets.empty:
        return pd.DataFrame(columns=columns)

    quote_frame = assets[["asset_key", "asset_name", "currency_code"]].copy()
    quote_frame["quote_symbol"] = quote_frame.apply(
        lambda row: resolve_quote_symbol(
            asset_name=str(row["asset_name"]),
            currency_code=str(row["currency_code"]),
        ),
        axis=1,
    )
    quote_frame["quote_price"] = float("nan")
    quote_frame["quote_currency"] = quote_frame["currency_code"]
    quote_frame["quote_timestamp"] = ""
    quote_frame["quote_status"] = status
    quote_frame["usdbrl_rate"] = float("nan")
    return quote_frame[columns]


def is_queryable_quote_symbol(symbol: str) -> bool:
    """Return True iff ``symbol`` is safe to send to yfinance.

    The pattern (``^[A-Z0-9.\\-=\\^]+$``) excludes lower-case letters
    (yfinance normalizes everything to upper-case anyway) and any
    non-printable character. Empty / whitespace symbols return
    ``False`` — they would produce a yfinance 404 and pollute the
    refresh log with noise.
    """
    normalized = str(symbol).strip().upper()
    if not normalized:
        return False
    return bool(QUERYABLE_SYMBOL_PATTERN.fullmatch(normalized))


def quote_status_for(
    *,
    quote_price: float,
    currency_code: str,
    usdbrl_rate: float,
) -> str:
    """Apply the freshness + FX dependency decision for one quote row.

    Returns:

    * ``"unavailable"`` if ``quote_price`` is non-finite (NaN/inf)
      OR if the asset is USD and ``usdbrl_rate`` is non-finite.
      USD assets with stale ``BRL=X`` cannot be quoted because the
      solver can't convert them to BRL.
    * ``"available"`` otherwise.

    Mirrors the reference's ``_resolve_quote_status`` exactly so the
    adapter's per-row decision matches what Phase 4 expects from the
    solver's perspective.
    """
    if not np.isfinite(quote_price):
        return QUOTE_STATUS_UNAVAILABLE
    if str(currency_code).upper() == "USD" and not np.isfinite(usdbrl_rate):
        return QUOTE_STATUS_UNAVAILABLE
    return QUOTE_STATUS_AVAILABLE


def quote_price_from_cache(price: float | None) -> float:
    """Convert an optional cache price to a solver-friendly float.

    ``None`` (cache miss) and non-finite values both map to ``NaN`` so
    the caller can write one expression without a separate ``is None``
    branch. ``0.0`` is preserved (a real zero is meaningful — some
    legacy positions import with ``current_price = 0`` and the solver
    treats them as "no price available", distinct from "no cache row").
    """
    if price is None or not np.isfinite(float(price)):
        return float("nan")
    return float(price)


__all__ = [
    "MarketPriceLookup",
    "NoopMarketPriceLookup",
    "QuoteSnapshot",
    "QUOTE_STATUS_AVAILABLE",
    "QUOTE_STATUS_NOT_REQUESTED",
    "QUOTE_STATUS_UNAVAILABLE",
    "USD_BRL_QUOTE_SYMBOL",
    "build_empty_quote_frame",
    "is_queryable_quote_symbol",
    "quote_price_from_cache",
    "quote_status_for",
    "resolve_quote_symbol",
]
