## ADDED Requirements

### Requirement: Coverage instrumentation SHALL NOT run in browser-heavy lanes
The `test-e2e`, `test-bdd`, and `test-visual` taskipy commands SHALL run without coverage instrumentation (`--no-cov`). These lanes validate UI flow and visual regression, not code coverage. The XML coverage report (`reports/coverage.xml`) SHALL NOT be produced by these commands.

#### Scenario: e2e tests run without coverage
- **WHEN** user runs `uv run task test-e2e`
- **THEN** pytest runs without `--cov` instrumentation
- **AND** no `reports/coverage.xml` file is written

#### Scenario: BDD tests run without coverage
- **WHEN** user runs `uv run task test-bdd`
- **THEN** pytest runs without `--cov` instrumentation
- **AND** no `reports/coverage.xml` file is written

#### Scenario: Visual tests run without coverage
- **WHEN** user runs `uv run task test-visual`
- **THEN** pytest runs without `--cov` instrumentation
- **AND** no `reports/coverage.xml` file is written

### Requirement: Coverage reporting SHALL be explicit in fast-lane tasks
The `test-unit`, `test-integration`, and `coverage` taskipy commands SHALL include explicit `--cov` and `--cov-report` flags. Coverage is opt-in at the task level, not inherited from global pytest addopts.

#### Scenario: Unit tests produce coverage when run via task
- **WHEN** user runs `uv run task test-unit`
- **THEN** pytest runs with `--cov=src/omaha` and produces coverage output

#### Scenario: Integration tests produce coverage when run via task
- **WHEN** user runs `uv run task test-integration`
- **THEN** pytest runs with `--cov=src/omaha` and produces coverage output

#### Scenario: Coverage task produces term-missing and XML
- **WHEN** user runs `uv run task coverage`
- **THEN** pytest runs with `--cov-report=term-missing` and `--cov-report=xml:reports/coverage.xml`

### Requirement: Global pytest addopts SHALL NOT carry coverage flags
The `[tool.pytest.ini_options] addopts` in `pyproject.toml` SHALL NOT contain `--cov` or `--cov-report` flags. Coverage configuration belongs to individual taskipy task commands, not to the global pytest baseline.

#### Scenario: addopts has no coverage flags
- **WHEN** developer reads `[tool.pytest.ini_options] addopts` in `pyproject.toml`
- **THEN** the addopts string does not contain `--cov` or `--cov-report`
- **AND** addopts still contains `--ignore=tests/e2e/_disabled` and `-q`
