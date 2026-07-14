# test-worker-db-isolation Specification

## Purpose

Enable safe parallel execution of integration tests by provisioning an independent SQLite database for each pytest-xdist worker, preventing shared-state corruption when multiple workers run concurrently.

## Requirements

### Requirement: Each xdist worker SHALL get its own SQLite database

When `pytest-xdist` is active (detected via `PYTEST_XDIST_WORKER` environment variable), each worker process SHALL provision its own temporary SQLite database. The database SHALL be independent — no shared file, no shared connection, no shared state between workers.

#### Scenario: Worker gw0 gets its own DB
- **WHEN** pytest runs with `-n 2` and worker `gw0` starts
- **THEN** `gw0` binds `SessionLocal` to a SQLite file in a tempdir unique to `gw0`
- **AND** the file path contains the worker ID (e.g., `omaha-worker-gw0-`)

#### Scenario: Worker gw1 gets a different DB
- **WHEN** pytest runs with `-n 2` and worker `gw1` starts
- **THEN** `gw1` binds `SessionLocal` to a different SQLite file
- **AND** `gw0` and `gw1` databases are fully independent

#### Scenario: Workers do not share tempdir
- **WHEN** two workers provision their databases
- **THEN** each worker's tempdir is distinct
- **AND** no worker reads or writes another worker's tempdir

### Requirement: Worker DB SHALL be migrated and seeded

Each worker's database SHALL have the same schema and seed data as the existing session-scoped test database. The alembic migration (`upgrade head`) and the idempotent seed (`omaha.seed.seed()`) SHALL run per-worker at startup.

#### Scenario: Worker DB has current schema
- **WHEN** a worker provisions its database
- **THEN** `alembic upgrade head` runs against the worker's `DATABASE_URL`
- **AND** the worker's DB has all tables and columns matching the latest migration

#### Scenario: Worker DB is seeded
- **WHEN** a worker provisions its database
- **THEN** `omaha.seed.seed()` runs after migration
- **AND** the worker's DB contains the family and profile seed data

### Requirement: Serial mode SHALL be unaffected

When `PYTEST_XDIST_WORKER` is not set (serial execution, the default), the existing `prepare_safe_test_database()` behavior SHALL remain unchanged. The session-scoped tempdir, env vars, import binding, migration, and seed all execute exactly as before.

#### Scenario: Serial run uses session-scoped DB
- **WHEN** pytest runs without `-n` flag
- **THEN** `PYTEST_XDIST_WORKER` is not set
- **AND** `prepare_safe_test_database()` executes (not the worker path)
- **AND** all tests share one session-scoped SQLite file

#### Scenario: Serial run prod-DB guard still works
- **WHEN** pytest runs serially and `SessionLocal` is bound
- **THEN** `verify_session_local_is_safe()` still raises `RuntimeError` if bound to `data/portfolio.db`

### Requirement: Worker tempdir SHALL be self-contained

Each worker's tempdir SHALL contain `portfolio.db` and a `snapshots/` subdirectory, mirroring the existing session-scoped layout. Environment variables (`DATABASE_URL`, `SNAPSHOT_SOURCE`, `SNAPSHOT_DEST_DIR`) SHALL point to the worker's tempdir.

#### Scenario: Worker env vars point to worker DB
- **WHEN** worker `gw2` provisions its database
- **THEN** `os.environ["DATABASE_URL"]` contains the worker's DB path
- **AND** `os.environ["SNAPSHOT_SOURCE"]` points to the worker's `portfolio.db`
- **AND** `os.environ["SNAPSHOT_DEST_DIR"]` points to the worker's `snapshots/`

### Requirement: Parallel integration task SHALL be available

A `test-integration-parallel` taskipy task SHALL exist that runs integration tests with `pytest-xdist` (`-n auto`). The existing `test-integration` task SHALL remain unchanged as a serial fallback.

#### Scenario: Parallel task runs with xdist
- **WHEN** user runs `uv run task test-integration-parallel`
- **THEN** pytest runs with `-m integration --ignore=tests/audit_integration -n auto`
- **AND** each worker gets its own DB

#### Scenario: Serial task is unchanged
- **WHEN** user runs `uv run task test-integration`
- **THEN** pytest runs without `-n` flag
- **AND** tests run serially with session-scoped DB
