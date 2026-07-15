# T22 — Design

## Decision: Move to `tests/audit_integration/` (no new infrastructure)

### Context

`test_audit_inventory.py` lives in `tests/` root with explicit `pytestmark = pytest.mark.integration`. It runs via `task test-integration` which blocks push. The tests are valid (real audit of CSS/template rendering) but expensive (~48s) and not relevant to push-time functional validation.

### Options considered

**A. Move to `tests/audit_integration/`** — reuse existing directory, task, CI job.
- Pro: zero infrastructure changes; existing `--ignore=tests/audit_integration` in `test-integration` already excludes it; `test-audit-integration` task and CI job already exist
- Pro: consistent with `test_app_css_shape.py`, `test_logging_middleware.py`, `test_report_pipeline.py` which already live there
- Con: none identified

**B. Add `--timeout=30` to pre-push hook for audit tests** — keep file in `tests/`, add timeout.
- Pro: tests still run on push (catch regressions early)
- Con: adds complexity to prek.toml; timeout-based failure is fragile; 30s may not be enough on CI
- Con: doesn't use existing `audit_integration` infrastructure

**C. Create new taskipy task + CI job** — `test-audit-inventory` separate from `test-audit-integration`.
- Pro: maximum isolation
- Con: duplicates infrastructure that already exists for `tests/audit_integration/`

### Decision: Option A

Move the file. The infrastructure is already built. `tests/audit_integration/` is the canonical home for heavy audit tests that don't block push.

### How the exclusion works

1. `task test-integration` runs `pytest -m integration --ignore=tests/audit_integration` — audit_inventory excluded
2. `task test-integration-parallel` runs `pytest -m integration --ignore=tests/audit_integration -n auto` — audit_inventory excluded
3. Pre-push hook runs `test-integration-parallel` — push not blocked
4. `task test-audit-integration` runs `pytest tests/audit_integration -v` — audit_inventory included
5. CI job `test-audit-integration` runs `task test-audit-integration` — runs in dedicated job

### Why explicit `pytestmark` still works

The file has `pytestmark = pytest.mark.integration`. The conftest's `pytest_collection_modifyitems` skips files with explicit markers (line 271: `if "unit" in existing or "integration" in existing: continue`). So the marker is preserved regardless of directory location. The `tests/audit_integration/` path-based rule (line 279) would also tag it `integration` — redundant but harmless.

### Fixture scoping impact

The file uses session-scoped `jinja_env` and `stylesheet` fixtures. Moving directories does not affect fixture resolution — pytest discovers fixtures from the test file's own module and conftest hierarchy. The `tests/audit_integration/` directory has its own `__init__.py` and shares the root `tests/conftest.py`. No fixture breakage.
