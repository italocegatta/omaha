# Proposal: Test architecture marker + dedup + false-positive patterns

## Why

A deep audit of `tests/**/*.py` (41 files, ~150 integration + e2e tests) found four structural problems that together produce a misleading "green" signal:

1. **Marker misclassification**: `tests/conftest.py:137-156` auto-tags every file in `tests/*.py` as `unit` by default. The only explicit `pytestmark = pytest.mark.integration` lives in `test_audit_inventory.py`. Net effect: ~25 files that hit a real DB + TestClient (the entire S02/S03/S04 route families, `test_t0*_routes.py`, `test_t99_*`, `test_t06_*`, `test_t04_e2e`, `test_t03_*`) are silently tagged `unit`. `task test-integration` runs only `test_audit_inventory.py`; `task check` (lint + test-unit) runs every DB+HTTP test under the "unit" label. The label is a lie.

2. **Duplicated test coverage**: the three "retire" stubs (`test_s02_t07_classes_retire.py`, `test_s03_t05_assets_retire.py`, `test_s04_t09_import_retire.py`) each test one redirect (`GET /x → 302 → /`) that is already covered by another file. `test_t02_classes_routes.py::test_get_classes_redirects_to_dashboard` and `test_s02_t07_classes_retire.py::test_get_classes_redirects_to_dashboard` are byte-for-byte the same assertion with different docstrings. `test_t03_classes_e2e.py::test_snapshot_replaces_pre_existing` duplicates `test_t02_classes_routes.py::test_post_classes_snapshot_replaces_pre_existing`. `test_s04_import_modal.py::test_import_modal_happy_path` overlaps ~80% of `test_s04_user_journey.py::test_import_journey_43_matched_5_unmatched_5_assigned_confirm_dashboard`.

3. **Docstring drift**: `test_s02_t01_classes_patch.py:8-23`, `test_s02_t02_classes_post.py:8-18`, and `test_s03_t01_assets_post.py:10-25` describe `test_*_invalid_sum_returns_422` tests that were renamed/repurposed when the contract changed ("allocation is informational, not blocking"). The tests now assert 200/201, but the module docstrings still describe a 422 expectation. A future agent reading the docstring sees the opposite of what the file tests.

4. **False-positive bait**: `test_s06_full_journey.py` accepts `mismatch_ratio < 0.15`, `wrong_assignments < 5`, `row_count >= 10` — three loose thresholds that let 15% of misclassified rows pass. `test_s05_visual_gate.py` captures a screenshot and only asserts `st_size > 1024` — an empty page with whitespace > 1KB passes. `test_s04_t04_real_csv_flow.py::TestSuggestClassId::test_suggest_class_id_real_categories` parametrizes 9 categories all expecting `None`; if the function were deleted the test would still pass. `test_t06_logging.py::test_json_formatter_emits_seven_documented_keys` asserts `set(keys) == _EXPECTED_KEYS` while its docstring says "novas chaves podem ser adicionadas" — the test contradicts its own intent.

This change does not introduce any user-facing feature. It tightens the test layer itself so the "all green" signal becomes trustworthy.

## What Changes

