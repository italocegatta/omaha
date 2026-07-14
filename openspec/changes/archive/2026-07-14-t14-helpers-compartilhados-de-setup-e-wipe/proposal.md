# T14 — Helpers compartilhados de setup e wipe

## Problem

Test harness code is duplicated across conftest files:

| Pattern | e2e/conftest.py | bdd/conftest.py | visual/conftest.py | tests/support/ |
|---|---|---|---|---|
| Uvicorn start/wait/yield/shutdown | full impl `_start_uvicorn` + `live_url` | inline copy of same pattern | inline copy | `browser.py` has primitives but no composed lifecycle |
| `pytest_runtest_makereport` hook | yes | yes (identical) | no | — |
| `REPO_ROOT` / `TEST_ADMIN_PASSWORD` / `TEST_SECRET_KEY` | defined locally | defined locally | defined locally | `db.py` has its own `TEST_SECRET_KEY` / `TEST_ADMIN_PASSWORD` |
| `login_as_italo` | no | no | local impl | `import_flow.py` has `login_and_select_italo` (close duplicate) |
| `_seed_assets_with_positions_via_import` | local impl | no | no | not shared |
| `_set_asset_target_pcts_via_db` | local impl | no | no | not shared |
| `_HarnessPage` goto guard | local class | re-exported from e2e | no | not shared |

Consequences:
- Changing server startup teardown requires editing 3+ files.
- Password/secret drift possible (e2e uses one value, bdd another — currently same by copy-paste).
- Visual conftest reimplements login instead of reusing `import_flow`.
- `_seed_assets_with_positions_via_import` and `_set_asset_target_pcts_via_db` are useful beyond e2e but locked in e2e conftest.

## Non-goals

- **No behavior change.** Test suite must pass identically before/after.
- **No marker/hook refactoring.** `pytest_collection_modifyitems` stays in root conftest.
- **No changes to `scripts/seed_from_csv/`.** Production seed code is out of scope.
- **No new test files.** Only conftest + support module changes.

## Approach

1. **Centralize constants** in `tests/support/` — single source for `REPO_ROOT`, `TEST_ADMIN_PASSWORD`, `TEST_SECRET_KEY`.
2. **Extract uvicorn server lifecycle** into `tests/support/server.py` — a `run_test_server(db_path, port, extra_env)` context manager that wraps start/wait/yield/shutdown.
3. **Extract shared hooks** (`pytest_runtest_makereport` + `_remember_call_report`) into `tests/support/hooks.py`.
4. **Move `_HarnessPage`** to `tests/support/browser.py` (already has browser primitives).
5. **Move `_seed_assets_with_positions_via_import`** to `tests/support/import_flow.py`.
6. **Move `_set_asset_target_pcts_via_db`** to `tests/support/db.py`.
7. **Unify login helpers** — visual's `login_as_italo` becomes a thin wrapper or direct call to `login_and_select_italo`.
8. **Slim conftest files** — each becomes a thin composition layer that imports from `tests/support/` and wires fixtures.

## Risk

Low. Refactoring test infrastructure only. No production code touched. Each step is independently verifiable by running the affected test subset.
