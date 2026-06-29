# Spec: rebalance-engine

## Purpose

Define the CVXPY rebalance solver that consumes the
`PortfolioSetup` + `Position` DataFrames produced by
`rebalance-data-bridges` and emits a `RebalancePlan` in the
native shape consumed by `rebalance-route`'s glue. This spec
is the engine's contract — `rebalance-route` plugs the
solver into its `solver` kwarg and `rebalance-page` renders
the result.

The engine is a 1:1 port of the reference algorithm at
`~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`
(1688 LOC, 41 functions, commit `ca867ba`), adapted to the
omaha module boundary (split across 5 submodules). No
algorithmic innovation; tolerances are literal (`1e-6`,
`1e-4`); unit mistakes are the #1 reference error and are
guarded by `test_rebalance_constants.py`.

## ADDED Requirements

### Requirement: Solver validates inputs and raises on failure

The system SHALL provide
`omaha.rebalance.validation._validate_rebalance_inputs(setup,
position, contribution)` that runs 11 checks and raises
`RebalanceValidationError(errors: list[str])` when any check
fails. The error message SHALL be the concatenation of all
failing checks separated by newlines (matching the
reference).

The 11 checks (per reference §7.1):

1. `contribution < 0` ⇒ "O aporte informado nao pode ser
   negativo."
2. `setup.categories.empty` ⇒ "O setup nao possui categorias
   carregadas."
3. `setup.assets.empty` ⇒ "O setup nao possui ativos
   carregados."
4. Sum of `target_weight` does not equal `1.0` within
   `ALLOCATION_TOLERANCE` ⇒ "Soma dos pesos-alvo difere de
   100%."
5. Position contains `asset_key` not in setup ⇒ list orphan
   keys.
6. Setup contains `asset_key` not in position AND
   `target_pct > 0` ⇒ list missing keys.
7. `current_value < 0` for any asset ⇒ list offending assets.
8. Duplicate `asset_key` in position ⇒ list duplicate keys.
9. `currency_code` not in `{"BRL", "USD"}` ⇒ list offending
   assets.
10. `target_pct < 0` for any asset ⇒ list offending assets.
11. `NaN` / `inf` in any numeric column ⇒ list offending
    rows.

