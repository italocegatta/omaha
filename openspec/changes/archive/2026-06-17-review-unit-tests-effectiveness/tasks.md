## 1. Production refactors (land first)

- [x] 1.1 Delete the dead `parse_stylesheet` definition at `src/omaha/audit/css_parser.py:111-120`. Verify the surviving definition at `:210-227` is unchanged. Run `uv run task test-unit` — no behavior change expected.
- [x] 1.2 Replace `_build_registry_from_stylesheet` in `src/omaha/audit/inventory.py:433-450` with `from omaha.audit.css_parser import _build_registry as _build_registry_from_stylesheet`. Verify the registry produced is identical for `parse_stylesheet(Path("src/omaha/static/app.css"))`.
- [x] 1.3 Tighten `composite_over` in `src/omaha/audit/color_resolver.py:100-120`. Validate backdrop before the `alpha >= 1.0` short-circuit so `composite_over("#ff0000", "bad-color")` raises `ValueError`. Confirm `audit/inventory.py:state_color_pairs` already swallows the exception (no caller-side change needed). Run `uv run task test-unit` — fix should land together with the new test in §4.

## 2. Test marker infrastructure

- [x] 2.1 Add `markers = ["unit: pure-function tests, no DB no HTTP", "integration: tests requiring DB, TestClient, or external services"]` to `[tool.pytest.ini_options]` in `pyproject.toml`.
- [x] 2.2 Update the `task` definitions in `pyproject.toml`: keep `test` (everything), keep `test-e2e`, keep `test-unit` but switch from `--ignore=tests/e2e` to `-m unit` (and add the existing route tests to the `unit` marker set explicitly, since they currently run as "integration" via the conftest). Add a `test-integration = uv run pytest -m integration` shortcut.
- [x] 2.3 Verify `uv run pytest -m unit --collect-only` shows only the unit subset (no route tests, no model tests, no e2e).

## 3. Audit test rewrites

