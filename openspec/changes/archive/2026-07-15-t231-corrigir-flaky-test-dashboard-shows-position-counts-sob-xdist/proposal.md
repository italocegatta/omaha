## Why

`test_dashboard_shows_position_counts` fails 100% under `pytest-xdist` parallel execution but passes in isolation. Root cause: the test writes to the shared SQLite DB via ORM (`_ensure_class_with_asset`) then runs a CSV import + confirm flow. Under xdist, other workers' concurrent DB mutations corrupt the preview/session state. This blocks the pre-push hook (`task test-integration-parallel`), preventing pushes.

## What Changes

- Add `pytestmark = pytest.mark.xdist_group("serial")` to `tests/test_imports_routes.py` so the entire module runs in a single serial group under xdist. This is the established pattern (used in `test_seed_from_csv.py`, `test_snapshot_to_csv.py`, `test_real_csv_flow.py`, `test_db_reset_both_profiles.py`).

## Capabilities

### New Capabilities

None. This is a test-infrastructure fix, not a product capability.

### Modified Capabilities

None. No spec-level behavior changes.

## Impact

- **Files**: `tests/test_imports_routes.py` (1 line added).
- **Tests**: `test_dashboard_shows_position_counts` and all other tests in `test_imports_routes.py` will run serially under xdist. Wall-clock impact minimal — the module has ~12 tests, all lightweight HTTP + ORM.
- **CI**: pre-push hook (`task test-integration-parallel`) unblocked.
