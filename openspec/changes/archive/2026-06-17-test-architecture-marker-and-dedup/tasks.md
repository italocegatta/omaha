# Tasks: Test architecture marker + dedup + false-positive patterns

## 1. Marker rule rewrite

- [x] 1.1 Capture pre-change baseline: run `task test-unit`, `task test-integration`, `task test-e2e` and record durations + counts
- [x] 1.2 Rewrite `tests/conftest.py::pytest_collection_modifyitems` with explicit integration path list (D1) — `tests/s0*_*`, `tests/test_t02_*_routes.py`, `tests/test_t03_auth.py`, `tests/test_t03_pages_routes.py`, `tests/test_t03_imports_routes.py`, `tests/test_t03_assets_e2e.py`, `tests/test_t03_classes_e2e.py`, `tests/test_t04_e2e.py`, `tests/test_t06_*`, `tests/test_t99_*`. Preserve the module-level `pytestmark` override + `tests/e2e/` no-marker carve-out
- [x] 1.3 Add a `pytest.warns(UnknownTestPath)` for any file in `tests/*.py` not matched by either set (D6, OQ3) so future drift is loud
- [x] 1.4 Run `task test-integration` and confirm the S02/S03/S04 + T0* families are collected; assert count matches expected
- [x] 1.5 Run `task test-unit` and confirm only parser/validator/audit tests are collected (no DB, no TestClient)

## 2. Update task help text

- [x] 2.1 Edit `pyproject.toml:99-101` to match the corrected marker rule (`task test-unit` help text → "pure-function tests, no DB no HTTP, no Playwright"; `task test-integration` help text → "tests requiring DB, TestClient, or audit pipeline (full S0* + T0* route families)"; `task test-e2e` help text → "Playwright tests under tests/e2e/")

## 3. Delete retire-stub duplicates

- [x] 3.1 Delete `tests/test_s02_t07_classes_retire.py` (D2; canonical lives in `test_t02_classes_routes.py::test_get_classes_redirects_to_dashboard`)
- [x] 3.2 Delete `tests/test_s03_t05_assets_retire.py` (D2; canonical lives in `tests/e2e/test_s03_asset_crud.py::test_assets_route_redirects_to_dashboard`)
- [x] 3.3 Delete `tests/test_s04_t09_import_retire.py` (D2; canonical lives in `test_t03_imports_routes.py::test_get_import_redirects_to_dashboard` + `::test_review_redirects_to_dashboard`)
- [x] 3.4 Run `task test-integration` and `task test-e2e` to confirm no coverage loss

## 4. Remove T0* ≡ S0* duplicate assertions

- [x] 4.1 Confirm `test_t02_classes_routes.py::test_get_classes_redirects_to_dashboard` is the canonical home for the `/classes → 302 → /` redirect (per design D2; not removed — task description was inverted)
- [x] 4.2 Remove `test_t03_classes_e2e.py::test_snapshot_replaces_pre_existing` (canonical: `test_t02_classes_routes.py::test_post_classes_snapshot_replaces_pre_existing`)
- [x] 4.3 Remove `test_t03_imports_routes.py::test_review_preselects_class_via_preview_api` (duplicate redirect assertion of `test_review_redirects_to_dashboard`; the pre-selection logic is tested at the API level in `test_s04_t01_import_preview.py`). Keep `test_review_redirects_to_dashboard` as the canonical home for `/import/review → 302 → /`
- [x] 4.4 Run `task test-integration` and confirm the snapshot semantics still covered; assert count delta = -3

## 5. Tighten S06 thresholds

