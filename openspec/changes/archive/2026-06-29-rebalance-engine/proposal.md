# Change: rebalance-engine

## Why

Four OpenSpec changes already shipped the rebalance pipeline
end-to-end against a frozen JSON fixture:

- `asset-trade-flags` (Phase 1, archived 2026-06-26) — model +
  migration + UI for per-asset `buy_enabled` / `sell_enabled` /
  `currency_code`.
- `rebalance-infra` (Phase 2, archived 2026-06-26) — pure-function
  bridges (`build_setup_from_db`, `build_position_frame`) +
  `MarketPriceLookup` adapter over `QuoteCache`.
- `rebalance-route` (Phase 3a, archived 2026-06-27) — `POST
  /api/rebalance`, Pydantic wire schemas, glue orchestration
  (`run_rebalance(..., *, solver=None)`), deterministic solver
  stub backed by `tests/fixtures/rebalance_stub_fixture.json`.
- `rebalance-page` (Phase 3b, archived 2026-06-27) — `/rebalance`
  page, sidebar form, 6 metric cards, asset/category tables,
  warnings panel, stub banner that says "solver CVXPY chegará em
  [Phase 4]".

The glue takes the solver as a kwarg and defaults to the stub.
The page renders the stub fixture output (a 2-class / 5-asset
toy portfolio). The operator submits the form, sees a frozen plan
that does not match their real portfolio, and reads the banner
explaining the solver has not landed yet.

This change ports the real CVXPY solver from
`~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`
(1688 lines, 41 functions, hierarchical 2-phase LP + policy cascade
+ post-processing) into `src/omaha/rebalance/`, swaps the glue's
default solver from the stub to the real one, and removes the
stub banner from the rendered page. After this change the
operator's aporte produces a real plan derived from their actual
`AssetClass` / `Asset` / `Position` rows.

## What Changes

### New solver modules under `src/omaha/rebalance/`

- **ADDED** `src/omaha/rebalance/constants.py` (~50 LOC). Literal
  transcription of the constants in §4 of
  `~/github/investing/docs/portfolio-rebalance-algorithm-reference.md`:
  `ALLOCATION_TOLERANCE = 1e-6`, `DISPLAY_TOLERANCE = 1e-4`,
  `PRIORITIZED_ASSET_GAP_COUNT = 5`,
  `PRIORITIZED_CATEGORY_GAP_COUNT = 2`,
  `SHORTFALL_RELATIVE_FLOOR_VALUE = 100.0`,
  `MIN_BUY_AMOUNT = 1_000.0`, `MIN_SELL_AMOUNT = 1_000.0`,
  `LOT_SIZE = None`, `REQUIRES_INTEGER_QUANTITIES = False`,
  the contribution-only thresholds (`*_TOLERANCE`,
  `*_MAX_RESIDUAL_CASH_SHARE`, `*_GAP_TOLERANCE`), the staged
  sales thresholds (`STAGED_SALES_*`), and the policy-name string
  constants (`CONTRIBUTION_ONLY_POLICY`,
  `OVERWEIGHT_SALES_POLICY`, `FULL_SALES_POLICY`,
  `CURRENT_PORTFOLIO_REBALANCE_POLICY`).
- **ADDED** `src/omaha/rebalance/validation.py` (~120 LOC).
  `_validate_rebalance_inputs(setup, position, contribution)` —
  the 11-check validator from §7.1 of the reference. Raises
  `RebalanceValidationError(errors)` (already defined in
  `models.py`, raised from the solver, mapped to HTTP 400 by
  `routes/rebalance.py` and to inline `form_error` by
  `routes/pages.py`).
- **ADDED** `src/omaha/rebalance/solver.py` (~600 LOC).
  CVXPY Phase 1 LP (`_build_category_phase1_model`,
  `_solve_category_phase1`), Phase 2 LP
  (`_build_intra_category_model`, `_solve_intra_category` with
  min-trade enforcement loop), helpers
  (`_aggregate_position`, `_build_simulation_frame`,
  `_build_optimizer_parameters`, `_run_problem`,
  `_clip_solution`). Public entry point
  `simulate_rebalance(setup, position, contribution,
  market_price_lookup=None)` mirrors the reference signature.
