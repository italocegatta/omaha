## Context

`test_dashboard_shows_position_counts` (line 325, `tests/test_imports_routes.py`) fails 100% under `pytest-xdist` parallel. The test writes to the shared SQLite via ORM then runs CSV import + confirm. Other workers corrupt state. Passes in isolation.

Established pattern in codebase: `pytestmark = pytest.mark.xdist_group("serial")` — used in `test_seed_from_csv.py`, `test_snapshot_to_csv.py`, `test_real_csv_flow.py`, `test_db_reset_both_profiles.py`.

## Goals / Non-Goals

**Goals:**
- Make `test_imports_routes.py` reliable under xdist parallel execution.
- Unblock pre-push hook (`task test-integration-parallel`).

**Non-Goals:**
- Fixing per-worker DB isolation for import tests (larger effort, out of scope).
- Refactoring the test to avoid shared DB writes.

## Decisions

**D1: Module-level `xdist_group("serial")` vs per-test marker.**
Use module-level `pytestmark` (matches existing pattern). Per-test marker would leave other tests in the module still flaky. Module-level is consistent and safe — the module is ~12 lightweight tests, serial cost negligible.

**D2: No design/specs needed (skipped for this trivial fix).**
This is a 1-line test-infrastructure change. No product behavior changes. Minimal design/spec artifacts created only to satisfy the OpenSpec pipeline.

## Risks / Trade-offs

- **Risk**: Serial execution adds ~2-3s to parallel suite wall-clock. **Mitigation**: Module is small; impact negligible vs reliability gain.
