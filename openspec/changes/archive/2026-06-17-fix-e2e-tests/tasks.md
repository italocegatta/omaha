## 1. Diagnosis

- [x] 1.1 Run each failing test with `pytest -v -k <test_name> --tb=long` and capture root cause
- [x] 1.2 Classify each failure: environment (browser/server), flaky, or regression

## 2. Fixes

- [x] 2.1 Fix S01 (inline edit) — address root cause
- [x] 2.2 Fix S02 (class CRUD) — address both failures
- [x] 2.3 Fix S03 (asset CRUD) — address failure
- [x] 2.4 Fix S04 (import modal + journey) — address 3 failures
- [x] 2.5 Fix S05 (visual gate) — address failure
- [x] 2.6 Fix S06 (full journey) — address failure

## 3. Verification

- [x] 3.1 Run `task test-e2e` — all passing