- **ADDED** `src/omaha/rebalance/policy.py` (~400 LOC).
  `_solve_hierarchical_policy`, `_solve_contribution_only_rebalance`,
  `_evaluate_contribution_only_solution`,
  `_evaluate_progressive_sales_stage_solution`,
  `_build_zero_target_sell_mask`, `_build_overweight_sell_mask`,
  `_build_overweight_projected_value_floor`,
  `_build_contribution_only_rejection_reason`,
  `_build_stage_rejection_reason`. Implements the cascade:
  `contribution-only` → `contribution-with-overweight-sales` →
  `contribution-with-full-sales` → `current-portfolio-rebalance`.
- **ADDED** `src/omaha/rebalance/postprocessing.py` (~300 LOC).
  `_build_rebalance_plan`, `_build_category_plan`,
  `_build_plan_metrics`, `_build_plan_warnings`,
  `_clamp_projected_values_to_target_side`,
  `_reduce_buy_overspend`, `_build_restriction_note`,
  `_enrich_asset_plan_with_market_data`,
  `_collect_solution_metrics`, `_calculate_solution_deviations`,
  `_calculate_solution_top_gaps`, `_sum_largest_values`,
  `_relative_improvement`. Builds the 31-column `asset_plan`,
  13-column `category_plan`, ~28-key `metrics`, and `warnings`
  tuple in the reference's native shape.
