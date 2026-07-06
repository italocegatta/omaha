# ci-coverage-pipeline Specification

## Purpose

Defines the project's continuous-integration wiring: which jobs run on push / pull_request, in which order, which taskipy tasks each job invokes, and how `pytest-cov` integrates with the coverage driver via the XML artifact at `reports/coverage.xml`. Backed by `.github/workflows/ci.yml` at the repo root and by the `[tool.coverage.*]` + `[tool.pytest.ini_options]` blocks in `pyproject.toml`.

## ADDED Requirements

### Requirement: CI workflow triggers on push and pull_request

The repository SHALL include a GitHub Actions workflow at `.github/workflows/ci.yml` that triggers on `push` to the default branch and on `pull_request` targeting the default branch.

#### Scenario: Push to main triggers the workflow

- **WHEN** a commit is pushed to the default branch
- **THEN** the workflow `ci.yml` starts
- **AND** it runs the `lint`, `test-unit`, `test-integration`, `test-bdd`, and `coverage` jobs (in that order, with coverage running only after the test jobs complete)

#### Scenario: Pull request against main triggers the workflow

- **WHEN** a pull request is opened or updated against the default branch
- **THEN** the workflow `ci.yml` starts
- **AND** it runs the same job set as a push event

### Requirement: Lint job runs ruff check and ruff format

The workflow SHALL include a `lint` job that runs `ruff check` and `ruff format --check` on `src/`, `tests/`, and `alembic/`. The job MUST fail the workflow if either check reports an error.

#### Scenario: Ruff check passes and workflow proceeds

- **WHEN** the `lint` job executes
- **AND** `ruff check` reports no errors
- **THEN** the job reports success
- **AND** the `test-unit` job starts

#### Scenario: Ruff check fails and workflow fails

- **WHEN** the `lint` job executes
- **AND** `ruff check` reports one or more errors
- **THEN** the job reports failure
- **AND** the `test-unit` job does NOT start

### Requirement: Test jobs invoke the taskipy tasks

The workflow SHALL run `task test-unit`, `task test-integration`, and `task test-bdd` as separate jobs in that order. Each job MUST install dependencies via `uv sync --frozen --extra dev` before running the task.

#### Scenario: Unit job runs task test-unit

- **WHEN** the `test-unit` job executes
- **THEN** it runs `uv run task test-unit`
- **AND** the job reports success when the task exits 0

#### Scenario: Integration job runs task test-integration

- **WHEN** the `test-integration` job executes
- **THEN** it runs `uv run task test-integration`
- **AND** the job reports success when the task exits 0

#### Scenario: BDD job runs task test-bdd

- **WHEN** the `test-bdd` job executes
- **THEN** it runs `uv run task test-bdd`
- **AND** the job reports success when the task exits 0

### Requirement: Coverage artifact produced via pytest-cov XML report

The repository SHALL configure `pytest-cov` to produce a Cobertura-compatible XML coverage report at `reports/coverage.xml`. The `coverage` job in the workflow SHALL upload this XML as a workflow artifact.

#### Scenario: pytest-cov writes XML report

- **WHEN** `uv run task coverage` runs locally (or the coverage step runs in CI)
- **THEN** `pytest-cov` writes `reports/coverage.xml`
- **AND** the file contains line + branch coverage data for `src/omaha/`

#### Scenario: Coverage job uploads XML artifact

- **WHEN** the `coverage` job in the workflow completes
- **THEN** `reports/coverage.xml` is uploaded via `actions/upload-artifact@v4` with name `coverage-report`
- **AND** the artifact is downloadable from the workflow run page

### Requirement: Coverage is informational, not a fail-under gate

The `coverage` job SHALL report coverage but MUST NOT fail the workflow if the coverage percentage drops. The `pytest-cov` invocation SHALL NOT include `--cov-fail-under`.

#### Scenario: Coverage drops but workflow succeeds

- **WHEN** line coverage decreases compared to the previous run
- **THEN** the coverage report is uploaded as an artifact
- **AND** the workflow exits with success

