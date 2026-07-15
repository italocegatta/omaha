# T22 — Isolar audit_inventory em job CI separado

## Problem

`tests/test_audit_inventory.py` (30 tests, ~48s) runs as part of `task test-integration` and blocks every push via the pre-push hook (`test-integration-parallel`). These tests parse production `app.css` (~2500 lines) and render Jinja2 templates to validate the interactive-element inventory. They are real audit tests — but their cost (~48s of CSS/template parsing) delays pushes for work that has nothing to do with functional correctness.

## Proposed change

Move `tests/test_audit_inventory.py` → `tests/audit_integration/test_audit_inventory.py`.

This leverages the existing infrastructure completely:
- `tests/audit_integration/` is already excluded from `task test-integration` and `task test-integration-parallel` (via `--ignore=tests/audit_integration`)
- `task test-audit-integration` already collects everything under `tests/audit_integration/`
- CI job `test-audit-integration` already exists as a dedicated job
- Pre-push hook uses `test-integration-parallel` — audit_inventory will no longer block push

No changes to `prek.toml`, `pyproject.toml`, or `.github/workflows/ci.yml` needed.

## Non-goals

- Not deleting or disabling the tests — they are valid audit tests
- Not changing timeout behavior or adding `--timeout` flags
- Not modifying the test content (only the file location and docstring)

## Scope

| Action | File |
|--------|------|
| Move | `tests/test_audit_inventory.py` → `tests/audit_integration/test_audit_inventory.py` |
| Update docstring | Moved file — reference new location and task |
| Update paths | `tests/PERFORMANCE.md` — two path references |

## Acceptance criteria

1. `task test-integration` no longer collects audit_inventory tests
2. `task test-audit-integration` collects and runs all 30 tests from the moved file
3. Pre-push hook does not block on audit_inventory
4. CI job `test-audit-integration` runs the moved file
5. Zero test content changes — only path and docstring
