# Design: rebalance-infra

## Context

The reference algorithm (`~/github/investing/src/portfolio_rebalancing/domain/`) expects three
inputs that don't exist in omaha:

1. `PortfolioSetup{categories: DataFrame, assets: DataFrame}` — categories with `target_weight` ∈
   [0,1] and assets with `target_weight` + `target_weight_in_category` + `buy_enabled` +
   `sell_enabled` + `currency_code`. The omaha ORM stores `target_pct` ∈ [0,100] and uses
   related-object traversal, not DataFrames.
2. `Position` DataFrame — per-asset aggregation of `qty`, `total_invested`, `total_current`,
   `current_weight`. `routes/pages.py::portfolio_aggregates` computes the same numbers but
   returns a nested Dict for the dashboard template, not a flat DataFrame.
3. `MarketPriceLookup` Protocol — `get_quotes(assets: DataFrame) -> DataFrame` with columns
   `asset_key, quote_symbol, quote_price, quote_currency, quote_timestamp, quote_status,
   usdbrl_rate`. `QuoteCache.get_many` is keyed by symbol and returns `QuoteWithFreshness`
   rows, not a frame.

Phase 1 (`asset-trade-flags`) shipped `buy_enabled`, `sell_enabled`, `currency_code` on `Asset`,
plus `USD` on the `currency_code` allowlist. This phase consumes those columns and builds the
data bridges; the route and the CVXPY engine arrive in Phase 3 (`rebalance-route`) and Phase 4
(`rebalance-engine`).

Stakeholders: Italo (operator, runs rebalance from dashboard), Ana Livia (viewer, reviews
results). Single-user household deployment — concurrency is not a design constraint.

## Goals / Non-Goals

**Goals:**
- Pure-function builders that take a pre-loaded `Profile` and return DataFrames matching the
  reference algorithm's expected schema (plus one omaha-specific column `quote_kind`).
- `OmahaMarketPriceLookup` that satisfies the `MarketPriceLookup` Protocol over the existing
  `QuoteCache` + `Position.current_price` fallback.
- USD assets resolve `BRL=X` via the existing `QuoteCache` (no live yfinance call during request).
- Five design decisions captured from the explore session, each with rationale.

**Non-Goals:**
- CVXPY solver, optimization, policy cascade — Phase 4 (`rebalance-engine`).
- HTTP route, request/response schemas — Phase 3 (`rebalance-route`).
- Dashboard UI (modal de aporte, results table) — Phase 5 (`rebalance-results`).
- Schema migration for cross-class asset name uniqueness — see Decision 1 (deferred).
- Concurrency control on `POST /api/rebalance` — single-user app, serial by design.

## Decisions

### Decision 1: `asset_key` cross-class collision handled by silent groupby + warning

The algorithm's `_validate_rebalance_inputs` rejects duplicated `asset_key` (line 123 of the
reference). The omaha schema permits the same `Asset.name` across two `AssetClass` rows under
the same `Profile` (`UniqueConstraint("asset_class_id", "name")` is intra-class only). Three
options were considered:

- **(A) Groupby first** (`groupby("asset_key").first()`) + emit warning per collision in the
  response. *Adopted.* Zero migration, matches reference behavior. Trade-off: dashboard shows
  both rows but solver treats them as one — the response carries the warning so the operator
  sees which rows were shadowed.
- (B) New Alembic migration adding `UniqueConstraint("profile_id", "name")`. Defers Phase 2
  scope (requires a data-audit pass to resolve existing duplicates before applying).
- (C) Builder raises and the route returns 400. Bad UX — the operator finds out after the
  entire dataset is loaded.

### Decision 2: `BRL=X` is injected into the `QuoteService` symbol list, not into the request path

USD assets need `BRL=X` available in `QuoteCache` for the solver's `usdbrl_rate` column. Three
options:

- **(A) Extend `QuoteService._collect_symbols`** to append `BRL=X` whenever any
  `Asset.currency_code == "USD"` exists in the DB. *Adopted.* Cache stays warm, request latency
  unchanged.
- (B) Adapter triggers `QuoteService.refresh_once()` before `get_many`. Adds 1–5s latency to
  `POST /api/rebalance` (yfinance HTTP call); race-prone under rapid clicking.
- (C) v1 ignores FX conversion. **Mathematically wrong** — sums USD + BRL as one basket, breaks
  `gain_pct` and `total_current_value`. Deferred indefinitely as it would corrupt the
  portfolio totals.

### Decision 3: Builder emits a `quote_kind` column; solver ignores unknown columns

`AssetClass.quote_kind` controls whether to fetch live quotes (`auto`) or use `Position.current_price`
(`none`/`manual`). The adapter needs this to decide the fallback strategy, but the algorithm's
`assets` DataFrame doesn't carry it.

