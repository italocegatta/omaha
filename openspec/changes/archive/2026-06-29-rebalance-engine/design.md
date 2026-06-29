# Design: rebalance-engine

## Context

Four archived OpenSpec changes built the rebalance pipeline
end-to-end against a frozen JSON fixture:

- `asset-trade-flags` — `Asset.buy_enabled`, `Asset.sell_enabled`,
  `Asset.currency_code`. Solver hard-locks respect these flags.
- `rebalance-infra` — bridges turn the omaha ORM into the
  reference algorithm's expected shapes:
  - `PortfolioSetup` (categories + assets DataFrames, target
    weights in 0..1, `buy_enabled` / `sell_enabled` /
    `currency_code` per asset, plus the omaha-specific
    `quote_kind` column).
  - `Position` DataFrame (one row per `Asset`, aggregated from
    `Position.qty` / `total_invested` / `total_current`).
  - `MarketPriceLookup` Protocol + `OmahaMarketPriceLookup`
    adapter over `QuoteCache` (returns `quote_price` in R$
    already, USD assets converted via `BRL=X` pre-fetched by
    `QuoteService._collect_symbols`).
- `rebalance-route` — `POST /api/rebalance`, Pydantic wire
  schemas, glue orchestration
  (`run_rebalance(db, profile, contribution, *, solver=None)`),
  solver stub backed by
  `tests/fixtures/rebalance_stub_fixture.json`.
- `rebalance-page` — `/rebalance` page renders the stub output
  with a banner explaining the solver is not real yet.

The reference algorithm lives at
`~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`
(1688 LOC, 41 functions, commit `ca867ba`). The reference docs
live at
`~/github/investing/docs/portfolio-rebalance-algorithm-reference.md`
(1126 lines). This change ports the algorithm 1:1, adapted only
for the omaha module boundary (split into 5 submodules instead of
one 1688-line file) and the already-translated bridge output.

Stakeholders: Italo (operator — runs rebalance after every
paycheck), Ana Livia (viewer — reviews the plan). Single-user
household deployment; concurrency is not a constraint.

## Goals / Non-Goals

**Goals:**

- Replace the stub solver with the real CVXPY solver so the
  `/rebalance` page reflects the operator's actual
  `AssetClass` / `Asset` / `Position` rows.
- Transcribe the reference's constants, validation, Phase 1
  LP, Phase 2 LP, policy cascade, and post-processing
  literally. Tolerances are literal (`1e-6`,
  `1e-4`); unit mistakes are the #1 reference error.
- Carry forward the stub fixture as the "golden regression
  baseline" (`rebalance-route` Decision 4). Real solver runs
  against the canonical 2-class / 5-asset fixture input,
  output matches within `1e-4` abs.
- Keep the change small and reviewable by splitting the
  reference's single 1688-line file into 5 modules
  (`constants`, `validation`, `solver`, `policy`,
  `postprocessing`) plus a thin `engine` shim.
- Port the Apêndice D fixtures and the Apêndice B RBRX11
  regression tests. The B.1 + B.2 fixes are coupled — port
  together.

**Non-Goals:**

- Withdrawals (negative contribution). Engine rejects via
  `_validate_rebalance_inputs` (match reference). Page gate
  client-side (already in `rebalance-page`). Contract stays
  permissive.
- CVXPY alternatives (scipy.optimize.linprog, hand-rolled LP,
  PuLP). Decision locked to CVXPY by §4 of the reference.
- Persisted rebalance runs. Stateless, as decided in
  `rebalance-route` Decision 6.
- Standalone solver CLI (`build_rebalance_plan(setup_path,
  position_path, contribution)` from `investing`). omaha
  builders read from the DB; the xlsx path is irrelevant.
- Solver hot-reload / precompile. Phase 4 ships cold-start,
  < 1s for typical portfolios (< 50 assets).
- GPU acceleration. CVXPY default (CPU CLARABEL) is fast
  enough.
- Multiple solvers (multi-objective, robust LP, scenario
  analysis). Single objective LP per the reference.

## Decisions

### Decision 1: Module split — 5 submodules + thin shim

The reference ships as a single 1688-line
`rebalancing.py`. Porting it verbatim into
`src/omaha/rebalance/solver.py` keeps the diff trivial but
makes review painful (one giant PR) and test file
co-location hard.

Split into 5 modules, mirroring the reference's natural
section boundaries:

