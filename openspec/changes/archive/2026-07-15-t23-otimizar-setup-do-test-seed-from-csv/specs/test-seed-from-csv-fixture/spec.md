## MODIFIED Requirements

### Requirement: omaha_db fixture provides per-test isolated SQLite

The `omaha_db` fixture in `tests/test_seed_from_csv.py` SHALL provide each test with an isolated SQLite database backed by a per-test temporary file. The fixture SHALL copy from a session-scoped snapshot (created once via `run_alembic_and_seed`) rather than re-running migration + seed per test.

#### Scenario: Snapshot created once per session

- **WHEN** the pytest session starts and `test_seed_from_csv.py` tests are collected
- **THEN** `run_alembic_and_seed` executes exactly once (session-scoped), producing a snapshot SQLite file containing the canonical Italo seed state

#### Scenario: Per-test copy from snapshot

- **WHEN** a test requests the `omaha_db` fixture
- **THEN** the fixture copies the snapshot SQLite file to `tmp_path`, sets `DATABASE_URL` to the copy, clears and reimports `omaha.*` modules so `SessionLocal` binds to the copy, and returns `{"db_url": ..., "SessionLocal": ...}`

#### Scenario: Module restore on teardown

- **WHEN** a test using `omaha_db` completes
- **THEN** the fixture's finalizer restores the original `sys.modules` state (same as pre-refactor behavior)

### Requirement: Loader tests do not require omaha_db

Tests that only exercise CSV parsing (`load_classes`, `load_assets`, `load_positions`) SHALL NOT depend on the `omaha_db` fixture. They SHALL use only `tmp_path` and `monkeypatch`.

#### Scenario: Loader test runs without database

- **WHEN** `test_auto_class_fixture_loads_with_quote_kind` runs
- **THEN** it succeeds without the `omaha_db` fixture, using only `tmp_path` for temporary CSV files and `monkeypatch` for `SEED_DIR` override

#### Scenario: Loader tests do not trigger run_alembic_and_seed

- **WHEN** the 4 loader tests (14–17) run
- **THEN** `run_alembic_and_seed` is not called for them (it was called once at session start for the snapshot, but these tests don't consume the snapshot)
