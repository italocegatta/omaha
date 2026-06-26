"""Data bridges for the CVXPY rebalance solver.

Phase 2 of ``.planning/REBALANCE_PLAN.md`` (Gaps E, F, G). The reference
algorithm (``~/github/investing/src/portfolio_rebalancing/domain/``)
consumes three inputs that the omaha ORM doesn't produce directly:

* :class:`PortfolioSetup` — categories + assets DataFrames matching
  the algorithm's expected schema (target weights in 0..1, per-asset
  trade-control flags, currency code, plus the omaha-specific
  ``quote_kind`` column).
* A ``Position`` DataFrame — per-asset aggregation of ``qty``,
  ``total_invested``, ``total_current``, and ``current_weight``.
* A :class:`MarketPriceLookup` implementation — the algorithm queries
  live prices via a ``get_quotes(assets) -> DataFrame`` Protocol.

The three pure-function bridges live in this package:

* :func:`builders.build_setup_from_db` — PortfolioSetup + warnings
* :func:`builders.build_position_frame` — Position DataFrame
* :class:`quotes_adapter.OmahaMarketPriceLookup` — Protocol impl

The Protocol and helper functions (:func:`market_prices.resolve_quote_symbol`,
:func:`market_prices.build_empty_quote_frame`) are ports of the
reference so Phase 4 can import the contract verbatim.

Phase 3 (``rebalance-route``) wires these to ``POST /api/rebalance``;
Phase 4 (``rebalance-engine``) plugs in the CVXPY solver. No DB
migration, no UI change, no new route in this phase.
"""

from __future__ import annotations

from omaha.rebalance.models import PortfolioSetup, RebalanceValidationError
from omaha.rebalance.builders import build_position_frame, build_setup_from_db
from omaha.rebalance.market_prices import (
    MarketPriceLookup,
    NoopMarketPriceLookup,
    QuoteSnapshot,
    build_empty_quote_frame,
    is_queryable_quote_symbol,
    resolve_quote_symbol,
)
from omaha.rebalance.quotes_adapter import OmahaMarketPriceLookup

__all__ = [
    "PortfolioSetup",
    "RebalanceValidationError",
    "build_position_frame",
    "build_setup_from_db",
    "MarketPriceLookup",
    "NoopMarketPriceLookup",
    "OmahaMarketPriceLookup",
    "QuoteSnapshot",
    "build_empty_quote_frame",
    "is_queryable_quote_symbol",
    "resolve_quote_symbol",
]