- [x] 3.1 Rewrite `tests/test_audit_color_resolver.py`. Keep `contrast_ratio` (hex, oklch, invalid, color-mix with a structural assert — `pytest.approx(21.0)` not `> 20.0`). Collapse `aa_status_*` (6 tests) into one `@pytest.mark.parametrize("ratio,is_large,expected_status", [(4.5, False, "Passa"), (4.4, False, "Falha"), (3.0, True, "Passa"), (2.9, True, "Falha"), (4.4, False, "Falha"), (3.1, True, "Passa"), (4.5, False, "Passa")])`. Collapse `apply_brightness_*` into one parametrized test that decodes the hex and compares sRGB channels (no more `startswith("#")`). Collapse `composite_over_*` into one parametrized test that asserts the exact blended hex (e.g. `#ff8080` for 50% red over white) using `pytest.approx` on the channels. Delete `test_audit_color_resolver_importable` and `test_aa_status_returns_tuple`. Target: 10 tests.
- [x] 3.2 Rewrite `tests/test_audit_css_parser.py`. Delete the unused `_SMALL_FIXTURE_RULES` block at `:67-76`. Tighten `test_css_rule_construction` to use `pytest.raises(dataclasses.FrozenInstanceError)`. Replace the tautological `assert "--border" in by_name or "--border" not in by_name` at `:237` with `assert "--spacing-xs" not in by_name` only. Remove `if "--ink" in by_name:` guards — assert directly. Inline the `parse_stylesheet` well-formedness into one parametrized test that uses `tmp_path`. Target: 12 tests.
- [x] 3.3 Rewrite `tests/test_audit_inventory.py`. Collapse `TestAuditContextFactory.test_context_for_*` (7 tests) into one parametrized test that asserts the keys per template. Collapse `TestRenderPage.test_render_*` (8 tests) into one parametrized test that asserts a template-specific anchor per page (e.g. "Omaha" for base, dashboard class name for dashboard, etc.). Collapse `TestFindInteractive.test_finds_elements_in_*` (3 tests) into one test with a parametrized `(template, expected_tag)` table. Delete `test_row_has_all_fields` (dataclass shape) and `test_create_row`/`test_row_is_frozen` (covered by the new dataclass test in 3.2's pattern). Keep `test_hover_state_differs_from_default` and `test_element_without_colors_returns_none` and `test_nonexistent_template_returns_empty`. Target: 10 tests.
- [x] 3.4 Rewrite `tests/test_audit_report.py`. Move `TestGenerateReport` and `TestCLI.test_cli_writes_report` (3 integration tests) to `tests/audit_integration/test_report_pipeline.py`. Keep `_parse_args` tests (pure) in unit. Collapse `TestRenderReport` (12 substring tests) into one parametrized test with `(substring, label)` table. Delete `test_summary_counts_accurate` (`assert "2" in html` is a false positive) and `test_generate_report_larger_than_10kb` (non-behavioral). Target: 4 unit tests.
- [x] 3.5 Rewrite `tests/test_phase02_tokens.py`. Keep `test_class_swatches_against_bg`, `test_status_ink_on_fill`, `test_error_fg_on_error_bg`, `test_legacy_aliases_intact`, and `test_documented_pairs_pass` (the DESIGN.md contract sweep — keep this as the one app.css-bound test). Move `test_delete_confirm_no_white` and `test_corrected_tokens_are_oklch` to `tests/audit_integration/test_app_css_shape.py` (they exercise live CSS, not pure logic). Mark the survivor with `@pytest.mark.integration` if it stays in this file, or move it too. Target: 6 unit tests.
- [x] 3.6 Rewrite `tests/test_t06_logging.py`. Move the 3 `TestClient`-using tests (`test_access_log_middleware_emits_*`, `test_access_log_middleware_captures_303_*`) to `tests/audit_integration/test_logging_middleware.py`. Keep `test_json_formatter_emits_seven_documented_keys`, `test_json_formatter_includes_formatted_traceback_when_exc_info_set`, and `test_configure_logging_json_format_emits_parseable_line` in unit. Target: 3 unit tests.

## 4. New `composite_over` validation tests

- [x] 4.1 In `tests/test_audit_color_resolver.py` (the rewritten file from §3.1), add a parametrized scenario covering `composite_over("#ff0000", "bad-color")` raises `ValueError` and `composite_over("bad-color", "#ffffff")` raises `ValueError`. This is the regression test for the production fix in §1.3.

## 5. Cleanup

- [x] 5.1 Delete `tests/test_t01_smoke.py`. Confirmed it asserts only on `settings.DATABASE_URL` default — zero regression coverage.
- [x] 5.2 Confirm `tests/test_t01_asset_target.py` survives unchanged — the three tests are tight, contract-driven, and have no false positives.
- [x] 5.3 Confirm `tests/test_t02_csv_import.py` survives unchanged except for an `@pytest.mark.unit` annotation at module top. (Per design §OQ3, leaving the fixture file dependency is OK for now.)

## 6. Verification

- [x] 6.1 Run `uv run pytest -m unit -v` and confirm count is in the 60–80 range (down from 152), every test passes, and CI runtime drops.
- [x] 6.2 Run `uv run pytest -m integration -v` and confirm the route tests, model tests, and the moved audit-integration tests all pass.
- [x] 6.3 Run `uv run task test` (full suite) and confirm 0 regressions.
- [x] 6.4 Run `uv run task lint` (ruff + prek) — confirm no new lint violations from the file rewrites.
- [x] 6.5 Open the change with `openspec status --change review-unit-tests-effectiveness` and confirm all `applyRequires` artifacts are `done`. Run `openspec archive review-unit-tests-effectiveness` to finalize.

## 7. Optional follow-up (not in this change)

- [x] 7.1 Decide on OQ1 (conftest split for `audit_integration/`). Tracked separately; doesn't block archive.
- [x] 7.2 Decide on OQ2 (`apply_brightness` symmetric tightening). Tracked separately.
- [x] 7.3 Decide on OQ3 (fixture file dependency for `test_t02_csv_import.py`). Tracked separately.
