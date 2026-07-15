## ADDED Requirements

### Requirement: test_imports_runs_serial_under_xdist
`tests/test_imports_routes.py` SHALL execute as a single serial group under `pytest-xdist` to prevent shared-DB state corruption between parallel workers.

#### Scenario: all tests in module pass under xdist parallel
- **WHEN** `pytest-xdist` distributes `tests/test_imports_routes.py` across workers
- **THEN** all tests in the module execute in a single worker (serial group), not split across workers

#### Scenario: tests still pass in isolation
- **WHEN** `tests/test_imports_routes.py` is run without xdist (single process)
- **THEN** all tests pass as before (marker has no effect without xdist)
