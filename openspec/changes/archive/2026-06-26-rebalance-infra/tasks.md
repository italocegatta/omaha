# Tasks: rebalance-infra

## 1. Module skeleton

- [x] 1.1 Create `src/omaha/rebalance/__init__.py` with public exports (`build_setup_from_db`,
      `build_position_frame`, `OmahaMarketPriceLookup`, `PortfolioSetup`, `RebalanceValidationError` placeholder)
- [x] 1.2 Add `pandas` to the runtime `dependencies` list in `pyproject.toml` if not present
      (verify with `uv run python -c "import pandas"`); do **not** add `cvxpy` yet (Phase 4)

## 2. PortfolioSetup + Position builders

- [x] 2.1 Implement `rebalance/builders.py::build_setup_from_db(db, profile) -> tuple[PortfolioSetup, list[str]]`
      returning `(PortfolioSetup, warnings)` (warnings list captures Decision 1 + Decision 4)
- [x] 2.2 Implement `rebalance/builders.py::build_position_frame(db, profile) -> pd.DataFrame`
      with the schema from spec §"Position builder aggregates per-asset holdings"
- [x] 2.3 Convert `Decimal` → `float` once at the builder boundary (not per-cell loop) to keep
      CVXPY-friendly precision; document tolerance (`1e-6`)
- [x] 2.4 Re-number `category_order` / `asset_order` to `0..N-1` regardless of `display_order`
      gaps (Decision: re-number defensively to avoid solver index confusion)

## 3. MarketPriceLookup port

- [x] 3.1 Copy `resolve_quote_symbol`, `build_empty_quote_frame`, `QuoteSnapshot`,
      `is_queryable_quote_symbol`, `_resolve_quote_status` from
      `~/github/investing/src/portfolio_rebalancing/domain/market_prices.py` into
      `src/omaha/rebalance/market_prices.py`; replace import paths to omaha-relative
- [x] 3.2 Define `MarketPriceLookup` Protocol (`get_quotes(assets: DataFrame) -> DataFrame`)
      and `NoopMarketPriceLookup` in `rebalance/market_prices.py`
- [x] 3.3 Define `PortfolioSetup` dataclass in `rebalance/models.py` matching the reference
      (`categories: pd.DataFrame, assets: pd.DataFrame`) — frozen

## 4. OmahaMarketPriceLookup adapter

- [x] 4.1 Implement `OmahaMarketPriceLookup(cache: QuoteCache, db: Session)` in
      `rebalance/quotes_adapter.py` per spec §"OmahaMarketPriceLookup satisfies the Protocol"
- [x] 4.2 Build the empty quote frame via `build_empty_quote_frame(assets, status="unavailable")`
      and populate it row-by-row: BRL assets query `cache.get_many([symbol + ".SA"])`;
      USD assets query `[symbol, "BRL=X"]` and resolve `usdbrl_rate` from the BRL=X row
- [x] 4.3 For `quote_kind ∈ {none, manual}`, query `Position` for the asset's first
      `Position.current_price` (by `id` ASC); if none, `quote_price = 0.0`, `status = "not-requested"`
- [x] 4.4 Apply the status decision: `available` if fresh + (USD requires fresh `BRL=X`);
      `not-requested` if `quote_kind ∈ {none, manual}`; otherwise `unavailable`

## 5. QuoteService BRL=X injection

- [x] 5.1 Extend `QuoteService._collect_symbols` (`src/omaha/quotes/service.py:167`) to query
      `select(Asset.currency_code).where(Asset.currency_code == "USD").limit(1)` and append
      `"BRL=X"` to the returned list when at least one row matches
- [x] 5.2 Verify the existing `test_quote_service.py` still passes — `BRL=X` only appears when
      USD assets exist, which the existing fixtures do not seed

## 6. portfolio_aggregates refactor (private helper only)

- [x] 6.1 Extract `_compute_class_totals(assets: list[Asset]) -> dict` private helper inside
      `routes/pages.py`; contains the per-asset qty/invested/current summing loop
- [x] 6.2 Refactor `portfolio_aggregates` to call the helper without changing its external
      return shape (Dict with `portfolio` + `classes` keys)
- [x] 6.3 Verify `audit/inventory.py:155`, `test_pages_routes.py`, `test_real_csv_flow.py:662`,
      `test_seed_from_csv.py:465` continue to pass against the refactored helper

## 7. Tests

- [x] 7.1 Create `tests/test_rebalance_builders.py` with scenarios from
      spec §"PortfolioSetup builder" + §"Position builder" + §"Empty class warning":
      - happy-path 3-class/5-asset profile (target sums to 1.0)
      - empty profile returns empty DataFrames with full schema
      - asset name cross-class collision triggers warning + groupby dedup
      - empty class with non-zero target emits warning
      - empty class with target=0 does not warn
      - asset with 3 positions aggregates totals correctly
      - asset with 0 positions yields zero totals + zero weight
      - empty portfolio produces zero current_weight per asset (not NaN)
- [x] 7.2 Add `tests/test_rebalance_builders.py` prefix to `_INTEGRATION_PREFIXES` in
      `tests/conftest.py` (DB-hitting fixtures)
- [x] 7.3 Create `tests/test_market_prices_adapter.py` covering spec §"Quote symbol resolution":
      - `resolve_quote_symbol("PETR4", "BRL")` → `"PETR4.SA"`
      - already-suffixed idempotent
      - USD ticker not suffixed
      - empty name returns empty
- [x] 7.4 Add `tests/test_market_prices_adapter.py` covering spec §"OmahaMarketPriceLookup":
      - auto BRL with fresh cache → `available`
      - auto BRL with stale cache → `unavailable`
      - none-class falls back to `Position.current_price` → `not-requested`
      - USD asset with fresh `BRL=X` → `usdbrl_rate` populated, status `available`
      - USD asset with missing `BRL=X` → `unavailable` regardless of own quote
      - asset with zero `Position` rows → `quote_price = 0.0`, `not-requested`
- [x] 7.5 Add `tests/test_market_prices_adapter.py` prefix to `_INTEGRATION_PREFIXES`
- [x] 7.6 Cover spec §"QuoteService BRL=X injection":
      - one USD asset in DB → symbol list contains `BRL=X`
      - zero USD assets → symbol list unchanged

## 8. Validate + document

- [x] 8.1 Run `openspec validate rebalance-infra` and resolve any schema warnings
- [x] 8.2 Run `uv run task test-unit && uv run task test-integration` — all green
- [x] 8.3 Run `uv run task lint` (prek + ruff)
- [x] 8.4 Update `.planning/REBALANCE_PLAN.md` Decision 1-5 sections to reflect the
      resolutions captured in `design.md` (so the planning doc stays in sync with the change)
