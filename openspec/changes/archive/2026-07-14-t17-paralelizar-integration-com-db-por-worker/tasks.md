## 1. Dependency setup

- [x] 1.1 Add `pytest-xdist` to `[dependency-groups] dev` in `pyproject.toml`
- [x] 1.2 Run `uv sync` to install the new dependency

## 2. Worker DB isolation in tests/support/db.py

- [x] 2.1 Create `prepare_worker_database(worker_id: str, repo_root: Path) -> SafeTestDatabase` function in `tests/support/db.py` that provisions a per-worker tempdir with `portfolio.db` and `snapshots/`, sets all required env vars (`DATABASE_URL`, `SNAPSHOT_SOURCE`, `SNAPSHOT_DEST_DIR`, `SECRET_KEY`, `ADMIN_PASSWORD`, `OMAHA_SKIP_STARTUP`, `OMAHA_ENV`), imports `omaha.config`, `omaha.db`, `omaha.seed` to bind `SessionLocal`, runs `alembic upgrade head` via subprocess, and runs `omaha.seed.seed()`
- [x] 2.2 Ensure `prepare_worker_database` reuses existing `run_alembic_upgrade` helper and test constants (`TEST_SECRET_KEY`, `TEST_ADMIN_PASSWORD`)

## 3. Conftest worker detection in tests/conftest.py

- [x] 3.1 Add worker-detection branch in the module-load block: if `PYTEST_XDIST_WORKER` env var is set, call `prepare_worker_database(worker_id, repo_root)` instead of `prepare_safe_test_database()`
- [x] 3.2 Ensure `_SAFE_DB_FILE` and `_SAFE_SNAPSHOT_DIR` are set from the worker's `SafeTestDatabase` when in worker mode
- [x] 3.3 Preserve existing serial behavior when `PYTEST_XDIST_WORKER` is not set — no changes to the `prepare_safe_test_database()` call path
- [x] 3.4 Verify `verify_session_local_is_safe()` still works in both worker and serial modes

## 4. Taskipy task for parallel integration

- [x] 4.1 Add `test-integration-parallel` task in `pyproject.toml` `[tool.taskipy.tasks]` that runs `uv run pytest -m integration --ignore=tests/audit_integration -n auto --dist loadgroup --cov=src/omaha --cov-report=xml:reports/coverage.xml`
- [x] 4.2 Verify existing `test-integration` task is unchanged (serial fallback)

## 5. CSV-mutating test serialization

- [x] 5.0 Mark `test_seed_from_csv.py`, `test_snapshot_to_csv.py`, `test_real_csv_flow.py`, `test_db_reset_both_profiles.py` with `pytestmark = pytest.mark.xdist_group("serial")` to prevent CSV file races across parallel workers. Register `xdist_group` marker in `pyproject.toml`.

## 6. Verification

- [x] 6.1 Run `uv run task test-integration` and confirm serial execution still passes (regression check) — 384 passed, 2 failed (pre-existing `test_pages_routes.py` colgroup issues), 2 skipped, 5:34 wall-clock
- [x] 6.2 Run `uv run task test-integration-parallel` and confirm parallel execution passes with multiple workers — 384 passed, 2 failed (same pre-existing), 2 skipped, 2:44 wall-clock (~48% speedup)
- [x] 6.3 Compare wall-clock time: serial 5:34 vs parallel 2:44 (~48% speedup, ~2× faster)
- [x] 6.4 Run `uv run task test-unit` to confirm no unit test regression — 349 passed, 2 skipped, 18s