| Module | LOC | Reference section | Responsibility |
|---|---|---|---|
| `constants.py` | ~50 | §4 | Literal constants — `ALLOCATION_TOLERANCE`, `DISPLAY_TOLERANCE`, `MIN_BUY_AMOUNT`, `MIN_SELL_AMOUNT`, `PRIORITIZED_*`, `SHORTFALL_RELATIVE_FLOOR_VALUE`, contribution-only / staged-sales thresholds, policy-name strings. |
| `validation.py` | ~120 | §7.1 | `_validate_rebalance_inputs(setup, position, contribution)` — 11 checks. |
| `solver.py` | ~600 | §5 + `rebalancing.py:300-700` | Phase 1 LP + Phase 2 LP + helpers + `simulate_rebalance` entry. |
| `policy.py` | ~400 | §6 + `rebalancing.py:700-1300` | Policy cascade (4 outcomes) + masks + evaluation. |
| `postprocessing.py` | ~300 | §7.2 + `rebalancing.py:1300-1688` | Plan builders (asset/category/metrics/warnings) + clamp + overspend + min-trade + market data enrichment. |
| `engine.py` | ~30 | (new) | Thin shim re-exporting `simulate_rebalance` as `cvxpy_solver(setup, positions, quotes, contribution)` (glue-compatible signature). |

* (A) Single 1688-line `solver.py`. *Rejected.* Review
  burden; tests can't co-locate with the function they
  exercise; git history is one giant blob.
* **(B) 5-module split + thin shim.** *Adopted.* Each
  module ≤ 600 LOC. Test files mirror (`test_rebalance_*`),
  one per module. Re-export from `rebalance.__init__`
  stays minimal (CVXPY is heavy — don't import it at
  module top-level of the package).
* (C) Full split into 10+ tiny modules. *Rejected.*
  Differs too far from the reference; future re-syncing
  becomes harder.

Trade-off: cross-module imports are slightly more verbose
(`from omaha.rebalance.solver import simulate_rebalance`
inside `policy.py`) but Python's relative imports make it
trivial.

### Decision 2: Withdrawal — engine rejects, contract permissive

The contract (`rebalance-route` spec, archived 2026-06-27)
says `contribution` is "any finite float" — zero is valid,
negative is valid, NaN/inf returns 422. The page gates
`< 0` client-side with `min="0"` and explanatory copy
("Saques serão suportados em versão futura"). The
reference's `_validate_rebalance_inputs` rejects
`contribution < 0` with `"O aporte informado nao pode ser
negativo."` (`rebalancing.py:118-119`).

`rebalance-engine` keeps the reference's behavior. The
engine's validation raises `RebalanceValidationError` on
negative contribution. The route maps the error to HTTP
400 (`rebalance-route` Decision 7 already covers this).
The page, since it gates client-side, never submits
negative in practice.

* (A) Engine rejects negative, contract stays permissive,
  page gates client-side. *Adopted.* Matches reference;
  contract remains useful for future withdrawal support.
* (B) Engine accepts negative, treats as "withdrawal" —
  solver sells until portfolio = 0. *Rejected.* Scope
  creep; reference doesn't define withdrawal semantics;
  Phase 5+.
* (C) Engine rejects negative, contract tightens to
  reject negative server-side (422). *Rejected.* Breaks
  the `rebalance-route` contract; the spec is already
  archived and synced to main.

### Decision 3: cvxpy pin — `>= 1.5, < 2`

CLARABEL has been CVXPY's default conic solver since
1.4.x. SCS ships as the bundled fallback. Pinning `>= 1.5`
guarantees CLARABEL as primary; `< 2` blocks any 2.0
breaking change while the project matures.

* (A) `cvxpy>=1.5,<2`. *Adopted.* Stable, modern, CLARABEL
  default.
* (B) `cvxpy>=1.3,<2`. *Rejected.* Older, misses some
  CLARABEL improvements.
* (C) No upper bound. *Rejected.* 2.x may introduce API
  changes that require code edits.

CLARABEL install size: ~30 MB. SCS: ~20 MB. Total CVXPY
overhead: ~50 MB. Already noted as Phase 4 trade-off in
`.planning/REBALANCE_PLAN.md` §Riscos item 1.

### Decision 4: Stub fixture is the golden regression baseline

Carry forward from `rebalance-route` Decision 4. The
fixture (`tests/fixtures/rebalance_stub_fixture.json`) is
a 2-class / 5-asset toy portfolio. The real solver must
match the fixture's output within `1e-4` abs when fed the
matching setup + position inputs.

Implementation: a unit test constructs the canonical input
DataFrames that produce the fixture's `asset_plan` /
`category_plan` / `metrics` shape, runs the real solver,
and asserts equality within tolerance. CLARABEL is
deterministic over the same problem and solver settings,
so this test is reproducible.

