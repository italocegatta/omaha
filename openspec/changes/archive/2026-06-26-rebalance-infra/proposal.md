# Change: rebalance-infra

## Why

The reference rebalancing algorithm (`~/github/investing/src/portfolio_rebalancing/`) expects
`PortfolioSetup`, a `Position` DataFrame, and a `MarketPriceLookup` Protocol — none of which exist
in the omaha stack. Phase 1 (`asset-trade-flags`) shipped the per-asset trade-control columns that
the solver consumes as hard locks; Phase 2 closes the data-bridge gap so Phase 4 can drop the
CVXPY engine behind a route without re-shaping the ORM layer.

## What Changes

- **ADDED** new module `src/omaha/rebalance/` with three pure-function bridges:
  - `builders.build_setup_from_db(db, profile)` → `PortfolioSetup` (categories + assets DataFrames)
  - `builders.build_position_frame(db, profile)` → `Position` DataFrame (per-asset aggregation)
  - `quotes_adapter.OmahaMarketPriceLookup` implements the algorithm's `MarketPriceLookup` Protocol
    over `QuoteCache` + `Position.current_price` fallback
- **ADDED** `MarketPriceLookup` Protocol + helpers (`resolve_quote_symbol`, `build_empty_quote_frame`)
  as a thin port of the reference module so the engine can import the contract verbatim in Phase 4.
- **MODIFIED** `QuoteService._collect_symbols` to include `BRL=X` whenever any `Asset` with
  `currency_code = "USD"` exists, so USD assets have an FX rate available during rebalance.
- **ADDED** tests: `tests/test_rebalance_builders.py`, `tests/test_market_prices_adapter.py`.
  Follows the marker rule — new DB-hitting test prefixes go into `_INTEGRATION_PREFIXES`.

No model migrations. No UI changes. No new route. The endpoint and solver arrive in Phase 3 and
Phase 4 respectively (`rebalance-route`, `rebalance-engine`).

## Capabilities

### New Capabilities

- `rebalance-data-bridges` — Pure-function bridges that translate the omaha ORM (Profile →
  AssetClass → Asset → Position) into the data shapes the reference CVXPY solver expects.

### Modified Capabilities

None. Phase 1 (`asset-trade-flags`) defined the trade-control columns this phase consumes but
its requirements do not change.

## Impact

- **Code:** `src/omaha/rebalance/` (new, ~5 files), `src/omaha/quotes/service.py` (1 method body),
  `src/omaha/routes/pages.py` (extract `_compute_class_totals` private helper — external contract
  unchanged).
- **Dependencies:** pandas + numpy already present (Phase 4 will add cvxpy; this phase does not).
- **Tests:** `tests/test_rebalance_builders.py`, `tests/test_market_prices_adapter.py` (both
  integration markers; prefixes registered in `tests/conftest.py::_INTEGRATION_PREFIXES`).
- **Docs:** `.planning/REBALANCE_PLAN.md` updated to reflect the 5 design decisions captured in
  `design.md`.
