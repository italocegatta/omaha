# Design: rebalance-route

## Context

`rebalance-infra` (archived 2026-06-26) shipped four pure-function
modules under `src/omaha/rebalance/`:

* `models.py` — `PortfolioSetup` dataclass + `RebalanceValidationError`.
* `builders.py` — `build_setup_from_db`, `build_position_frame`.
* `market_prices.py` — `MarketPriceLookup` Protocol + helpers
  (`resolve_quote_symbol`, `build_empty_quote_frame`, `NoopMarketPriceLookup`).
* `quotes_adapter.py` — `OmahaMarketPriceLookup` (the concrete
  `Protocol` implementation over `QuoteCache` + `Position.current_price`).

The bridges take a `Profile` and a SQLAlchemy session and emit the
data shapes the reference CVXPY solver
(`~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`)
consumes. The solver itself is **not ported yet** — that is Phase 4
(`rebalance-engine`).

Today the dashboard sidebar has three buttons (Importar CSV, + Novo
ativo, + Nova classe). The user has confirmed the fourth button reads
"Rebalancear" and lands on a dedicated page `/rebalance` (the page is
the next change, `rebalance-page`; this change owns the route only).
The user has also confirmed v1 is stateless (no `rebalance_runs`
table, no run_id, every POST is a fresh computation) and the dev
target is desktop only.

Stakeholders: Italo (operator, runs rebalance after a paycheck),
Ana Livia (viewer, reviews the plan). Single-user household
deployment; concurrency is not a constraint.

## Goals / Non-Goals

**Goals:**
- Define a stable HTTP + JSON contract that Phase 4
  (`rebalance-engine`) plugs into and Phase 3b (`rebalance-page`)
  consumes. The contract is the primary deliverable; the route is
  its first consumer.
- Wire the existing bridges into a `POST /api/rebalance` endpoint
  behind a glue module that owns the contract translation, so the
  solver stays oblivious of the wire format.
- Provide a deterministic solver stub backed by a frozen JSON fixture
  so the route + glue + future UI can be exercised end-to-end before
  CVXPY lands. The fixture is the golden baseline Phase 4 will run
  against.
- Map `RebalanceValidationError` → HTTP 400 with the validation
  message in `detail`. Generic solver failure → 500 with a generic
  detail (no stack trace leakage).

**Non-Goals:**
- CVXPY solver port. Arrives in `rebalance-engine` (Phase 4).
- Dashboard UI, sidebar button, Alpine store, page rendering.
  Arrives in `rebalance-page` (Phase 3b).
- Persistence of rebalance runs (no `rebalance_runs` table). Every
  visit to `/rebalance` requires the operator to type the aporte
  and click Calcular; the response is not cached on the server.
- Authentication/authorization changes. The route uses the existing
  `require_user` + `require_active_profile` dependencies from
  `omaha.auth` like every other JSON route.
- Live quote refresh on the request path. `BRL=X` is already
  pre-fetched by `QuoteService._collect_symbols` (Phase 2 Decision 2).
- Concurrency control. Single-user app; serial by design.

## Decisions

### Decision 1: Wire format exposes a v1 subset of the solver's full output

The reference solver's `RebalancePlan` carries a 31-column
`asset_plan`, a 13-column `category_plan`, and ~28 metric keys.
The v1 wire format exposes only what the page renders in Phase 3b:

| Solver field | v1 wire field | Why subset |
|---|---|---|
| `asset_plan[i]` × 31 cols | 9 fields per row | Page v1 renders: name, class, current, target, buy, sell, projected, action |
| `category_plan[j]` × 13 cols | 4 fields per row | Page v1 renders: name, current, projected, delta |
| `metrics` × 28 keys | 6 keys | Page v1 needs: totals + deviation; rest is internal |
| `applied_policy` (top-level) | `applied_policy: str` (top-level) | Page v1 renders the cascade name; not in metrics |
| `warnings` (list[str]) | `list[RebalanceWarning]` | Wrapping adds `code` for future filtering |

`RebalancePlanMetrics` does NOT carry `applied_policy` — that
field lives at the top of `RebalancePlanResponse` because it
applies to the whole plan, not to the metrics block.

* **(A) Expose v1 subset now, add fields as the page needs them.**
  *Adopted.* Wire stays small (~3x smaller payload); contract grows
  by demand, not by surprise. Trade-off: Phase 4 must add a column to
  the schema, not just to the solver — but the round-trip is cheap
  (spec edit + schema edit + glue edit + test edit, all in the same
  PR).
* (B) Expose full 31 + 13 + 28. Future-proof, but adds ~3x payload,
  22 hidden columns the page will never read, and bleeds solver
  internals into the wire format. Schema evolution becomes harder.
* (C) Expose as `dict[str, Any]` with no schema. Loses Pydantic
  validation and OpenAPI docs; refactor cost when a real schema is
  added is higher than starting with a real schema.