#### Scenario: pytest-cov runs without --cov-fail-under

- **WHEN** the coverage step executes
- **THEN** the pytest command does NOT pass `--cov-fail-under=N`
- **AND** the exit code of the pytest step depends only on test pass/fail (which is already covered by the `test-unit` and `test-integration` jobs)

### Requirement: uv cache reused across CI runs

The workflow SHALL configure `actions/setup-python@v5` with `cache: "uv"` so the `~/.cache/uv` directory is restored between runs. The cache key MUST be derived from the hash of `uv.lock`.

#### Scenario: First CI run installs dependencies

- **WHEN** the workflow runs for the first time on a fresh runner
- **THEN** `actions/setup-python@v5` with `cache: "uv"` populates `~/.cache/uv` from the `uv.lock` key
- **AND** `uv sync --frozen` installs dependencies from cache

#### Scenario: Subsequent CI runs reuse the cache

- **WHEN** the workflow runs again with the same `uv.lock`
- **THEN** the `uv` cache is restored from the previous run
- **AND** `uv sync --frozen` completes without re-downloading packages

### Requirement: pyproject.toml defines coverage configuration

The `pyproject.toml` file SHALL include a `[tool.coverage.*]` block configuring `pytest-cov`. The configuration MUST scope coverage to `src/omaha/` and SHALL NOT include `fail_under`.

#### Scenario: pyproject.toml has tool.coverage.run with source

- **WHEN** a reader inspects `pyproject.toml`
- **THEN** `[tool.coverage.run]` is present
- **AND** it specifies `source = ["src/omaha"]`

#### Scenario: pyproject.toml omits coverage fail_under

- **WHEN** a reader inspects `pyproject.toml`
- **THEN** no `fail_under` key is present under any `[tool.coverage.*]` section
- **AND** no `--cov-fail-under` is present in the `addopts` of `[tool.pytest.ini_options]`

### Requirement: pytest addopts include XML coverage report path

The `[tool.pytest.ini_options]` block in `pyproject.toml` SHALL include `addopts` entries that configure the XML report path so that `pytest --cov` produces `reports/coverage.xml` even when invoked without `task coverage`.

#### Scenario: Direct pytest --cov invocation writes XML

- **WHEN** a developer runs `uv run pytest --cov=src/omaha` directly (without `task coverage`)
- **THEN** `pytest-cov` produces `reports/coverage.xml`
- **AND** the term-missing report is also printed to stdout (via the explicit `--cov-report=term-missing` from `task coverage`)

#### Scenario: task coverage command still produces term-missing output

- **WHEN** a developer runs `uv run task coverage`
- **THEN** the term-missing report is printed to stdout
- **AND** the XML report is written to `reports/coverage.xml`

### Requirement: Reports directory is not committed

The `reports/` directory SHALL be excluded from version control via `.gitignore`. The CI workflow SHALL create the directory if it does not exist before invoking `pytest --cov`.

#### Scenario: .gitignore excludes reports/

- **WHEN** a reader inspects `.gitignore`
- **THEN** an entry matching `reports/` or `reports/*.xml` is present

#### Scenario: CI creates reports directory before pytest runs

- **WHEN** the `coverage` job in the workflow executes
- **THEN** a step creates `reports/` (e.g., `mkdir -p reports`) before the pytest step
- **AND** `pytest-cov` writes `reports/coverage.xml` without `FileNotFoundError`

### Requirement: E2E tests are out of scope for this workflow

The CI workflow SHALL NOT include an e2e job. E2E tests under `tests/e2e/` SHALL continue to run only via `task test-e2e` locally (Playwright dependency, no parallel uvicorn in CI runner).

#### Scenario: ci.yml has no e2e job

- **WHEN** a reader inspects `.github/workflows/ci.yml`
- **THEN** no job references `task test-e2e` or `tests/e2e/`

#### Scenario: E2E tests run locally only

- **WHEN** a developer runs `uv run task test-e2e`
- **THEN** Playwright launches a browser
- **AND** tests run against a locally-spawned dev server
- **AND** no CI job exercises the e2e suite