`RebalanceValidationError` is already defined in
`omaha.rebalance.models` and is mapped to HTTP 400 by
`routes/rebalance.py` (per `rebalance-route` spec §"Error
mapping") and to inline `form_error` by `routes/pages.py`
(per `rebalance-page` spec §"Validation failure").

#### Scenario: Negative contribution rejects

- **WHEN** `simulate_rebalance` is called with
  `contribution = -1000.0` and otherwise valid setup +
  position
- **THEN** `RebalanceValidationError` raises with the
  message containing "O aporte informado nao pode ser
  negativo."

#### Scenario: Empty setup rejects

- **WHEN** `simulate_rebalance` is called with
  `setup.categories.empty == True`
- **THEN** `RebalanceValidationError` raises with the
  message containing "O setup nao possui categorias
  carregadas."

#### Scenario: Target weight sum mismatch rejects

- **WHEN** `simulate_rebalance` is called with a setup
  whose `target_weight.sum() != 1.0` within
  `ALLOCATION_TOLERANCE`
- **THEN** `RebalanceValidationError` raises with the
  message containing "Soma dos pesos-alvo difere de 100%."

#### Scenario: Multiple checks fail, all errors reported

- **WHEN** `simulate_rebalance` is called with a setup +
  position that violates 3 checks simultaneously
- **THEN** `RebalanceValidationError` raises with all 3
  error messages joined by newlines (the user sees every
  problem in one pass, not one-at-a-time).

### Requirement: Solver runs hierarchical 2-phase LP

The system SHALL implement
`omaha.rebalance.solver.simulate_rebalance(setup, position,
contribution, market_price_lookup=None) -> RebalancePlan`
that executes:

1. **Validation.** Call `_validate_rebalance_inputs`. Abort
   on `RebalanceValidationError`.
2. **Aggregation.** Call `_aggregate_position(position)` to
   roll up multiple `Position` rows per `asset_key` into one
   row.
3. **Simulation frame.** Call `_build_simulation_frame(
   setup, aggregated_position)` to produce the joined
   DataFrame carrying both setup (target) and position
   (current) values.
4. **Policy cascade.** Call `_solve_hierarchical_policy(
   simulation_frame, setup.categories, contribution)` to
   select one of 4 policy outcomes.
5. **Plan assembly.** Call `_build_rebalance_plan(
   simulation_frame, setup.categories, contribution,
   solution, market_price_lookup)` to emit the
   `RebalancePlan` native shape.

The public function signature matches the reference:
`simulate_rebalance(setup, position, contribution,
market_price_lookup=None)`. The glue shim
(`omaha.rebalance.engine.cvxpy_solver`) adapts this
signature to the glue-callable shape
`(setup, positions, quotes, contribution)`.

#### Scenario: Simple 2-asset profile rebalances successfully

- **WHEN** `simulate_rebalance` is called with
  `build_simple_setup` (1 class, 2 assets 50/50 BRL),
  `build_simple_position(5000.0, 5000.0)` (current values
  5000 / 5000), and `contribution = 1000.0`
- **THEN** the result is a `RebalancePlan` with status
  `optimal`, `asset_plan` length 2, `category_plan`
  length 1, `applied_policy == "contribution-only"` or
  `"contribution-with-overweight-sales"` (depending on
  whether the small rebalance is achievable without
  selling), and `residual_cash` ≤
  `contribution * CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE`.

#### Scenario: Italo portfolio with 48 assets solves in < 1s

- **WHEN** `simulate_rebalance` is called with the
  canonical Italo seed (6 classes, 48 assets, 47
  positions) and `contribution = 5000.0`
- **THEN** the result is a `RebalancePlan` with status
  `optimal` and the call returns in less than 1 second on
  the dev machine.

### Requirement: Phase 1 LP allocates contribution across categories

The system SHALL implement
`omaha.rebalance.solver._build_category_phase1_model(...)`
that builds a CVXPY problem with variables per category
(`delta_c`, `contrib_c`, `sell_c`, `buy_c`) and an
objective of weighted least-squares deviation from
category target values, subject to:

- Cash balance: `Σ_c contrib_c == contribution`.
- Sell funds buys: `Σ_c sell_c == Σ_c buy_c + residual_cash`.
- `projected_value[c] == current_value[c] + contrib_c -
  sell_c`.
- `delta_c == projected_value[c] - target_value[c]`.
- **RBRX11 B.2 fix:** if category is underweight
  (`current_value[c] < target_value[c] -
  DISPLAY_TOLERANCE`), then `delta_c >= 0` regardless of
  internal overweights.
- `sell_c <= category_sell_capacity[c]`.
- `buy_c <= category_buy_capacity[c]`.
- Zero target (`target_value[c] < ZERO_TARGET_VALUE_TOLERANCE`)
  forces `sell_c == 0` (no extraction from zero-target
  classes).

#### Scenario: Underweight category receives at least its delta

- **WHEN** `_build_category_phase1_model` runs against a
  profile with category B underweight (`current_value <
  target_value - DISPLAY_TOLERANCE`) and a positive
  `contribution`
- **THEN** the solved `delta_c[B] >= 0` (no extraction
  from the underweight class even if internal assets are
  over their intra-cat target).

### Requirement: Phase 2 LP distributes per-category deltas across assets

The system SHALL implement
`omaha.rebalance.solver._build_intra_category_model(...)`
that builds a CVXPY problem per category with variables
per asset (`buy_i`, `sell_i`) and an objective of
weighted least-squares deviation from asset target values,
subject to:

- Cash balance per category: `Σ_i buy_i == buy_c` and
  `Σ_i sell_i == sell_c`.
- `projected_value[i] == current_value[i] + buy_i -
  sell_i`.
- `buy_enabled[i] == False ⇒ buy_i == 0`.
- `sell_enabled[i] == False ⇒ sell_i == 0`.
- **RBRX11 B.1 fix:** if asset is at-or-below target AND
  `delta_c >= 0`, then `sell_i == 0` (no selling assets
  at target when the category is receiving capital).

After solving, `_solve_intra_category` SHALL enforce
minimum-trade thresholds in a post-loop: any
`|buy_i| < MIN_BUY_AMOUNT` is set to `0` and the LP is
re-solved. Same for sells.

#### Scenario: Asset at target is not sold when category receives capital

- **WHEN** `_build_intra_category_model` runs against a
  category with `delta_c > 0` containing an asset at
  exactly its target value
- **THEN** the solved `sell_i` for that asset is `0`
  (the B.1 fix prevents intra-category reallocation from
  selling on-target assets).

#### Scenario: Buy-enabled flag is a hard lock

- **WHEN** `_build_intra_category_model` runs against a
  category with `delta_c > 0` containing an asset with
  `buy_enabled = False`
- **THEN** the solved `buy_i` for that asset is `0`
  regardless of how much capital the category has to
  deploy.

#### Scenario: Min-trade threshold enforced iteratively

- **WHEN** `_solve_intra_category` solves and produces a
  `buy_i` with `0 < buy_i < MIN_BUY_AMOUNT`
- **THEN** the loop sets `buy_i = 0`, re-solves the LP
  with the additional constraint, and repeats until all
  buy amounts are either `0` or `≥ MIN_BUY_AMOUNT`.

### Requirement: Policy cascade selects one of four outcomes

The system SHALL implement
`omaha.rebalance.policy._solve_hierarchical_policy(...)`
that attempts 4 policies in order, returning the first
that passes its acceptance criteria:

1. **`"contribution-only"`** — solve with `sell = 0` for
   all assets. Pass if all four contribution-only
   criteria hold:
   - Per-asset deviation: max
     `|projected_weight[i] - target_weight[i]| <
     CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE`.
   - Per-category deviation: max
     `|projected_weight[c] - target_weight[c]| <
     CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE`.
   - Residual cash share: `residual_cash / contribution <
     CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE` (or
     `residual_cash == 0` if contribution is 0).
   - Top asset gap: largest single asset deviation below
     `CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE`.
   - Top category gap: largest single category deviation
     below `CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE`.

2. **`"contribution-with-overweight-sales"`** — relax the
   `sell = 0` constraint to allow selling assets above
   target (`_build_overweight_sell_mask`). Pass if the
   solution's `current_deviation_pct` improves by at
   least `STAGED_SALES_MIN_CATEGORY_IMPROVEMENT` (5%)
   over the contribution-only baseline.

3. **`"contribution-with-full-sales"`** — relax further to
   allow any sell-enabled asset to be sold. Pass if the
   solution's `current_deviation_pct` improves by at
   least `STAGED_SALES_MIN_CATEGORY_IMPROVEMENT` over
   the overweight-sales stage.

4. **`"current-portfolio-rebalance"`** — fallback when
   `contribution == 0` and no policy can avoid selling.
   Equivalent to "full-sales with zero contribution".

Each stage's rejection reason is captured in
`_build_stage_rejection_reason(stage, metrics)` for
debugging.

#### Scenario: Balanced portfolio uses contribution-only

- **WHEN** `_solve_hierarchical_policy` runs against a
  profile with `current_value` close to target (small
  drift, well within
  `CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE`) and a
  modest `contribution`
- **THEN** `applied_policy == "contribution-only"`.

#### Scenario: Overweight profile falls to overweight-sales

- **WHEN** `_solve_hierarchical_policy` runs against a
  profile with `current_value` overweight on at least
  one category AND `contribution == 0`
- **THEN** the contribution-only stage is rejected
  (cannot rebalance without selling) AND the
  overweight-sales stage passes AND
  `applied_policy == "contribution-with-overweight-sales"`.

### Requirement: Output shape — 31-col asset_plan, 13-col category_plan, ~28-key metrics

The system SHALL emit a `RebalancePlan` with:

- `asset_plan` — DataFrame, one row per asset in setup,
  31 columns (reference §3.2). The v1 wire format
  (`rebalance-route` spec) consumes a subset of 9 fields;
  the remaining 22 are exposed for future wire-format
  expansion.
- `category_plan` — DataFrame, one row per category, 13
  columns (reference §3.3). Wire subset is 4 fields.
- `metrics` — dict, ~28 keys (reference §3.4). Wire
  subset is 6 keys (`contribution`, `total_buy`,
  `total_sell`, `residual_cash`, `current_deviation_pct`,
  `projected_deviation_pct`).
- `warnings` — tuple of strings. Wire format wraps each
  in a `RebalanceWarning(code, message)` object.
- `applied_policy` — string ∈
  `{"contribution-only", "contribution-with-overweight-
  sales", "contribution-with-full-sales",
  "current-portfolio-rebalance"}`.

The native shape is the reference's
`RebalancePlan(asset_plan, category_plan, metrics,
warnings)` dataclass. The omaha glue shim wraps this in
the v1 wire format unchanged.

#### Scenario: Output has the documented shape

- **WHEN** `simulate_rebalance` returns against a
  populated profile
- **THEN** `asset_plan` has shape `(N_assets, 31)`,
  `category_plan` has shape `(N_categories, 13)`,
  `metrics` is a dict with at minimum the 6 v1 keys,
  `warnings` is a tuple (possibly empty), and
  `applied_policy` is one of the 4 policy strings.

### Requirement: Solver is deterministic on the same input

The system SHALL use CLARABEL as the primary CVXPY solver
with SCS as the fallback (`_run_problem` tries CLARABEL
first, falls back to SCS on `SolverError`). Same problem
formulation + same CVXPY version SHALL produce the same
output within `1e-4` absolute tolerance on monetary
values.

The stub fixture (`tests/fixtures/rebalance_stub_fixture.json`)
serves as the golden regression baseline. The engine
regression test
(`test_engine_matches_stub_fixture`) constructs the
canonical 2-class / 5-asset inputs that produce the
fixture's output and asserts the real solver matches
within tolerance.

#### Scenario: Repeated runs produce identical output

- **WHEN** `simulate_rebalance` is called twice with the
  same `(setup, position, contribution,
  market_price_lookup)` arguments in the same Python
  process
- **THEN** the two `RebalancePlan` outputs are
  byte-equivalent (same status, same per-asset values,
  same policy, same warnings).

#### Scenario: Real solver matches stub fixture on canonical input

- **WHEN** `simulate_rebalance` runs against the inputs
  that produce the stub fixture's
  `(contribution=1000.0, 2 classes, 5 assets)` plan
- **THEN** the real solver's output matches the fixture
  within `1e-4` abs on every monetary field.

### Requirement: Engine respects asset trade-control flags as hard locks

The system SHALL treat `Asset.buy_enabled` and
`Asset.sell_enabled` as hard locks in the Phase 2 LP:

- `buy_enabled == False ⇒ buy_i == 0` for that asset.
- `sell_enabled == False ⇒ sell_i == 0` for that asset.
- No path through the cascade overrides these locks.
- An asset with both flags `False` keeps its current
  value unchanged in the plan (`buy_amount == 0`,
  `sell_amount == 0`, `projected_value == current_value`).

These flags were added in `asset-trade-flags` (Phase 1,
archived 2026-06-26) as a conservative default — assets
imported from broker CSVs start with both flags `False`
and require explicit operator opt-in.

#### Scenario: Asset with both flags off is locked

- **WHEN** `simulate_rebalance` runs against a profile
  containing an asset with `buy_enabled = False` AND
  `sell_enabled = False`, regardless of contribution
- **THEN** the asset's `buy_amount == 0`,
  `sell_amount == 0`, and `projected_value ==
  current_value` (within `DISPLAY_TOLERANCE`).

### Requirement: Empty class with non-zero target produces a warning, not an error

The system SHALL accept a setup with a category that has
`target_pct > 0` but zero assets (the bridge emits a
warning but does not error — see
`rebalance-data-bridges` Decision 7). The solver SHALL
run as normal, allocating `delta_c` to the empty class in
Phase 1, but Phase 2 has no assets to distribute across,
so the allocation lands as `residual_cash`.

The plan SHALL emit a second warning `"Classe X recebeu
R$ Y de aporte mas nao possui ativos para alocar"`
whenever `residual_cash > MIN_BUY_AMOUNT` AND the
residual is attributable to an empty class.

#### Scenario: Empty class with target > 0 produces residual

- **WHEN** `simulate_rebalance` runs against a profile
  where class C has `target_pct = 20` but zero assets, AND
  `contribution = 10000.0`
- **THEN** the plan's `residual_cash >= 0` (some
  fraction of the contribution cannot be deployed) AND
  `warnings` contains a message referencing class C AND
  the empty-class warning.

