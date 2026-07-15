## Context

`test_seed_from_csv.py` has 20 tests marked `xdist_group("serial")`. Each test calls the `omaha_db` fixture which:

1. Saves `omaha.*` modules from `sys.modules`
2. Creates a tmp SQLite file
3. Sets `DATABASE_URL`, `ADMIN_PASSWORD`, `SECRET_KEY` env vars
4. Calls `run_alembic_and_seed(REPO_ROOT, db_url)` — spawns 2 subprocesses
5. Clears `omaha.*` from `sys.modules`, reimports `omaha.config`, `omaha.db`, `omaha.models`
6. Registers finalizer to restore original modules

Step 4 is the bottleneck: ~2.5s per test. Steps 1–3 + 5–6 are ~10ms total.

The tests fall into three categories:

| Category | Tests | Needs DB? | Mutates CSV? |
|---|---|---|---|
| Reset-only (read after reset) | 1, 3, 9, 10, 11, 12, 13, 19 | Yes | No |
| DB/CSV mutators | 2, 4, 5, 6, 7, 8, 18, 20 | Yes | Some |
| Loader-only | 14, 15, 16, 17 | No | No |

## Goals / Non-Goals

**Goals:**
- Run `run_alembic_and_seed` once per pytest session, not once per test
- Copy the resulting SQLite file for each test that needs a DB (~10ms vs ~2.5s)
- Remove `omaha_db` dependency from loader-only tests
- Keep all 20 tests, same assertions, same serial execution, same coverage

**Non-Goals:**
- Changing test assertions or adding/removing tests
- Making tests parallelizable (CSV file mutation still requires serial execution)
- Changing `scripts/seed_from_csv` or `tests/support/db.py` public API
- Changing the subprocess invocation in `_run_seed` (that's the behavior under test)

## Decisions

### D1 — Session-scoped snapshot fixture

**Choice**: Add `_seed_db_snapshot` as a `session`-scoped fixture in `test_seed_from_csv.py`. It calls `run_alembic_and_seed` once and stores the resulting SQLite file path. The per-test `omaha_db` fixture copies this file via `shutil.copy2` instead of re-running migration + seed.

**Why**: The migration + seed subprocess calls are the dominant cost (~2.5s). SQLite files are small (~50–100KB). File copy is ~10ms. The snapshot captures the post-seed state (users, profiles, alembic version) that most tests need as their starting point.

**Alternative considered**: Make `omaha_db` session-scoped directly. Rejected — CSV-mutating tests modify shared `data/seed/*.csv` files and need per-test isolation.

### D2 — Module save/restore stays per-test

**Choice**: Keep the `_save_modules` / `_restore_modules` dance inside the per-test `omaha_db` fixture. Each test still clears `sys.modules` and reimports `omaha.db` so `SessionLocal` binds to the test's own SQLite copy.

**Why**: SQLAlchemy's `SessionLocal` binds to the engine at import time. Different tests need different SQLite files (especially mutators). The module reimport is the mechanism that rebinds. Cost is ~10ms — negligible.

### D3 — Loader tests drop `omaha_db`

**Choice**: Tests 14–17 remove `omaha_db` from their signature. They only use `tmp_path` and `monkeypatch` for CSV parsing via `scripts.seed_from_csv.load_*` functions.

**Why**: These tests never call `SessionLocal`, never run `_run_seed`, never touch the database. The fixture was cargo-cult — removing it eliminates 4 unnecessary `run_alembic_and_seed` calls (10s saved).

### D4 — CSV-mutating tests get own copy + CSV backup

**Choice**: Tests that modify `data/seed/*.csv` (6, 7, 8, 18) continue to backup/restore CSV files in try/finally. Their `omaha_db` fixture copies the snapshot DB (not shared with other tests).

**Why**: CSV mutations are destructive and test-specific. The existing try/finally pattern already handles this. The only change is the DB source: snapshot copy instead of fresh `run_alembic_and_seed`.

### D5 — Snapshot creation in session fixture, not conftest

**Choice**: The snapshot fixture lives in `test_seed_from_csv.py`, not in `tests/conftest.py` or `tests/support/db.py`.

**Why**: The snapshot is specific to `test_seed_from_csv.py`'s needs (canonical Italo seed state). Other test files use the session-scoped `_SAFE_DATABASE` from conftest for their own DB. Putting the snapshot here keeps the change isolated and avoids coupling.

## Risks / Trade-offs

- **[Risk] Snapshot corruption**: If the session fixture fails partway through `run_alembic_and_seed`, the snapshot file is incomplete. → Mitigation: `run_alembic_and_seed` already asserts `returncode == 0`; failure aborts the session.
- **[Risk] Test isolation**: If a test mutates the snapshot file directly (not a copy), subsequent tests see stale state. → Mitigation: each test gets its own copy via `shutil.copy2` to `tmp_path`.
- **[Trade-off] Snapshot shared across xdist workers**: Under `pytest -n auto`, each worker has its own session, so each creates its own snapshot. No cross-worker sharing issue. The `xdist_group("serial")` marker keeps all 20 tests in one worker anyway.
- **[Trade-off] File copy vs in-memory**: SQLite file copy to `tmp_path` is simple but creates disk I/O. Acceptable — `tmp_path` is typically a tmpfs or SSD-backed directory.
