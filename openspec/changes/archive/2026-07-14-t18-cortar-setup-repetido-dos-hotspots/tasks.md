## 1. Shared helpers in tests/support/db.py

- [x] 1.1 Add `make_test_env(db_url: str) -> dict[str, str]` function that returns env dict with `DATABASE_URL`, `ADMIN_PASSWORD`, `SECRET_KEY`, `OMAHA_SKIP_STARTUP`, `OMAHA_ENV` plus `os.environ`
- [x] 1.2 Add `run_alembic_and_seed(repo_root: Path, db_url: str)` function that calls `run_alembic_upgrade()` + `omaha.seed.seed()` in one shot
- [x] 1.3 Add docstring to `make_test_env` and `run_alembic_and_seed` documenting the contract and usage pattern

## 2. Refactor test_audit_inventory fixtures

- [x] 2.1 Promote `jinja_env` fixture from `scope="module"` to `scope="session"` in `test_audit_inventory.py`
- [x] 2.2 Promote `stylesheet` fixture from `scope="module"` to `scope="session"` in `test_audit_inventory.py`
- [x] 2.3 Add docstring note that session-scoped fixtures are read-only (production files don't change during test run)
- [x] 2.4 Run `task test-integration -- -k test_audit_inventory` to verify all 16 tests pass

## 3. Refactor test_db_reset_both_profiles

- [x] 3.1 Replace inline `_set_test_env()` with `make_test_env()` from `tests.support.db`
- [x] 3.2 Replace inline `_run_alembic()` with `run_alembic_upgrade()` from `tests.support.db`
- [x] 3.3 Keep the subprocess calls for `omaha.seed` and `scripts.reset_both_profiles` (these are the actual test subjects)
- [x] 3.4 Run `task test-integration -- -k test_db_reset_both_profiles` to verify test passes

## 4. Refactor test_seed_from_csv omaha_db fixture

- [x] 4.1 Replace inline alembic subprocess + env dict in `omaha_db` fixture with `run_alembic_and_seed()` from `tests.support.db`
- [x] 4.2 Replace inline env dict in `_run_seed()` helper with `make_test_env()` from `tests.support.db`
- [x] 4.3 Keep the module save/restore dance (`_save_modules` / `_restore_modules`) — needed for CSV mutation isolation
- [x] 4.4 Run `task test-integration -- -k test_seed_from_csv` to verify all 20 tests pass

## 5. Verification

- [x] 5.1 Run `task test-integration` — full integration suite passes
- [x] 5.2 Compare wall-clock time before/after (target: ~15-20s savings)
- [x] 5.3 Run `task test-unit` — unit suite unaffected
