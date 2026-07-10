## MODIFIED Requirements

### Requirement: Test markers split unit from integration
`pyproject.toml` MUST declare three pytest markers — `unit`, `integration`, and `bdd`. `tests/conftest.py::pytest_collection_modifyitems` MUST keep the path and allowlist mapping explicit, reviewable, and loud on drift.

The canonical path-to-bucket rule is:

- `tests/e2e/**/*.py` and `tests/visual/**/*.py` → no `unit`, `integration`, or `bdd` marker; these Playwright suites are selected by path-based tasks.
- `tests/bdd/**/*.py` → `@pytest.mark.bdd` only.
- `tests/audit_integration/**/*.py` and any file matched by `_INTEGRATION_PREFIXES` → `@pytest.mark.integration`.
- Files explicitly named in `_UNIT_FILES` and the remaining `tests/*.py` files → `@pytest.mark.unit`.
- Any `tests/*.py` file that falls through to `unit` without belonging to an explicit carve-out MUST emit `UnknownTestPath` so allowlist drift is visible.

The canonical task buckets and their help text MUST mirror the same partition: `task test-unit` runs only `unit`, `task test-integration` runs only `integration`, `task test-bdd` runs only `tests/bdd/`, `task test-e2e` runs only `tests/e2e/`, `task test-visual` runs only `tests/visual/`, and `task test` runs the full suite.

#### Scenario: Marker configuration is present
- **WHEN** the change is applied
- **THEN** `[tool.pytest.ini_options]` in `pyproject.toml` contains marker entries for `unit`, `integration`, and `bdd`
- **AND** the task help text names the same bucket meanings

#### Scenario: Unknown path drift warns loudly
- **WHEN** a new `tests/test_*.py` file falls through to the default `unit` branch without joining `_UNIT_FILES` or `_INTEGRATION_PREFIXES`
- **THEN** collection emits `UnknownTestPath`
- **AND** the warning tells the operator to update the explicit allowlist

#### Scenario: BDD subset is isolated from unit and integration markers
- **WHEN** `uv run task test-bdd` is invoked
- **THEN** pytest collects `tests/bdd/` only
- **AND** the collected scenarios carry the `bdd` marker instead of `unit` or `integration`

#### Scenario: Playwright buckets stay path-scoped
- **WHEN** `uv run task test-e2e` or `uv run task test-visual` is invoked
- **THEN** the selected suite is determined by `tests/e2e/` or `tests/visual/` path
- **AND** those tests are not back-filled with `unit` or `integration` markers during collection

#### Scenario: Full test task preserves all buckets
- **WHEN** `uv run task test` is invoked
- **THEN** unit, integration, BDD, e2e, and visual families remain reachable through one full-suite entrypoint
- **AND** no family is silently omitted from the contract described by tasks and markers
