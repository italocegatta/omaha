# unit-test-effectiveness Delta

## MODIFIED Requirements

### Requirement: Test markers split unit from integration
`pyproject.toml` MUST declare two pytest markers — `unit` and
`integration`. Unit tests in `tests/` carry `@pytest.mark.unit`;
integration tests carry `@pytest.mark.integration`. The mapping from
test file to marker MUST be deterministic and path-based via
`pytest_collection_modifyitems` in `tests/conftest.py`. The
canonical path→marker rule is:

- `tests/e2e/**/*.py` → no marker (Playwright tests are invoked by
  `task test-e2e`, not by `-m` selectors; the no-marker carve-out
  matches the existing `conftest.py` skip logic).
- `tests/audit_integration/**/*.py` → `@pytest.mark.integration`.
- `tests/s0*_*.py` → `@pytest.mark.integration` (the S02/S03/S04
  route, asset, and import families; they all hit DB + TestClient).
- `tests/test_t0*_routes.py`, `tests/test_t0*_e2e.py`,
  `tests/test_t0*_auth.py`, `tests/test_t04_e2e.py`,
  `tests/test_t06_*.py`, `tests/test_t99_*.py` →
  `@pytest.mark.integration`.
- Every other file in `tests/*.py` → `@pytest.mark.unit`.

`task test-unit` MUST run only the `unit` subset (no DB, no
TestClient, no alembic subprocess, no Playwright). `task
test-integration` MUST run every TestClient-based route test,
including the S02/S03/S04 families. `task test-e2e` MUST run only
the Playwright suite under `tests/e2e/`. `task test` MUST run
everything. A module-level `pytestmark` declaration wins over the
path rule (already supported by the existing
`pytest_collection_modifyitems`).

#### Scenario: Marker configuration is present
- **WHEN** the change is applied
- **THEN** `[tool.pytest.ini_options]` in `pyproject.toml`
  contains `markers = ["unit: pure-function tests, no DB no HTTP", "integration: tests requiring DB, TestClient, or external services"]`

#### Scenario: Unit subset is runnable alone
- **WHEN** `uv run pytest -m unit` is invoked
- **THEN** every test in the unit subset runs without booting
  `omaha.main.app` and without migrating a SQLite database

#### Scenario: Integration subset exercises the full S0* route family
- **WHEN** `uv run pytest -m integration` is invoked
- **THEN** every test in `tests/s02_*`, `tests/s03_*`, `tests/s04_*`,
  `tests/test_t02_*_routes.py`, `tests/test_t03_*`,
  `tests/test_t04_e2e.py`, `tests/test_t06_*`, `tests/test_t99_*`
  is collected and runs with the shared `_omaha_test_env`
  fixture

#### Scenario: E2E subset excludes path-based unit marker
- **WHEN** `uv run pytest tests/e2e` is invoked
- **THEN** no test in `tests/e2e/` carries either `@pytest.mark.unit`
  or `@pytest.mark.integration` (Playwright tests are filtered
  separately by path)