* (A) Carry forward as golden regression. *Adopted.*
  Continuity with the stub's contract.
* (B) New fixture tuned to the real solver's output.
  *Rejected.* Loses the diff-vs-stub baseline; harder to
  spot regressions introduced by the port.
* (C) No regression against the stub — only against
  Apêndice D fixtures. *Rejected.* Stub fixture is the
  closest thing to a "rebalance for a real-ish portfolio"
  regression we have; skipping it loses signal.

### Decision 5: `applied_policy` strings — the reference's four

The reference defines 4 policy strings
(`rebalancing.py:43-46`):

- `"contribution-only"` — aporte realoca sem vender
  nada. Adequado quando portfolio já está balanceado
  (só ativos subponderados ou na borda).
- `"contribution-with-overweight-sales"` — vende
  sobreponderados, mas só os que estão acima do alvo;
  não vende para zerar desvio total.
- `"contribution-with-full-sales"` — vende sem
  restrição; o solver pode vender qualquer ativo
  trade-enabled.
- `"current-portfolio-rebalance"` — aporte zero;
  rebalanceia só vendendo.

The stub uses `"stub-fixture-v1"` as a sentinel. The real
solver returns one of the 4 reference strings. The page's
stub banner template
(`{% if plan.applied_policy == "stub-fixture-v1" %}`) auto-
hides when the real solver lands.

* (A) Use the reference's 4 strings verbatim. *Adopted.*
  Diff trivial; PT-BR is not required for machine-emitted
  policy names.
* (B) Translate to PT-BR. *Rejected.* The strings flow
  into the page UI via `applied_policy`; English strings
  are fine (or we can add a translation layer in the page
  later).
* (C) Introduce a 5th string `"withdrawal"` for negative
  contribution. *Rejected.* Engine rejects negative
  per Decision 2; no need for a new string.

### Decision 6: Empty class with non-zero target — warning + residual

The bridge emits `EMPTY_CLASS_NONZERO_TARGET` warning when
a class has `target_pct > 0` but zero assets (see
`rebalance-data-bridges` spec). The solver still runs.

What happens at solve time:
- Phase 1 LP sees an asset-less class with `target_value >
  0`. The solver allocates `delta_c = target_value -
  current_value` of the contribution to that class, then
  Phase 2 has no assets to distribute it across.
- `residual_cash` grows by the unallocated amount.
- The class appears in `category_plan` with `current_value`
  unchanged and `projected_value == current_value`.

