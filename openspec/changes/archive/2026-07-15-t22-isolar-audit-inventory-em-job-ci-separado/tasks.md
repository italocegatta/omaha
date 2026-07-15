# T22 — Tasks

## 1. Move test file

- [x] 1.1 `git mv tests/test_audit_inventory.py tests/audit_integration/test_audit_inventory.py`
- [x] 1.2 Update the module docstring: replace references to `task test-integration` with `task test-audit-integration`, and note the file lives under `tests/audit_integration/`
- [x] 1.3 Fix relative paths: `Path(__file__).resolve().parents[1]` → `parents[2]` for `_TEMPLATES_DIR` and `_CSS_PATH` (extra directory depth after move)

## 2. Update documentation references

- [x] 2.1 Update `tests/PERFORMANCE.md` — change the two path references from `tests/test_audit_inventory.py` to `tests/audit_integration/test_audit_inventory.py`

## 3. Verify exclusion and inclusion

- [x] 3.1 Run `uv run task test-integration -- --collect-only 2>&1 | grep audit_inventory` — expect zero collected tests ✅ (0 matches)
- [x] 3.2 Run `uv run task test-audit-integration -- --collect-only 2>&1 | grep audit_inventory` — expect 27 collected tests (27 from test_audit_inventory.py, 40 total in suite)
- [x] 3.3 Run `uv run task test-audit-integration` — all 40 tests pass ✅

## 4. Verify push path

- [x] 4.1 Run `uv run task test-integration-parallel -- --collect-only 2>&1 | grep audit_inventory` — expect zero collected tests ✅ (0 matches)
- [x] 4.2 Confirm pre-push hook (`prek.toml` line 116) uses `test-integration-parallel` — no changes needed ✅

## Additional fix discovered during implementation

- `parents[1]` → `parents[2]` in `_TEMPLATES_DIR` and `_CSS_PATH` path constants. The file moved from `tests/` to `tests/audit_integration/`, adding one directory level. Without this fix, `FileNotFoundError` on `app.css` and empty template renders.