### Requirement: RBRX11 regressions are guarded by coupled tests

The system SHALL pass two regression tests ported from
reference Apêndice B. The two tests cover coupled bugs
in Phase 1 + Phase 2 and SHALL be ported together in the
same change to keep the fixes coupled.

The two regressions:

- **B.1** — Phase 2 must not sell an asset at its global
  target when the category is receiving capital.
- **B.2** — Phase 1 must not drain an underweight category
  even when internal assets are over their intra-cat
  targets.

#### Scenario: B.1 — Asset at target not sold when category receives capital

- **WHEN** `simulate_rebalance` runs against
  `build_category_first_setup` +
  `build_category_first_position` with
  `contribution = 7000.0`
- **THEN** `sell_amount(FII-A) == pytest.approx(0.0,
  abs=1e-4)` AND `sell_amount(FII-B) ==
  pytest.approx(0.0, abs=1e-4)` AND
  `projected_value(FII-A) >= current_value(FII-A) -
  1.0`.

#### Scenario: B.2 — Underweight category not drained even with internal overweights

- **WHEN** `simulate_rebalance` runs against
  `build_category_first_setup` +
  `build_category_first_position`
- **THEN** `sell_amount(B1) == pytest.approx(0.0,
  abs=1e-4)` (B1 is underweight within category B, even
  if other internal positions exist) AND
  `projected_value_total(B) >= current_value_total(B) -
  1.0` (category B does not lose net capital).

