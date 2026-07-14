## Why

Integration test wall-clock is ~3min (down from 5:34 after T17 parallelization). Three hotspots consume disproportionate time repeating identical bootstrap/alembic/seed setup: `test_audit_inventory` (~11s), `test_db_reset_both_profiles` (~4.5s), and `test_seed_from_csv` (~3s+). Each test or fixture independently spawns `alembic upgrade head` subprocesses and re-imports `omaha.*` modules, duplicating work that the session-scoped conftest already performed. Cutting this repeated setup can shave 15-20s off the integration suite and establish patterns for future test files.

## What Changes

- Extract reusable `alembic upgrade head` + seed helpers into `tests/support/db.py` so hotspot tests avoid subprocess duplication
- Convert `test_audit_inventory` module-scoped fixtures (`jinja_env`, `stylesheet`, `factory`) to session-scoped where safe, or cache the expensive parsed CSS/Jinja objects
- Refactor `test_seed_from_csv` `omaha_db` fixture to reuse the shared alembic helper instead of inline subprocess + module juggling
- Refactor `test_db_reset_both_profiles` to reuse shared alembic + seed helpers instead of inline `_run_alembic` + subprocess seed
- Maintain test isolation: each test file or xdist worker still gets its own DB; no cross-contamination

## Capabilities

### New Capabilities

_None — this change modifies existing test infrastructure only._

### Modified Capabilities

- `shared-test-support`: Add reusable `run_alembic_and_seed()` helper that combines migration + seed in one call; add `make_test_env()` helper for env dict composition; refactor hotspot tests to consume these helpers
- `test-worker-db-isolation`: No requirement changes — worker isolation contract stays identical; only internal implementation of helpers changes

## Impact

- **Files modified**: `tests/support/db.py`, `tests/test_audit_inventory.py`, `tests/test_db_reset_both_profiles.py`, `tests/test_seed_from_csv.py`
- **No production code changes** — test infrastructure only (T-prefix slice)
- **No API or dependency changes**
- **Risk**: Low — test behavior and assertions unchanged; only setup/teardown plumbing is refactored
- **Expected savings**: ~15-20s wall-clock reduction on integration suite
