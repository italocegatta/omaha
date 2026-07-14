# T15 — Tasks

## 1. Fix `bdd-workflow-reuse` spec
- [x] Rename `login_and_pick_profile` → `login_and_land` in `openspec/specs/bdd-workflow-reuse/spec.md`
- [x] Remove `profile_isolation.feature` from carve-out examples (code only has `{"login.feature"}` since 2026-06-26)
- [x] Update "profile_isolation.feature has no login wrapper" scenario → `profile_sharing.feature`
- [x] Update workflow count date reference
- [x] Verify no other active specs reference `login_and_pick_profile` (archives are OK)

## 2. Fix marker allow-list overlap
- [x] Remove `tests/test_csv_import.py` from `_INTEGRATION_PREFIXES` in `tests/conftest.py`
- [x] Verify `tests/test_csv_import.py` remains in `_UNIT_FILES`
- [x] Run `task test-file tests/test_csv_import.py` — must pass
- [x] Run `task test-unit` — no regressions

## 3. Fix performance baseline
- [x] Reconcile row counts in `tests/PERFORMANCE.md` (Collected = Passed + Failed + Skipped + Deselected)
- [x] Add note explaining deselected tests in the summary table
- [x] Verify counts against actual `pytest` output if available

## 4. Update BDD README
- [x] BDD README already documents `profile_isolation.feature` → `profile_sharing.feature` rename (lines 98-101)
- [x] Verify workflow table names match actual `_workflows.py` exports

## 5. Add marker overlap rule to `test-suite-quality` spec
- [x] Add requirement: files in `_INTEGRATION_PREFIXES` MUST NOT also appear in `_UNIT_FILES`
- [x] Add scenario: dual-listed file is silently tagged `integration` even if tests are pure functions

## 6. Note PRD stale reference (follow-up)
- [x] PRD §4.7 references `profile_isolation.feature` — file was renamed to `profile_sharing.feature` by 2026-06-26 change
- [x] Flag for PRD update in next PRD-touching slice (not this slice — PRD edits need owner approval)

## 7. Final verification
- [x] Run `task test-unit` — no regressions
- [x] Run `task lint` — no new warnings
- [x] Verify `tests/PERFORMANCE.md` row counts reconcile
