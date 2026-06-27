# Change: rebalance-route

## Why

Phase 2 (`rebalance-infra`, archived 2026-06-26) shipped the data bridges
that translate the omaha ORM into the shapes the reference CVXPY solver
consumes (`PortfolioSetup`, position DataFrame, `MarketPriceLookup`
Protocol). The bridges exist in `src/omaha/rebalance/` but nothing in
the HTTP layer can reach them. This change wires the bridges behind a
`POST /api/rebalance` endpoint with a typed request/response contract, a
glue module that runs the orchestration, and a deterministic solver
stub so Phase 4 (`rebalance-engine`) and Phase 3b (`rebalance-page`) can
both plug in against a stable contract without each having to wait for
the other.

The user-facing goal ("Rebalancear" button on the sidebar → operator
sees a contribution plan) is split across two changes for explicit
contract reasons: this change owns the **contract**, the next change
owns the **UI**.

## What Changes

- **ADDED** `POST /api/rebalance` router in `src/omaha/routes/rebalance.py`.
  Accepts `{contribution: float}` for the active profile; returns a
  `RebalancePlanResponse` JSON. 400 on `RebalanceValidationError` with
  the validation message in the `detail` field; 500 on unexpected
  solver failure.
- **ADDED** Pydantic schemas in `src/omaha/rebalance/schemas.py`:
  `RebalanceRequest`, `RebalanceAssetPlanRow` (subset of the solver's
  31-col `asset_plan` — only the columns the UI renders in v1),
  `RebalanceCategoryPlanRow` (subset of 13-col `category_plan`),
  `RebalancePlanMetrics` (~10 v1 metrics), `RebalanceWarning`, and
  `RebalancePlanResponse`. Schemas are the **contract** Phase 4 must
  satisfy and Phase 3b must consume — see Decision 1 in `design.md`.
- **ADDED** orchestration glue in `src/omaha/rebalance/glue.py`:
  `run_rebalance(db, profile, contribution) → RebalancePlan` that
  loads `Profile`, builds `PortfolioSetup`, builds the position frame,
  instantiates `OmahaMarketPriceLookup`, invokes the solver (stub in
  this change, real in Phase 4), and serializes the result to the
  response shape. The glue owns the contract translation — the solver
  returns its native dataclasses, the glue maps them into the v1
  schemas so the wire format is decoupled from the solver's internal
  column schema.
- **ADDED** deterministic solver stub in
  `src/omaha/rebalance/solver_stub.py`. Reads a frozen fixture
  (`tests/fixtures/rebalance_stub_fixture.json`) shaped exactly like
  the solver's native `RebalancePlan` output and returns it. Lets the
  route + UI be exercised end-to-end before CVXPY lands. The fixture
  is **identical** to the golden test Phase 4 will run against, so the
  stub and the real solver share a regression baseline.
- **MODIFIED** `src/omaha/main.py` to include `routes.rebalance.router`
  in the FastAPI app.
- **ADDED** tests: `tests/test_rebalance_route.py` (HTTP contract via
  TestClient), `tests/test_rebalance_glue.py` (orchestration unit
  tests, DB-touching), `tests/test_rebalance_schemas.py` (Pydantic
  schema round-trip + warning serialization). All three are
  `integration` markers — prefixes registered in
  `tests/conftest.py::_INTEGRATION_PREFIXES`.
- **NO** UI changes in this change. Sidebar button + page
  `/rebalance` + Alpine store arrive in the next change
  (`rebalance-page`).

### Implementation status (as of 2026-06-26)

Tasks 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, and 3.3 are already
implemented and committed (`81c4f5d`):

* `src/omaha/rebalance/schemas.py` — Pydantic v1 wire format.
* `src/omaha/rebalance/solver_stub.py` — fixture-backed stub.
* `src/omaha/rebalance/glue.py` — orchestration + translation.
* `tests/fixtures/rebalance_stub_fixture.json` — frozen fixture.

The remaining tasks (4 — route, 5 — main.py, 6 — tests, 7 —
verification) implement `POST /api/rebalance` and prove the
contract end-to-end. This proposal's spec + design therefore
document the **as-built** state of tasks 1-3 plus the
**to-be-built** tasks 4-7.

## Capabilities

### New Capabilities

- `rebalance-route`: HTTP endpoint and orchestration glue that turns
  the omaha ORM + a contribution amount into a `RebalancePlan`
  response. Owns the wire-format contract; Phase 4 plugs into the
  glue's solver hook, Phase 3b consumes the response shape.

### Modified Capabilities

None. `rebalance-data-bridges` (Phase 2, archived) defines the
builders the glue consumes; its requirements do not change.

## Impact

- **Code:** `src/omaha/routes/rebalance.py` (new, ~120 lines),
  `src/omaha/rebalance/schemas.py` (new, ~80 lines),
  `src/omaha/rebalance/glue.py` (new, ~80 lines),
  `src/omaha/rebalance/solver_stub.py` (new, ~30 lines),
  `src/omaha/main.py` (1 import + 1 `include_router` line),
  `tests/fixtures/rebalance_stub_fixture.json` (new, ~5 KB frozen
  fixture).
- **Dependencies:** None added. `cvxpy` ships with Phase 4
  (`rebalance-engine`); this change uses the stub fixture only.
- **Tests:** 3 new `tests/test_*.py` files, all `integration`. Prefix
  registration in `tests/conftest.py::_INTEGRATION_PREFIXES`.
- **Docs:** `.planning/REBALANCE_PLAN.md` updated to reflect the
  decision to split Phase 3 into `rebalance-route` (this change) +
  `rebalance-page` (next change).
- **Breaking changes:** None. The route is new; the schemas are
  private to this module until Phase 3b publishes them as the
  page's wire contract.

## Next change: `rebalance-page`

The follow-up change `rebalance-page` (Phase 3b) consumes the
wire contract defined here and renders:

* A `/rebalance` page (Jinja template + Alpine store) hosting the
  aporte input field and the results table.
* The fourth sidebar button labelled "Rebalancear" that links to
  `/rebalance`.
* The empty-state copy with a button to `/classes` when the
  profile has zero classes or zero assets.
* A chart comparing current vs projected allocation (per-class,
  not per-asset — the per-asset detail lives in the table).

`rebalance-page` does NOT add new server endpoints; it consumes
`POST /api/rebalance` defined here and renders the
`RebalancePlanResponse` shape documented in the spec.
