# Tasks: rebalance-route

## 1. Pydantic schemas

- [x] 1.1 Create `src/omaha/rebalance/schemas.py` with `RebalanceRequest`
      (one field: `contribution: float` with `gt=0` constraint),
      `RebalanceAction` enum (`"buy" | "sell" | "hold"`),
      `RebalanceAssetPlanRow` (9 fields per spec),
      `RebalanceCategoryPlanRow` (4 fields per spec),
      `RebalancePlanMetrics` (6 keys per spec), `RebalanceWarning`
      (code + message), and `RebalancePlanResponse` (composing the
      above + `applied_policy: str`).
- [x] 1.2 Add `model_config = ConfigDict(extra="forbid")` to all
      response models so unknown solver columns surface as a 500
      during development rather than silently leaking into the wire.

## 2. Solver stub + fixture

- [x] 2.1 Create `tests/fixtures/rebalance_stub_fixture.json` with
      the canonical 2-class / 5-asset shape per the spec
      ("Solver stub returns a frozen fixture" requirement):
      2 classes (60/40 target split), 5 assets with mixed
      `buy_enabled` / `currency_code`, populated `asset_plan` +
      `category_plan`, all six metric keys, and one
      `EMPTY_CLASS_NONZERO_TARGET` warning. Pin `contribution`
      to a fixture-level value of `1000.00` so the stub's
      response is fully deterministic.
- [x] 2.2 Create `src/omaha/rebalance/solver_stub.py` with
      `stub_solver(setup, positions, quotes, contribution)` that
      loads the fixture, overlays `metrics.contribution =
      contribution` (so the response reflects the request),
      and raises `ValueError` if both `setup.assets` and
      `setup.categories` are empty.

## 3. Glue orchestration

- [x] 3.1 Create `src/omaha/rebalance/glue.py` with
      `run_rebalance(db, profile, contribution, *, solver=None)`
      that orchestrates builders + adapter + solver in the order
      documented in spec §"Glue orchestrates profile loading,
      builders, adapter, and solver". Default `solver` to
      `stub_solver` when `None`.
- [x] 3.2 Implement the native → wire translation: map solver
      `asset_plan` rows to `RebalanceAssetPlanRow` (drop columns
      outside the v1 subset, derive `action` from `buy_amount` /
      `sell_amount` with `DISPLAY_TOLERANCE = 1e-4` for `hold`),
      map `category_plan` rows to `RebalanceCategoryPlanRow`
      (derive `delta`), map `metrics` to `RebalancePlanMetrics`,
      and wrap bridge warnings in `RebalanceWarning` with the
      documented `code` values.
- [x] 3.3 Add `EMPTY_PROFILE` warning emission: if the glue
      detects `setup.assets.empty AND setup.categories.empty`
      before calling the solver, return an empty
      `RebalancePlanResponse` with `warnings = [RebalanceWarning(
      code="EMPTY_PROFILE", message="Perfil sem classes nem ativos
      cadastrados...")]` instead of calling the solver.

## 4. Route

- [ ] 4.1 Create `src/omaha/routes/rebalance.py` with a single
      `POST /api/rebalance` endpoint. Dependencies:
      `require_user` + `require_active_profile` + `DbSession`
      (per the existing pattern in `routes/imports.py`).
- [ ] 4.2 Parse `RebalanceRequest` from the body; on Pydantic
      validation failure FastAPI returns 422 automatically
      (covered by the spec §"Request validates contribution
      greater than zero").
- [ ] 4.3 Catch `RebalanceValidationError` around the
      `run_rebalance` call and return
      `HTTPException(status_code=400, detail=str(exc))`. Let
      other exceptions propagate to FastAPI's default 500
      handler.
- [ ] 4.4 Return `run_rebalance(...)` as the response body (it
      already produces a `RebalancePlanResponse` Pydantic model;
      FastAPI serializes it).

## 5. App registration

- [ ] 5.1 Edit `src/omaha/main.py` to import
      `from omaha.routes.rebalance import router as rebalance_router`
      and add `app.include_router(rebalance_router)` next to the
      existing route registrations.

## 6. Tests

- [ ] 6.1 Create `tests/test_rebalance_schemas.py` (integration
      marker): round-trip a fully-populated `RebalancePlanResponse`
      through `model_validate` + `model_dump_json`; assert
      `extra="forbid"` rejects unknown keys; assert
      `RebalanceRequest(contribution=0)` raises Pydantic
      `ValidationError`.
- [ ] 6.2 Create `tests/test_rebalance_glue.py` (integration
      marker): build a profile with 2 classes + 5 assets via
      the existing factories, call `run_rebalance(db, profile,
      contribution=5000.0)`, assert response shape (asset_plan
      length, category_plan length, metrics.contribution,
      warnings); inject a custom sentinel solver and assert the
      sentinel output appears in the response; assert
      `EMPTY_PROFILE` warning appears for a profile with zero
      classes.
- [ ] 6.3 Create `tests/test_rebalance_route.py` (integration
      marker): `POST /api/rebalance` via `TestClient` with a
      valid session, assert 200 + response shape; assert 422
      for `contribution=0`; assert 401 for unauthenticated
      request; assert 400 when the bridge raises
      `RebalanceValidationError` (force via a profile whose
      class `target_pct` sums don't reach 100% — or by mocking
      `build_setup_from_db` to raise).
- [ ] 6.4 Edit `tests/conftest.py::_INTEGRATION_PREFIXES` to
      add the prefixes `tests/test_rebalance_route`,
      `tests/test_rebalance_glue`, and `tests/test_rebalance_schemas`
      so the three new files get the `integration` marker
      (per AGENTS.md "Test marker rule — explicit allow-list,
      not pattern matching").
- [ ] 6.5 If `tests/fixtures/` does not yet have an
      `__init__.py`, create one so the JSON fixture is
      importable from `tests/conftest.py` if needed.

## 7. Verification

- [ ] 7.1 Run `uv run task test-unit` — confirm no regressions
      in the unit subset.
- [ ] 7.2 Run `uv run task test-integration` — confirm the
      three new integration files pass and the marker rule
      does not emit `UnknownTestPath` warnings.
- [ ] 7.3 Run `uv run task lint` — confirm ruff format + check
      are clean on all new files.
- [ ] 7.4 Manual smoke: start the server with `uv run task serve`,
      curl `POST /api/rebalance` from the LAN URL
      (`http://192.168.1.6:8000/api/rebalance`) with a valid
      session cookie and `{"contribution": 5000.00}` body,
      confirm a 200 response with a populated `asset_plan`,
      `category_plan`, `metrics`, and `warnings`. Document the
      curl invocation in the change summary for the operator.
- [ ] 7.5 Update `.planning/REBALANCE_PLAN.md` to mark Phase 3
      as split into `rebalance-route` (this change) +
      `rebalance-page` (next change).