- **Marker rule correction**: rewrite `tests/conftest.py::pytest_collection_modifyitems` so the path→marker mapping is explicit. Files in `tests/s0*/`, `tests/test_t0*_routes.py`, `tests/test_t0*_e2e.py`, `tests/test_t0*_auth.py`, `tests/test_t04_*.py`, `tests/test_t06_*.py`, `tests/test_t99_*.py` are tagged `integration`. The marker is named `integration` (already declared in `pyproject.toml:59-62`). `tests/e2e/` keeps the "no marker" carve-out (Playwright tests run via `task test-e2e`, not `-m`). Everything else stays `unit`. `task test-integration` will then exercise the full S02/S03/S04 + T0* route families.
- **Docstrings on `task` commands**: tighten `task test-integration` / `task test-e2e` descriptions in `pyproject.toml:100-101` to match the corrected marker rule.
- **Delete redundant retire-stubs**: remove `test_s02_t07_classes_retire.py`, `test_s03_t05_assets_retire.py`, `test_s04_t09_import_retire.py`. Their assertions are duplicated by the main route tests (`test_t02_classes_routes.py`, `test_t03_imports_routes.py`) or the e2e redirect tests. **BREAKING**: 6 redundant test bodies disappear. Net test count goes down; coverage stays equal.
- **Delete redundant T0* ≡ S0* duplicates**: drop the duplicate assertion bodies from `test_t02_classes_routes.py`, `test_t03_classes_e2e.py`, `test_t03_imports_routes.py`. Keep one canonical location per assertion (prefer the S0* retire file when present, else the T0* route file). **BREAKING**: a handful of assertions disappear from T0* files; coverage identical.
- **Tighten S06 loose thresholds**: replace `mismatch_ratio < 0.15`, `wrong_assignments < 5`, `row_count >= 10` with exact-equality assertions backed by the parser output (count = 48, mismatches = 0, assignments correct for every ticker).
- **Replace visual-gate screenshot smoke with structural assertions**: `test_s05_visual_gate.py` keeps the screenshot capture but adds structural checks (3 class sections, asset rows with positions, BRL totals present) before the file-size assertion. The 1KB size check is removed — it was the weak link.
- **Add positive parametrization to `TestSuggestClassId`**: add at least one category-class pair that asserts a non-`None` match in `test_s04_t04_real_csv_flow.py`. Catches "delete the function" regression.
- **Update stale module docstrings**: rewrite the docstrings in `test_s02_t01_classes_patch.py`, `test_s02_t02_classes_post.py`, `test_s03_t01_assets_post.py` to describe what the file actually tests (allocation is informational, not blocking).
- **Pin `pyproject.toml:103` task descriptions**: update `task test-unit` and `task test-integration` help text to match the new path rule.

## Capabilities

### New Capabilities
- `test-suite-quality`: a new capability governing the rules that distinguish a trustworthy test suite from a permissive one. Covers (a) no-duplicate-coverage, (b) docstrings-must-match-tested-contract, (c) parametrized-tests-must-include-positive-case, (d) no-loose-percentage-thresholds, (e) copy-strings-not-used-as-assertions.

### Modified Capabilities
- `unit-test-effectiveness`: the existing requirement "Test markers split unit from integration" is updated to be precise about the path-based rule and what each marker means in practice. The existing `Scenario: Unit subset is runnable alone` is kept verbatim.

## Impact

- `tests/conftest.py` — rewrite `pytest_collection_modifyitems` with the explicit path list.
- `pyproject.toml:100-101` — task help text updated to match.
- `tests/test_s02_t07_classes_retire.py` — **deleted**.
- `tests/test_s03_t05_assets_retire.py` — **deleted**.
- `tests/test_s04_t09_import_retire.py` — **deleted**.
- `tests/test_t02_classes_routes.py` — `test_get_classes_redirects_to_dashboard` removed (kept in conftest behavior).
- `tests/test_t03_classes_e2e.py` — `test_snapshot_replaces_pre_existing` removed (kept in `test_t02_classes_routes.py`).
- `tests/test_t03_imports_routes.py` — `test_review_redirects_to_dashboard` removed (kept in `test_s04_t09_import_retire.py`'s canonical equivalent).
- `tests/test_s06_full_journey.py` — three thresholds tightened; per-ticker exact-equality assertions added.
- `tests/test_s05_visual_gate.py` — structural assertions added before the screenshot capture.
- `tests/test_s04_t04_real_csv_flow.py` — `TestSuggestClassId` gains positive parametrization.
- `tests/test_s02_t01_classes_patch.py`, `test_s02_t02_classes_post.py`, `test_s03_t01_assets_post.py` — module docstrings rewritten.
- No production code (`src/omaha/**`) touched.
- No user-facing behavior changes.
- CI gate (`task check`) runs the same set of assertions in fewer files; runs faster by ~30-60s (less duplicated work).
