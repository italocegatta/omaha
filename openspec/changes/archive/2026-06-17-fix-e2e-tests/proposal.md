## Why

9 e2e tests (Playwright) fail: S01 (1), S02 (2), S03 (1), S04 (3), S05 (1), S06 (1). Blocking CI confidence and masking real regressions. Need diagnosis: environment issue (no browser/server), flakiness, or genuine regressions.

## What Changes

- Diagnose root cause of each failure
- Fix or stabilize all 9 failing tests
- Ensure green run with `task test-e2e`

## Capabilities

### New Capabilities

*(none — test maintenance, no new capability)*

### Modified Capabilities

- *(no spec-level behavior changes)*

## Impact

- `tests/e2e/test_s01_inline_edit.py`
- `tests/e2e/test_s02_class_crud.py`
- `tests/e2e/test_s03_asset_crud.py`
- `tests/e2e/test_s04_import_modal.py`
- `tests/e2e/test_s04_user_journey.py`
- `tests/e2e/test_s05_visual_gate.py`
- `tests/e2e/test_s06_full_journey.py`