- **(A) Builder joins `quote_kind` from `AssetClass` into the `assets` DataFrame.** *Adopted.*
  Single source of truth; `get_quotes(assets)` is the only signature.
- (B) Adapter receives a separate `dict[asset_key, quote_kind]`. Caller manages two structures.
- (C) Adapter queries DB internally. Breaks pure-function contract; tests become integration
  tests.

The omaha `assets` DataFrame is a **super-set** of the reference: same 10 columns + `quote_kind`.
CVXPY reads only named variables, so extra columns are inert.

### Decision 4: Empty class with `target_pct > 0` emits a warning, not an error

A class with no assets but non-zero target allocates cash in Phase 1 that Phase 2 cannot absorb
(solver returns the unspent amount as `residual_cash`).

- **(A) Builder emits a warning string per empty class; solver runs.** *Adopted.* Modal can
  surface the warning; operator decides whether to add assets or zero the target.
- (B) Builder raises and the route returns 400. Frustrating for operators planning ahead
  (target set before assets added).
- (C) Builder silently drops the empty class. `_validate_rebalance_inputs` then fails the
  sum-to-100 check with an ambiguous error message.

### Decision 5: `portfolio_aggregates` refactor is private, contract-preserving

`portfolio_aggregates` is consumed by the dashboard template, `audit/inventory.py:155`, and
three test files (`test_pages_routes.py`, `test_real_csv_flow.py`, `test_seed_from_csv.py`).
Sharing aggregation with the rebalance builders risks breaking the audit pipeline silently.

- **(A) Extract `_compute_class_totals(assets)` as a private helper** in `routes/pages.py`. The
  rebalance builders do **not** import it — they re-implement the same Decimal-summing logic
  (~20 lines) but in `rebalance/builders.py`. *Adopted.* ~20 lines of deliberate duplication
  is cheaper than risking the audit pipeline.
- (B) Duplicate aggregation in the builders, no `portfolio_aggregates` refactor. Drift risk.
- (C) Full refactor with pure shared functions. Highest blast radius — three test files plus
  audit would need parallel updates.

The duplication mirrors the existing `broker-csv-import-totals` rule in
`routes/pages.py:212-217`: sum the broker-published totals directly, never recompute
`qty * price`. Both call sites follow the rule independently.

## Risks / Trade-offs

- **`asset_key` shadowing** (Decision 1) → Warning text in response + dedicated dashboard badge
  on shadowed classes (Phase 5). Until Phase 5 ships, the warning only surfaces in the
  rebalance response modal.
- **Stale `BRL=X`** (Decision 2) → `QuoteCache` already TTL's quotes (default 15 min); the FX
  rate can be up to 15 min stale during a rebalance. Acceptable for family-portfolio use;
  documented in the modal as "Cotação de HH:MM".
- **Decimal → float precision** at the builder boundary → Conversion happens once on
  `total_current_value` and `total_invested_value` per asset, not on a per-cell loop. Solver
  tolerances (`1e-6` ALLOCATION_TOLERANCE) absorb the float drift.
- **Pure-function contract on `OmahaMarketPriceLookup`** — the reference's Protocol takes a
  `DataFrame` and returns a `DataFrame`. We honor the signature, but the adapter *internally*
  calls `QuoteCache.get_many` (DB read). The builder pre-loads the assets DataFrame; the
  adapter is DB-touching on a per-call basis. Marked `@integration` in tests.
- **Eager loading convention** — builders require `AssetClass.assets.selectinload(Asset.positions)`
  to be applied by the caller. Phase 3 route follows the same pattern as `pages.py:99-107`.
  Documented in builder docstrings.

## Migration Plan

No data migration. No schema change. No backward-incompatible behavior change.

- `QuoteService._collect_symbols` change is behavior-additive: symbols list grows by `≤1`
  entry. No existing quote keys change.
- New module `src/omaha/rebalance/` is purely additive.
- `portfolio_aggregates` refactor preserves external contract; existing dashboard tests
  pass unchanged.

Rollback: delete `src/omaha/rebalance/`, revert `QuoteService._collect_symbols`. No DB state
to undo.

## Open Questions

- **Phase 4 dependency timing.** Should `cvxpy` be added to `pyproject.toml` in Phase 2 (so
  integration tests can import the solver module under test even if it doesn't run), or only
  in Phase 4? *Recommendation:* Phase 4 — Phase 2 doesn't import cvxpy, and the install size
  (~50 MB with CLARABEL + SCS) is better deferred until actually needed.
- **Cross-class asset name uniqueness.** Decision 1 sidesteps this. If operator feedback
  shows shadowing is a real problem, a future migration could enforce the constraint. Not
  blocking for Phase 2.