The post-processing step preserves the bridge warning
verbatim and adds a second warning ("class received
allocation but has no assets — contribution not deployed")
only if the residual is > `MIN_BUY_AMOUNT`. This matches
the reference's warning-passing-through behavior.

* (A) Solver runs, residual grows, both warnings emitted.
  *Adopted.* Matches reference; gives the operator full
  visibility.
* (B) Solver rejects the profile as invalid. *Rejected.*
  Bridge explicitly marks this as warning-not-error
  (`rebalance-data-bridges` Decision 7 in the archived
  change).
* (C) Solver silently absorbs. *Rejected.* Operator has
  no way to know the contribution was partially deployed.

### Decision 7: RBRX11 regressions — port B.1 and B.2 together

Apêndice B of the reference documents two coupled
regressions:

- **B.1** — Phase 2 was selling an asset at the global
  target when the category was receiving contribution.
  Fix: hard lock `sell[i] == 0` for assets at-or-below
  target when `delta_c >= 0`.
- **B.2** — Phase 1 was draining an underweight category
  to extract capital from internal overweights. Fix: if
  category is underweight, `delta[c] >= 0` regardless of
  internal overweights.

The reference explicitly notes the two fixes are coupled:
"Replicar só o fix de Phase 2 sem o de Phase 1 não
reproduz o comportamento correto. Replicar só o de Phase
1 sem o de Phase 2 idem. Os dois fixes devem ser portados
juntos." (Reference §B.2 closing paragraph.)

Port both fixes in the same change. Test functions live
in the same file
(`tests/test_rebalance_engine_regression.py`) with shared
fixtures (`build_category_first_setup`,
`build_category_first_position`).

* (A) Single test file with both B.1 and B.2, shared
  fixtures, ported together. *Adopted.*
* (B) Separate files per regression. *Rejected.* The
  fixtures are shared; split files duplicate setup.
* (C) Defer one of the regressions. *Rejected.* Coupled
  bugs require coupled tests.

### Decision 8: Solver import surface — lazy

`cvxpy` is ~50 MB and slow to import (~0.5s). Importing
`omaha.rebalance` should not pay that cost.

Implementation:
- `src/omaha/rebalance/__init__.py` does NOT import
  `solver`, `policy`, `postprocessing`, `engine`. Only
  bridges (`builders`, `market_prices`, `quotes_adapter`,
  `models`) and re-exported types.
- `cvxpy_solver` lives in `omaha.rebalance.engine`. Glue
  imports it lazily inside `run_rebalance` (Python's
  function-local imports are deferred until first call).
- Tests for the engine modules import directly from
  `omaha.rebalance.solver`, etc. — bypassing the package
  surface.

* (A) Lazy import via function-local `from .engine import
  cvxpy_solver`. *Adopted.* Keeps `omaha.rebalance`
  import-time fast.
* (B) Top-level `__init__.py` import. *Rejected.* Every
  test file (even pure bridge tests) pays the CVXPY
  import cost.
* (C) Separate `omaha.rebalance.cvxpy` subpackage.
  *Rejected.* Overkill for one module; hides the
  algorithm from casual readers.

### Decision 9: Test marker split — 6 unit + 1 integration

Per AGENTS.md "Test marker rule — explicit allow-list",
`tests/conftest.py::pytest_collection_modifyitems`
partitions the suite via two lists.

The new test files split as:

- **`_UNIT_FILES`** (pure-function, no DB):
  - `test_rebalance_constants.py` — assert constants
    match §4.
  - `test_rebalance_validation.py` — 11 validation
    scenarios.
  - `test_rebalance_solver.py` — LP smoke tests with
    fixture inputs.
  - `test_rebalance_policy.py` — 4 cascade outcome
    scenarios.
  - `test_rebalance_postprocessing.py` — plan builders.
  - `test_rebalance_engine_regression.py` — RBRX11 B.1
    + B.2.

- **`_INTEGRATION_PREFIXES`** (DB + TestClient):
  - `tests/test_rebalance_engine_glue` — full pipeline
    against the seeded Italo profile.

Carrying the marker rule forward keeps `task test-unit`
fast (no DB, no CVXPY-related network); `task
test-integration` exercises the full pipeline including
the glue integration.

### Decision 10: Stub stays in tree

`solver_stub.py` and `tests/fixtures/rebalance_stub_fixture.json`
remain in the repo after this change ships. Reasons:

1. **Deterministic tests.** Some test cases want a
   known-shape response without paying the CVXPY import
   cost.
2. **Diff baseline.** Comparing stub output vs. real
   output catches solver regressions.
3. **Backward compat.** External callers of
   `POST /api/rebalance` that pass
   `solver=stub_solver` continue to work.

Glue default flips from `stub_solver` to `cvxpy_solver`.
Tests that want the stub pass it explicitly.

* (A) Stub stays, glue default flips. *Adopted.*
* (B) Stub deleted. *Rejected.* Loses the regression
  baseline; breaks any external caller that relies on
  the deterministic fixture.
* (C) Stub moves to `tests/` only. *Rejected.* Couples
  production import path to test infrastructure.

## Implementation notes (non-binding guidance for tasks.md)

### CVXPY model sketch (from reference §5)

**Phase 1 LP** (per-category allocation):

```
Variables: delta_c (per category, real), contrib_c (per
           category, ≥ 0), sell_c (per category, ≥ 0),
           buy_c (per category, ≥ 0)

Objective: minimize  Σ_c (delta_c - target_c)²
           + λ_buy * Σ_c buy_c²
           + λ_sell * Σ_c sell_c²

Constraints:
  - Σ_c contrib_c == contribution (cash balance)
  - Σ_c sell_c == Σ_c buy_c + residual_cash
                   (cash balance, sells fund buys)
  - projected_value[c] == current_value[c] + contrib_c -
                          sell_c
  - delta_c == projected_value[c] - target_value[c]
  - category is underweight ⇒ delta_c >= 0 (RBRX11 B.2 fix)
  - sell_c <= category_sell_capacity[c]
  - buy_c <= category_buy_capacity[c]
  - target_pct == 0 ⇒ sell_c == 0  (zero-target hard lock)
```

**Phase 2 LP** (per-asset intra-category):

```
Variables: sell (per asset, ≥ 0), buy (per asset, ≥ 0)

Objective: minimize Σ_i (projected_i - target_i)²
                + λ * Σ_i (sell_i² + buy_i²)

Constraints:
  - Σ_i sell_i == sell_c (per category)
  - Σ_i buy_i == buy_c (per category)
  - projected_i == current_i + buy_i - sell_i
  - sell_enabled[i] == False ⇒ sell_i == 0
  - buy_enabled[i] == False ⇒ buy_i == 0
  - at_or_below_target[i] AND delta_c >= 0 ⇒ sell_i == 0
    (RBRX11 B.1 fix)
  - MIN_BUY_AMOUNT / MIN_SELL_AMOUNT enforced in
    post-processing, not LP (LP is continuous)
```

### Solver settings

```python
def _build_optimizer_parameters() -> dict[str, Any]:
    return {
        "solver": cp.CLARABEL,
        "verbose": False,
        "eps": 1e-8,  # SCS fallback precision
    }
```

CLARABEL on a 50-asset / 6-category LP solves in
milliseconds. SCS fallback for ill-conditioned problems;
rare in practice.

### Determinism

CLARABEL is deterministic given:
1. Same problem formulation (same constraints, same
   objective coefficients).
2. Same solver settings (same `eps`, same `max_iter`).
3. Same solver version.

CVXPY 1.5+ ships CLARABEL 0.7.x. Pinning `>= 1.5, < 2`
gives reproducible solver behavior across runs.

The stub fixture regression test
(`test_engine_matches_stub_fixture`) catches solver
behavior drift across upgrades. CI failures on a CVXPY
upgrade are a deliberate forcing function to review
output diffs.

### Output mapping (glue side)

The reference's `RebalancePlan` shape is identical to
the omaha glue's expected native shape
(`RebalancePlan` dataclass in
`src/omaha/rebalance/solver_stub.py:65-80`). The glue's
existing translation loop in `glue.py:107-155` works
unchanged. No glue edit required beyond the 1-line
default swap.

## Risks

1. **RBRX11 coupled bugs.** Decision 7 enforces
   co-porting, but if a future CVXPY upgrade subtly
   changes LP behavior, both regressions could regress
   simultaneously and the test might mask a
   partial-regression. Mitigation: run both tests
   independently, not as one combined assertion.

2. **CLARABEL determinism on platform variation.**
   CLARABEL results can differ across platforms if the
   underlying BLAS differs (e.g., macOS Accelerate vs
   Linux OpenBLAS). Mitigation: tolerance is `1e-4` abs
   (matches reference), wider than typical
   floating-point drift; the stub fixture regression
   test passes on both platforms.

3. **CVXPY install size.** ~50 MB. Already noted as
   Phase 4 trade-off in
   `.planning/REBALANCE_PLAN.md` §Riscos item 1. Docker
   image grows correspondingly. Test environment shares
   the same install; CI cost negligible.

4. **Solver cold start.** First `simulate_rebalance`
   call after process start pays CVXPY's import cost
   (~0.5s). Subsequent calls ~50ms for typical
   portfolios. End-to-end `/api/rebalance` round trip
   remains < 1s.

5. **Asset name collision asymmetry.** Bridge does
   `groupby("asset_key").first()` (one row per name,
   regardless of how many classes carry it). Position
   frame aggregates `Position.total_current` over all
   rows with the same `asset_key`. The solver runs
   against shadowed assets but combined positions —
   sums still match the live DB. Cross-class collision
   shows up in the bridge warning
   (`ASSET_NAME_COLLISION`) and as a single row in the
   plan table. Operator sees the warning; solver output
   is internally consistent.

6. **Tolerance drift across portfolio size.** The
   reference's tolerances were tuned for portfolios with
   ≤ 30 assets. Italo has 48 assets, Ana has ~40.
   Larger portfolios push LP solve time and may
   accumulate more numerical drift. Mitigation: `1e-4`
   abs tolerance on the stub fixture regression;
   monitor `task test-integration` runtime after first
   deploy.

## References

- Reference algorithm:
  `~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`
  (1688 LOC, 41 functions, commit `ca867ba`).
- Reference docs:
  `~/github/investing/docs/portfolio-rebalance-algorithm-reference.md`
  (1126 lines).
- Reference tests:
  `~/github/investing/tests/test_rebalancing.py` (RBRX11
  cases at lines 1270-1540) and
  `~/github/investing/tests/conftest.py` (Apêndice D
  fixtures).
- Bridge spec: `openspec/specs/rebalance-data-bridges/spec.md`.
- Route spec: `openspec/specs/rebalance-route/spec.md`.
- Page spec: `openspec/specs/rebalance-page/spec.md`.
- Roadmap: `.planning/REBALANCE_PLAN.md` (Phase 4).
- AGENTS.md: Network access (LAN URL), test marker rule,
  refresh-for-test delivery recipe.
