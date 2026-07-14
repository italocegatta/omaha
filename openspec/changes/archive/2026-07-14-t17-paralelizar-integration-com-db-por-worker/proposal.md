## Why

Integration lane (`task test-integration`) takes >3 min wall-clock and is the main bottleneck in the pre-merge flow. The suite runs serially because all tests share a single session-scoped SQLite database. Enabling `pytest-xdist` without per-worker DB isolation corrupts shared state. This slice gives each xdist worker its own temporary SQLite database so integration tests can run in parallel safely.

## What Changes

- Add `pytest-xdist` to dev dependencies
- Create a per-worker DB isolation layer in `tests/support/db.py` that provisions a fresh SQLite database when xdist is active (worker-scoped, not session-scoped)
- Update `tests/conftest.py` to detect xdist workers and bind each worker to its own DB instead of sharing the session-scoped one
- Add a `test-integration-parallel` taskipy task that runs integration tests with `-n auto`
- Keep the serial `test-integration` task unchanged as fallback
- Document the parallel execution model in the test suite docs

## Capabilities

### New Capabilities
- `test-worker-db-isolation`: Per-worker database isolation for pytest-xdist integration lane — each worker gets its own SQLite DB with independent alembic migration and seed, preventing shared-state corruption under parallel execution.

### Modified Capabilities
- `shared-test-support`: DB bootstrap helpers gain worker-aware branching — when xdist worker ID is detected, provision per-worker DB; otherwise fall back to existing session-scoped behavior.

## Impact

- `pyproject.toml`: new dev dependency (`pytest-xdist`), new taskipy task
- `tests/support/db.py`: new worker-scoped DB provisioning logic
- `tests/conftest.py`: conditional binding based on `PYTEST_XDIST_WORKER` env var
- No production code changes
- No CI workflow changes (GH Actions deferred per owner)
