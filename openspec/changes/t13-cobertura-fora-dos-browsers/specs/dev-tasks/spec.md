## MODIFIED Requirements

### Requirement: Test coverage report
The system SHALL provide a taskipy shortcut for running tests with coverage reporting, with `pytest-cov` added to dev dependencies.

#### Scenario: Run with coverage
- **WHEN** user runs `uv run task coverage`
- **THEN** pytest runs unit + integration tests with `--cov=src/omaha --cov-report=term-missing --cov-report=xml:reports/coverage.xml` and shows missing lines per module

#### Scenario: Unit tests produce coverage via task
- **WHEN** user runs `uv run task test-unit`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in the taskipy command

#### Scenario: Integration tests produce coverage via task
- **WHEN** user runs `uv run task test-integration`
- **THEN** pytest runs with `--cov=src/omaha` flag explicitly in the taskipy command

#### Scenario: Browser tasks do not produce coverage
- **WHEN** user runs `uv run task test-e2e`, `uv run task test-bdd`, or `uv run task test-visual`
- **THEN** pytest runs with `--no-cov` flag and no `reports/coverage.xml` is written
