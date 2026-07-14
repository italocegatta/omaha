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

### Requirement: Shared browser/bootstrap primitives are centralized

The system SHALL provide shared helpers under `tests/support/` for browser and uvicorn bootstrap concerns used by `tests/e2e/conftest.py` and `tests/visual/conftest.py`, including chromium resolution, port readiness, setup env composition, and uvicorn shutdown.

Existing host, port, launch args, and browser-selection order SHALL remain unchanged.

#### Scenario: e2e and visual launch through same helper

- **WHEN** either suite launches browser/server via shared helper
- **THEN** chromium selection still honors the current path order
- **AND** launch still uses the same headless/no-sandbox args
- **AND** ports and env remain unchanged

### Requirement: Import journey setup helpers are reusable

The system SHALL provide shared helpers for login, class creation, asset seeding, and debug-dump support used by `tests/e2e/test_import_user_journey.py`.

The test module MAY keep only scenario orchestration and final assertions.

#### Scenario: import journey still builds canonical setup

- **WHEN** the import journey test runs
- **THEN** shared helper still logs in as Italo, creates 3 classes, seeds 43 assets, and reaches same 48-row end state
- **AND** the file-level assertions remain the source of truth

## ADDED Requirements

### Requirement: Combined alembic-migration-and-seed helper

The system SHALL provide a `run_alembic_and_seed()` function in `tests/support/db.py` that runs `alembic upgrade head` followed by `omaha.seed.seed()` against a given database URL in a single call.

The function SHALL:

- Accept `repo_root: Path` and `db_url: str` parameters
- Build the env dict using `make_test_env(db_url)` (see below)
- Call `run_alembic_upgrade(repo_root, db_url)` for the migration step
- Call `omaha.seed.seed()` for the seed step
- Return without value; raise on failure

#### Scenario: single-call migration and seed

- **WHEN** `run_alembic_and_seed(repo_root, db_url)` is called
- **THEN** `alembic upgrade head` runs against `db_url`
- **AND** `omaha.seed.seed()` runs after migration
- **AND** the database contains family and profile rows

#### Scenario: used by hotspot test fixtures

- **WHEN** `test_seed_from_csv.omaha_db` or `test_db_reset_both_profiles` provisions a test DB
- **THEN** the fixture calls `run_alembic_and_seed()` instead of inline subprocess + seed
- **AND** the test behavior and assertions are unchanged

### Requirement: Subprocess env dict composition helper

The system SHALL provide a `make_test_env(db_url: str) -> dict[str, str]` function in `tests/support/db.py` that returns a complete env dict for subprocess calls targeting a test database.

The function SHALL return a dict containing:

- `DATABASE_URL` set to the provided `db_url`
- `ADMIN_PASSWORD` set to `TEST_ADMIN_PASSWORD`
- `SECRET_KEY` set to `TEST_SECRET_KEY`
- `OMAHA_SKIP_STARTUP` set to `"1"`
- `OMAHA_ENV` set to `"development"`
- All other `os.environ` entries preserved

#### Scenario: env dict used for seed subprocess

- **WHEN** `make_test_env("sqlite:///tmp/test.db")` is called
- **THEN** the returned dict has `DATABASE_URL` = `"sqlite:///tmp/test.db"`
- **AND** `ADMIN_PASSWORD` = `"test-password"`
- **AND** `SECRET_KEY` = `"test-secret-do-not-use"`

#### Scenario: env dict used for alembic subprocess

- **WHEN** a test calls `subprocess.run([..., "alembic", "upgrade", "head"], env=make_test_env(url))`
- **THEN** alembic reads the correct `DATABASE_URL` from the env dict
- **AND** migrations apply to the intended database