- **ADDED** `src/omaha/rebalance/engine.py` (~30 LOC). Thin
  shim that re-exports `simulate_rebalance` as
  `cvxpy_solver(setup, positions, quotes, contribution)` — the
  glue-compatible callable signature (matches
  `stub_solver`'s shape). Internal — not part of the public
  module surface.

### Glue + page integration

- **MODIFIED** `src/omaha/rebalance/glue.py`: 1-line change.
  Default `solver=None` resolves to `cvxpy_solver` instead of
  `stub_solver`. The `solver` kwarg remains overridable for
  tests. The `RebalancePlan` shape returned by the real solver
  matches the stub's native dataclasses so the existing
  translation loop needs zero changes.
- **MODIFIED** `src/omaha/templates/_rebalance_plan.html`: the
  stub banner (`{% if plan.applied_policy == "stub-fixture-v1"
  %}<details class="rebalance-stub-banner">...`) becomes inert
  the moment the real solver ships (it never returns
  `stub-fixture-v1`). No template edit strictly required, but
  the banner CSS in `app.css` stays in case we need to surface
  a "using stub" indicator in any test fixture.

### Dependencies

- **MODIFIED** `pyproject.toml`: add `cvxpy>=1.5,<2` to
  `dependencies`. CLARABEL ships as the default solver in
  CVXPY ≥ 1.4; SCS is the bundled fallback. Install size grows
  by ~50 MB (already noted as Phase 4 risk in this roadmap).
- **MODIFIED** `uv.lock`: regenerated by `uv sync`.

### Test infrastructure

- **ADDED** `tests/fixtures/rebalance_engine/` directory with
  the Apêndice D fixtures ported from
  `~/github/investing/tests/conftest.py` and
  `tests/test_rebalancing.py`:
  - `build_simple_setup()` — 1 class, 2 assets 50/50 BRL.
  - `build_simple_position(asset_a_value, asset_b_value)` —
    matching 2-asset position.
  - `build_simple_quote_frame()` — 2 BRL quotes
    `quote_status="available"`.
  - `StubMarketPriceLookup(quotes)` — Protocol stub that
    `left join`s on `asset_key`.
  - `build_zero_target_setup()` — 1 class, 2 assets; A target
    0 with `buy_enabled=False, sell_enabled=True`; B target 1.0.
  - `build_weighted_setup(weights)` /
    `build_weighted_position(values)` — N assets with custom
    weights.
  - `build_two_category_setup()` /
    `build_two_category_position(...)` — 2 classes 60/40, 1
    asset each.
  - `build_category_first_setup()` /
    `build_category_first_position()` — 2 classes 50/50; A
    has 1 asset, B has 2 assets 50/50 intra; B1 concentrated
    above intra-cat target.
- **ADDED** `tests/test_rebalance_constants.py` (unit, no DB).
  Asserts every constant from `constants.py` matches the value
  in §4 of the reference (transcription regression guard).
- **ADDED** `tests/test_rebalance_validation.py` (unit, no DB).
  11 scenarios, one per check in §7.1. Each constructs a setup
  + position that violates exactly one check and asserts
  `RebalanceValidationError` raises with the expected error
  message fragment.
- **ADDED** `tests/test_rebalance_solver.py` (unit, no DB).
  Phase 1 + Phase 2 LP smoke tests against
  `build_simple_setup`. Asserts LP status `optimal`,
  `delta_c.sum()` matches the expected contribution allocation,
  intra-cat weights sum to 1 per category.
- **ADDED** `tests/test_rebalance_policy.py` (unit, no DB).
  4 scenarios, one per policy cascade outcome:
  `contribution-only` (well-funded profile + small aporte),
  `contribution-with-overweight-sales` (need to rebalance
  overweights but no underweights need buying), `contribution-
  with-full-sales` (need full reallocation including selling
  underweights), `current-portfolio-rebalance` (no aporte,
  full reallocation).
- **ADDED** `tests/test_rebalance_postprocessing.py` (unit, no
  DB). Asserts `_build_plan_metrics` emits the ~28-key dict;
  `_build_rebalance_plan` emits a 31-col `asset_plan` and 13-col
  `category_plan`; warnings propagation matches reference's
  tuple-of-strings shape.
- **ADDED** `tests/test_rebalance_engine_regression.py` (unit,
  no DB). The two coupled RBRX11 regressions from Apêndice B,
  ported JUNTOS:
  - `test_phase2_does_not_sell_asset_at_target_when_category_receives_contribution`
    — `build_category_first_setup`, assert `sell_amount(FII-A) ==
    pytest.approx(0.0, abs=1e-4)`, `sell_amount(FII-B) ==
    pytest.approx(0.0, abs=1e-4)`, `projected_value(FII-A) >=
    current_value(FII-A) - 1.0`.
  - `test_phase1_does_not_drain_underweight_category_even_when_it_has_overweight_assets`
    — `build_category_first_position`, assert
    `sell_amount(B1) == pytest.approx(0.0, abs=1e-4)`,
    `projected_value_total(B) >= current_value_total(B) - 1.0`.
- **ADDED** `tests/test_rebalance_engine_glue.py` (integration).
  Builds the canonical Italo profile via the existing factories,
  calls `run_rebalance(db, profile, contribution=5000.0)`, asserts
  the `applied_policy` is one of the 4 reference strings (not
  `stub-fixture-v1`), `warnings` is a list (not empty unless the
  profile has no edge cases), and the stub banner testid
  (`rebalance-stub-banner`) is NOT present in the rendered HTML.
- **MODIFIED** `tests/conftest.py::_UNIT_FILES`: add
  `test_rebalance_constants.py`, `test_rebalance_validation.py`,
  `test_rebalance_solver.py`, `test_rebalance_policy.py`,
  `test_rebalance_postprocessing.py`,
  `test_rebalance_engine_regression.py`. (Pure-function tests;
  no DB, no TestClient.)
- **MODIFIED** `tests/conftest.py::_INTEGRATION_PREFIXES`: add
  `tests/test_rebalance_engine_glue`.

### Specs

- **ADDED** `openspec/specs/rebalance-engine/spec.md`. New
  capability: `rebalance-engine` — the CVXPY solver that turns
  bridge output into a `RebalancePlan`. Defines requirements
  for solver behavior, validation, output shape, determinism,
  and the RBRX11-coupled regression contract.

### Glue contract carry-forward

- **NO CHANGE** to `src/omaha/rebalance/schemas.py` — the wire
  format (v1 subset of the solver's native output) is already
  defined and consumed by `routes/rebalance.py` and
  `routes/pages.py`.
- **NO CHANGE** to `src/omaha/rebalance/solver_stub.py` — kept
  in tree as a fallback for tests that want a deterministic
  response without the CVXPY solver in scope. The fixture is
  preserved as the "golden baseline" referenced in
  `rebalance-route` Decision 4.

## Capabilities

### New Capabilities

- `rebalance-engine`: CVXPY hierarchical rebalance solver that
  consumes `PortfolioSetup` + `Position` DataFrame +
  `MarketPriceLookup` and emits a `RebalancePlan` with a
  31-column `asset_plan`, 13-column `category_plan`, ~28-key
  `metrics` dict, `warnings` tuple, and `applied_policy`
  string. Owns the constants, validation, LP models, policy
  cascade, and post-processing. Plugs into the existing glue
  via the `solver` kwarg.

### Modified Capabilities

None. `rebalance-data-bridges` (Phase 2) defines the builder
shapes; `rebalance-route` (Phase 3a) defines the HTTP contract;
`rebalance-page` (Phase 3b) defines the UI. None change.

## Impact

- **Code novo** (~1830 LOC):
  - 5 módulos em `src/omaha/rebalance/`: `constants.py`
    (~50), `validation.py` (~120), `solver.py` (~600),
    `policy.py` (~400), `postprocessing.py` (~300),
    `engine.py` (~30).
  - `tests/fixtures/rebalance_engine/` — 8 fixtures (~200).
  - 7 `tests/test_rebalance_*.py` (~1100 LOC total).
- **Code modificado** (~6 LOC + deps):
  - `pyproject.toml` — +1 linha (`cvxpy>=1.5,<2`).
  - `src/omaha/rebalance/glue.py` — 1 linha (default
    `cvxpy_solver` em vez de `stub_solver`).
  - `tests/conftest.py` — +7 entries nas listas.
- **Dependências:** `cvxpy>=1.5,<2` (~50 MB no Docker image —
  já documentado como Phase 4 trade-off em
  `.planning/REBALANCE_PLAN.md` §Riscos item 1).
- **Tests:** 7 novos `tests/test_*.py`. Marcadores: 6 unit
  (sem DB) + 1 integration (DB + TestClient).
- **Sem breaking changes.** Glue continua aceitando `solver`
  kwarg. Stub permanece em tree para testes determinísticos.
- **Sem mudança** em routes, templates, models, seeds,
  fixtures de Phase 3a/3b, ou UI.

## Non-Goals

- **Withdrawals (saque real).** Engine rejeita `contribution <
  0` via `_validate_rebalance_inputs` (match reference
  algorithm). Contract `rebalance-route` continua permissivo
  (server aceita 0, positivo, negativo; page gate client-side
  com `min="0"`). Engine só roda quando contribuição é ≥ 0.
  Withdrawal real é Phase 5+ (escopo separado).
- **Persistência do plano.** Stateless, como decidido em
  `rebalance-route` Decision 6. Sem `rebalance_runs` table.
- **Execução de ordens.** Decisão global do roadmap §Design
  Decisions item 1: "Aplicar" o rebalance = executar o
  otimizador e exibir o plano. Usuário age manualmente na
  corretora.
- **Mobile.** Decisão de `rebalance-page`: desktop only.
- **Substituir o stub permanentemente.** Stub continua em tree
  para uso em testes determinísticos (sem CVXPY em scope). Glue
  default muda para `cvxpy_solver`; tests que querem o stub
  passam `solver=stub_solver` explicitamente.
- **Solver CLI standalone.** `simulate_rebalance` é uma função
  Python, não um entry point CLI. `investing` tinha
  `build_rebalance_plan(setup_path, position_path,
  contribution)` que lia xlsx; omaha não precisa — builders
  leem do DB.

## Sequence

1. `pyproject.toml` — add `cvxpy>=1.5,<2`. `uv sync`.
2. `tests/fixtures/rebalance_engine/` — port Apêndice D
   fixtures (prerequisite para qualquer teste de solver).
3. `src/omaha/rebalance/constants.py` — transcrição literal
   §4.
4. `src/omaha/rebalance/validation.py` — 11 checks + tests.
5. `src/omaha/rebalance/solver.py` — Phase 1 LP + Phase 2 LP +
   helpers + `simulate_rebalance` entry.
6. `src/omaha/rebalance/policy.py` — cascade + masks +
   evaluation.
7. `src/omaha/rebalance/postprocessing.py` — clamp, overspend,
   min-trade, plan builders.
8. `src/omaha/rebalance/engine.py` — `cvxpy_solver` shim.
9. `glue.py` — 1-line default swap.
10. RBRX11 regression tests (B.1 + B.2 together).
11. Glue integration test (`test_rebalance_engine_glue.py`).
12. Verification: `uv run task lint`, `task test-unit`,
    `task test-integration`, `task test-e2e -k rebalance_page`
    smoke, manual browser test against
    `http://192.168.1.6:8000/rebalance` per AGENTS.md "Network
    access" rule.
13. Archive `openspec/changes/rebalance-engine/` once green.