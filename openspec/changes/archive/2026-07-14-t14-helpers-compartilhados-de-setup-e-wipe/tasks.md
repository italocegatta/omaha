# T14 — Tasks

## 1. Create `tests/support/constants.py`
- [ ] Extract `REPO_ROOT`, `TEST_ADMIN_PASSWORD`, `TEST_SECRET_KEY` from e2e conftest
- [ ] Verify no circular imports (constants must not import omaha.*)

## 2. Create `tests/support/hooks.py`
- [ ] Extract `remember_call_report` and `make_report_hook` from e2e conftest
- [ ] Import pytest only inside function body to avoid collection-time side effects

## 3. Create `tests/support/server.py`
- [ ] Implement `run_test_server` context manager
- [ ] Uses `compose_server_env`, `uvicorn_log_file`, `wait_for_port`, `shutdown_uvicorn` from `browser.py`
- [ ] Handles port-in-use, startup timeout, and teardown logging

## 4. Move `_HarnessPage` to `tests/support/browser.py`
- [ ] Copy class + `_GOTO_INTERRUPT_RE` regex
- [ ] Update `tests/e2e/conftest.py` to import from `tests.support.browser`
- [ ] Update `tests/bdd/conftest.py` if it re-exports (check)

## 5. Move `_set_asset_target_pcts_via_db` to `tests/support/db.py`
- [ ] Rename to `set_asset_target_pcts_via_db` (drop private prefix)
- [ ] Update `tests/e2e/conftest.py` import

## 6. Move `_seed_assets_with_positions_via_import` to `tests/support/import_flow.py`
- [ ] Move function + its uuid import
- [ ] Update `tests/e2e/conftest.py` import

## 7. Consolidate login helpers
- [ ] Move visual's `login_as_italo` into `tests/support/import_flow.py`
- [ ] Reuse `SELECTORS` from `tests/e2e/selectors.py` (already imported by import_flow)
- [ ] Update `tests/visual/conftest.py` to import from `tests.support.import_flow`

## 8. Rewire `tests/e2e/conftest.py`
- [ ] Import constants from `tests.support.constants`
- [ ] Import hooks from `tests.support.hooks`
- [ ] Replace `_start_uvicorn` + `live_url` / `live_url_short_ttl` with `run_test_server`
- [ ] Remove duplicated code
- [ ] Run `task test-e2e` — must pass

## 9. Rewire `tests/bdd/conftest.py`
- [ ] Import constants from `tests.support.constants`
- [ ] Import hooks from `tests.support.hooks`
- [ ] Replace inline uvicorn start with `run_test_server`
- [ ] Remove `_wait_for_bdd_port` (now handled by `run_test_server`)
- [ ] Run `task test-bdd` — must pass

## 10. Rewire `tests/visual/conftest.py`
- [ ] Import constants from `tests.support.constants`
- [ ] Replace inline uvicorn start with `run_test_server`
- [ ] Remove local `login_as_italo` → import from `tests.support.import_flow`
- [ ] Run `task test-visual` — must pass

## 11. Final verification
- [ ] Run `task test-unit` — no regressions
- [ ] Run `task test-integration` — no regressions
- [ ] Run `task test-bdd` — no regressions
- [ ] Run `task test-e2e` — no regressions
- [ ] Run `task test-visual` — no regressions
- [ ] Run `task lint` — no new warnings