- [x] 5.1 In `tests/e2e/test_s06_full_journey.py`, derive expected parsed-row count from `parse_positions(FIXTURE_PATH.read_text())` once at test setup (D3)
- [x] 5.2 Replace `mismatch_ratio < 0.15` with `len(mismatches) == 0`; remove the `len(mismatches) / max(len(unmatched), 1)` computation
- [x] 5.3 Replace `len(wrong_assignments) < 5` with `len(wrong_assignments) == 0`. Discovered contract: the Alpine store leaves `class_id=""` for None-suggested rows (user picks in the modal) — the original test's expectation of `default_id` was wrong. Updated to assert `== ""` for None-suggested rows
- [x] 5.4 Replace `row_count >= 10` with `row_count == expected_count` (48 unique tickers)
- [x] 5.5 Iterate every committed `Position` and assert `asset_class.name == _EXPECTED_CLASS[ticker]` for exact equality (zero mismatches)
- [x] 5.6 Run `tests/e2e/test_s06_full_journey.py` — caught the empty-class_id contract; test now passes with exact equality
- [x] 5.7 Expand `_EXPECTED_CLASS` map if any ticker is missing; document each addition in the PR description. N/A — all 48 tickers covered by parser + manual overrides

## 6. Strengthen S05 visual gate

- [x] 6.1 In `tests/e2e/test_s05_visual_gate.py`, add structural pre-assertions before the screenshot capture: `class-summary-row` count == 3, `dashboard-asset-row` count >= 1, `"R$" in page.locator("main").inner_text()` (D4)
- [x] 6.2 Remove the `screenshot_path.stat().st_size > 1024` assertion (replaced by the structural checks)
- [x] 6.3 Capture the screenshot AFTER the structural assertions pass; keep the save so the human artifact survives
- [x] 6.4 Run `tests/e2e/test_s05_visual_gate.py` and confirm green
- [x] 6.5 Visually inspect the captured screenshot at `/tmp/s05_e2e_screenshots/s05_dashboard_polish.png` (51.2K, dashboard renders 3 class sections + asset rows + BRL formatting)

## 7. Add positive parametrization to TestSuggestClassId

- [x] 7.1 In `tests/test_s04_t04_real_csv_flow.py::TestSuggestClassId`, add a fourth test class whose name normalizes to match a real CSV category (e.g. `"Internacional"`) (D5)
- [x] 7.2 Add one new parametrize entry to `test_suggest_class_id_real_categories` with a non-`None` expected id (e.g. `("Internacional", 4)`)
- [x] 7.3 Run the test and confirm the new entry passes; if it fails, investigate the matcher (the bug is the test, not the implementation)

## 8. Rewrite stale docstrings

- [x] 8.1 Rewrite `tests/test_s02_t01_classes_patch.py` module docstring to describe `test_patch_class_allows_any_target_pct` expecting 200 (not 422) when sum exceeds 100
- [x] 8.2 Rewrite `tests/test_s02_t02_classes_post.py` module docstring to describe `test_post_class_creates_even_with_non_100_sum` expecting 201 (not 422) when sum exceeds 100
- [x] 8.3 Rewrite `tests/test_s03_t01_assets_post.py` module docstring to enumerate the 5 actual tests by their current names and behaviors
- [x] 8.4 Run `task test-integration` to confirm docstring-only changes don't break anything

## 9. Verification + sign-off

- [x] 9.1 Re-run the full matrix: `task test-unit`, `task test-integration`, `task test-e2e`. Compare counts + durations to the baseline from 1.1
  - test-unit: 121 passed, 2 skipped, 212 deselected, 1.33s (was 277 passed, 2 skipped, 63 deselected, 44.15s) — **33× speedup**
  - test-integration: 191 passed, 144 deselected, 69.48s (was 42 passed, 300 deselected, 20.07s) — **149 more tests, +3.5× runtime**
  - test-e2e: 22 passed, 60.20s (was 22 passed, 59.91s) — unchanged
- [x] 9.2 Verify the marker rule with `pytest --collect-only -q | head -30` to confirm the test-class marker tags are correct
- [ ] 9.3 Open the PR with: change description, baseline-vs-after metrics, list of deleted files + deleted assertions, screenshot diff for S05 visual gate
- [x] 9.4 Update AGENTS.md — added "Test marker rule — explicit allow-list, not pattern matching" section
- [ ] 9.5 Archive the change via `openspec archive test-architecture-marker-and-dedup` after merge
