# shared-test-support Delta Specification

## Purpose

Extend the shared DB bootstrap helpers to support per-worker database provisioning for pytest-xdist parallel execution, while preserving existing session-scoped behavior for serial runs.

## MODIFIED Requirements

### Requirement: Shared DB cleanup primitives are centralized

The system SHALL provide shared cleanup helpers under `tests/support/` (or equivalent support package) that implement the current DB wipe semantics used by the suite conftests and by `scripts/seed_from_csv/modes.py`.

The helpers SHALL:

- keep existing SQLite `PRAGMA busy_timeout = 3000` behavior where used
- short-circuit when DB or profile is absent
- delete positions before assets, assets before asset_classes, and import_previews in the same cleanup flow
- preserve orphan cleanup used by seed reset where relevant

#### Scenario: cleanup helper reused across suites

- **WHEN** e2e, bdd, or visual imports the shared cleanup helper for a populated profile
- **THEN** the same rows are deleted as before
- **AND** no orphan rows remain
- **AND** missing DB or profile still returns without exception

#### Scenario: cleanup helper works with per-worker DB

- **WHEN** an xdist worker's test calls the cleanup helper
- **THEN** the helper operates on the worker's own `DATABASE_URL`
- **AND** other workers' databases are unaffected

## ADDED Requirements

### Requirement: Worker-aware DB bootstrap function

The system SHALL provide a `prepare_worker_database()` function in `tests/support/db.py` that provisions a per-worker SQLite database. The function SHALL:

- Accept a worker ID string (from `PYTEST_XDIST_WORKER` env var)
- Create a tempdir named `omaha-worker-{id}-`
- Set `DATABASE_URL`, `SNAPSHOT_SOURCE`, `SNAPSHOT_DEST_DIR`, `SECRET_KEY`, `ADMIN_PASSWORD`, `OMAHA_SKIP_STARTUP`, `OMAHA_ENV` environment variables
- Import `omaha.config`, `omaha.db`, `omaha.seed` to bind `SessionLocal`
- Run `alembic upgrade head` in a subprocess
- Run `omaha.seed.seed()`
- Return a `SafeTestDatabase` dataclass with the worker's paths

#### Scenario: Worker DB provisioning sets all env vars

- **WHEN** `prepare_worker_database("gw0")` is called
- **THEN** `os.environ["DATABASE_URL"]` is set to `sqlite:///.../omaha-worker-gw0-.../portfolio.db`
- **AND** `os.environ["SECRET_KEY"]` is set to the test secret key
- **AND** `os.environ["OMAHA_SKIP_STARTUP"]` is `"1"`

#### Scenario: Worker DB provisioning runs migrations

- **WHEN** `prepare_worker_database("gw1")` is called
- **THEN** `alembic upgrade head` runs against the worker's database
- **AND** the return value's `path` points to a migrated SQLite file

#### Scenario: Worker DB provisioning seeds data

- **WHEN** `prepare_worker_database("gw2")` is called
- **THEN** `omaha.seed.seed()` runs after migration
- **AND** the worker's database contains the family and profile rows