The subset is documented in the v1 spec (`specs/rebalance-route/spec.md`,
"Wire format subset"). When Phase 3b needs a column not in the
subset, it edits the spec + glue + adds a test, in that order.

### Decision 2: Glue owns contract translation; solver returns native dataclasses

The glue module (`rebalance/glue.py::run_rebalance`) calls the solver
and receives whatever shape the solver natively returns. The glue
maps the native dataclasses into the v1 Pydantic wire format before
the route returns.

* **(A) Glue translates; solver is wire-agnostic.** *Adopted.*
  `rebalance-engine` (Phase 4) can ship the solver without touching
  the wire format. The translation lives in one module with one
  test surface. The Pydantic schemas stay owned by the omaha side.
* (B) Solver returns Pydantic schemas. Couples the reference port
  to FastAPI / Pydantic version, which the reference algorithm
  doesn't otherwise need.
* (C) Route translates directly (no glue module). Saves ~80 lines
  but pushes glue concerns into FastAPI route handlers where
  they're hard to unit-test without `TestClient`.

### Decision 3: Solver is an injected callable, not a global

`run_rebalance(db, profile, contribution, *, solver=stub_solver)`
takes the solver as a keyword argument. The route passes the stub
in v1; Phase 4 swaps it for the real solver (a single line in the
route's `run_rebalance` call, or a FastAPI dependency override).

* **(A) Inject solver as kwarg.** *Adopted.* No global state, no
  module-level monkey-patching, trivial to test the glue with
  custom solvers (golden fixture vs edge case fixture). The stub
  fixture path is passed the same way.
* (B) Module-level `SOLVER = stub_solver`, swap by reassignment.
  Global mutable state; tests that mutate it leak between cases.
* (C) FastAPI `Depends(get_solver)` indirection. Adds a DI layer
  for a single function call — overhead exceeds value.

### Decision 4: Solver stub reads from a frozen JSON fixture

The stub (`rebalance/solver_stub.py::stub_solver`) loads
`tests/fixtures/rebalance_stub_fixture.json` and returns the
fixture as the solver's native `RebalancePlan` shape. The fixture
is the **same** file Phase 4 will use as its golden regression
test input.

The stub also overlays `metrics.contribution = contribution` on
top of the loaded fixture so the response reflects the request
(e.g. calling with `contribution=5000.00` returns a plan whose
`metrics.contribution = 5000.00`, even though the fixture carries
`metrics.contribution = 1000.00`). The fixture's `metrics.contribution`
is therefore a canonical reference value used by Phase 4's golden
test (the stub's overlay is a no-op when the test passes
`contribution=1000.00`).

* **(A) Frozen JSON fixture + stub overlay of `metrics.contribution`.**
  *Adopted.* One source of truth for "what the solver should
  produce for these inputs". The fixture's `metrics.contribution`
  is the canonical reference value Phase 4's golden test compares
  against (when called with `contribution=1000.00`, the stub's
  overlay is a no-op and the response matches the fixture
  byte-for-byte). The stub UX-correctly reflects any other
  `contribution` the operator typed. Trade-off: Phase 4's golden
  test must pin `contribution=1000.00` to stay comparable with the
  fixture.
* (B) Stub generates synthetic data procedurally. Saves writing
  the fixture but breaks Phase 4's ability to use it as a golden
  test (the stub is approximate, the real solver is exact — divergence
  is silent).
* (C) Stub inlines the data in Python. Same drift risk as (B),
  plus blocks pytest's snapshot tooling from comparing against the
  fixture.

Alternative considered for the `contribution` overlay:

* Stub ignores the `contribution` argument. Breaks the page UX
  (operator types R$ 5000 but sees R$ 1000 in the response).
* Glue overrides `metrics.contribution` after the solver returns.
  Cleanest separation but requires reverting the committed
  solver stub and glue. Deferred — not worth the divergence cost.

The fixture covers: 2 classes (60/40 target split), 5 assets
(CDB ABC, Tesouro Selic, PETR4 with `buy_enabled=False`, AAPL with
`currency_code="USD"`, ITUB4), populated `asset_plan` + `category_plan`,
all six metric keys, and one `EMPTY_CLASS_NONZERO_TARGET` warning.
~2.2 KB on disk.

### Decision 5: `RebalanceValidationError` → 400, generic Exception → 500

The route catches `RebalanceValidationError` (already defined in
`rebalance/models.py`) and returns HTTP 400 with the validation
message in `detail`. Any other exception escapes as 500 with a
generic `"Erro ao calcular rebalanceamento"` detail — no stack
trace in the response.

* **(A) Catch `RebalanceValidationError` explicitly, let others
  pass through to FastAPI's default 500 handler.** *Adopted.*
  Matches the pattern used by `routes/imports.py` for its preview
  validation errors. The validation message is operator-facing
  ("Classe 'Cripto' está vazia mas com target_pct=20.00%") so it
  belongs in `detail`, not in the log.
* (B) Catch `Exception` and return 500 with the message. Leaks
  solver internals (stack frames, CVXPY variable names) into the
  HTTP response. Worse for security + UX.

### Decision 6: No `rebalance_runs` table; stateless v1

The user confirmed: every visit to `/rebalance` requires the
operator to type the aporte and click Calcular. The server does
not cache the most recent plan.

* **(A) Stateless.** *Adopted.* Zero migration, zero new table,
  no invalidation logic (the only stale signal is the quote
  cache, which already has a TTL).
* (B) Persist every POST as a `rebalance_runs` row + per-asset
  `rebalance_run_items` rows. Adds an audit trail but requires a
  migration, a model, a serializer, and a deletion story (when do
  old runs expire?). Defers Phase 3b's UI work to design the
  history list.
* (C) Cache only the latest plan in-memory (TTL 60s). Saves the
  recompute cost (CVXPY is ms — negligible) at the price of a
  second code path that has to expire correctly. Not worth it.

The CVXPY solve is fast enough (CLARABEL on a few dozen assets
solves in <50ms per the plan's "Riscos" section) that recomputing
on every click is free. Stateless v1 matches the user's choice and
keeps the change small.

## Risks / Trade-offs

* **Wire format subset may be too small.** Mitigation: the v1 spec
  lists the rendered columns explicitly. Adding a column is a
  small change spanning the spec scenario + the Pydantic model +
  the glue mapper + a new schema assertion. Phase 3b owner
  will discover the gap immediately when a template needs a column
  the schema doesn't carry.

* **Stub fixture diverges from real solver.** Mitigation: the
  fixture is committed at the same path; Phase 4's first
  integration test reads the fixture and asserts the real solver's
  output matches byte-for-byte. If the stub fixture drifts from
  the real solver's expectations, that test fails first.

* **`RebalanceValidationError` message language drift.** The
  bridge emits Portuguese messages
  (`"Classe 'Crypto' está vazia mas com target_pct=20.00%..."`).
  The route forwards them verbatim to the page, which renders
  them inside the modal. If Phase 4 changes the message wording
  in the bridge, the page copy changes silently. Mitigation:
  `test_rebalance_glue.py` asserts the message text for the two
  known cases (empty class, asset collision).

* **Quote cache stale during rebalance.** Up to 15 min stale per
  Phase 2 Decision 2; documented in the page modal as "Cotação de
  HH:MM" in Phase 3b. No mitigation needed in this change.

* **Pydantic schema validation cost.** A `RebalancePlanResponse`
  with ~30 rows × ~10 fields runs `model_validate` once per
  request. CPU cost is sub-millisecond; not a risk.

* **Cross-class asset name collision (Phase 2 Decision 1).** The
  bridge already emits a warning per collision. The glue passes
  the warning through to the response `warnings` list. Phase 3b
  renders them; no special handling in the route.

## Migration Plan

No data migration. No schema change. No backward-incompatible
behavior change.

* `POST /api/rebalance` is a new endpoint; nothing else calls it
  yet.
* New modules under `src/omaha/rebalance/` are additive.
* `src/omaha/main.py` adds one `include_router` line; existing
  route registration is untouched.

Rollback: delete the new modules, revert the `include_router`
line. No DB state to undo.

## Open Questions

* **Solver callable signature.** Will the real solver in Phase 4
  accept `(setup, positions, lookup, contribution)` or
  `(setup, positions, lookup)` with `contribution` baked into the
  setup? Recommendation: Phase 4 keeps `contribution` as a
  separate argument to the solver function — the glue then has a
  natural place to inject it and the solver stays pure. The stub
  in this change will use the same signature so the swap is a
  drop-in. (Answered in Decision 4 — stub overlay of
  `metrics.contribution` keeps the fixture golden-testable.)

* **Should `RebalanceWarning` carry a `severity` field?** v1
  emits only `code` + `message` (info-level). Future warnings
  might be advisory ("cotação stale") vs blocking ("USD asset
  sem BRL=X no cache"). Recommendation: v1 schema does NOT
  carry `severity`; the page renders all warnings the same way.
  Adding severity later is a one-line schema change.

* **Should v1 carry `policy_reason` (the cascade's "why")?** YAGNI
  for v1. The cascade name (`applied_policy`) is enough for the
  page; the reason can be added as an optional
  `policy_reason: str | None = None` field when the page needs it.
  Adding later is a one-line schema change.

* **`contribution` validation range.** Allow negative (withdrawal)?
  v1 rejects `contribution <= 0` with 422 ("Aporte deve ser maior
  que zero"). Phase 4 will need to think about withdrawal policy;
  deferring to Phase 4 keeps this change small.

* **`/api/rebalance` rate limiting.** The endpoint triggers a
  CVXPY solve; a malicious client could DoS by spamming. v1 has no
  rate limit (single-user household, LAN-only); document this in
  the proposal as a v1 simplification. Phase 5+ can add FastAPI
  middleware if the threat model changes.