### Requirement: Engine defaults replace the stub in the glue

The system SHALL change `omaha.rebalance.glue.run_rebalance`
to default `solver = cvxpy_solver` (the engine shim from
`omaha.rebalance.engine`) instead of `stub_solver`. The
`solver` kwarg remains overridable for tests that want
deterministic stub output.

The stub module (`omaha.rebalance.solver_stub`) and its
fixture (`tests/fixtures/rebalance_stub_fixture.json`)
SHALL remain in the tree as a regression baseline and a
deterministic test fallback. They are NOT deleted by this
change.

The page template
(`src/omaha/templates/_rebalance_plan.html`) already
gates the stub banner on
`plan.applied_policy == "stub-fixture-v1"`. Once the
real engine ships, the banner never renders because the
real engine returns one of the 4 reference policy
strings, never `"stub-fixture-v1"`. No template edit is
required for the banner to disappear.

#### Scenario: Glue default uses the real engine

- **WHEN** `omaha.rebalance.glue.run_rebalance(db,
  profile, contribution)` is called without an explicit
  `solver` kwarg
- **THEN** the function dispatches to `cvxpy_solver`
  (which calls `simulate_rebalance`), NOT to
  `stub_solver`.

#### Scenario: Stub banner does not render with real engine

- **WHEN** `POST /api/rebalance` is called with a valid
  contribution and the real engine returns a plan
- **THEN** the rendered HTML does NOT contain
  `data-testid="rebalance-stub-banner"` (the banner is
  conditional on `applied_policy == "stub-fixture-v1"`).

#### Scenario: Test can override solver back to stub

- **WHEN** a test calls `run_rebalance(db, profile,
  contribution, *, solver=stub_solver)` explicitly
- **THEN** the glue dispatches to `stub_solver` (the
  override works; backward compat preserved).