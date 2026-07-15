## 1. Remove redundant skipped tests

- [x] 1.1 Delete `test_run_rebalance_negative_contribution_rejected` from `tests/test_rebalance_engine_glue.py` (lines 152-169) — behavior covered by `test_rebalance_validation.py::test_check_1_negative_contribution_rejected` + `test_rebalance_route.py::test_solver_validation_error_returns_400`
- [x] 1.2 Delete `test_default_solver_is_cvxpy` from `tests/test_rebalance_glue.py` (lines 270-279) — behavior covered by `test_rebalance_engine_glue.py::test_cvxpy_solver_directly_returns_native_shape`

## 2. Merge duplicate audit_inventory tests

- [x] 2.1 In `tests/test_audit_inventory.py`, merge `test_inventory_for_patrimonio_produces_rows` (line 284) and `test_inventory_rows_carry_template_field` (line 301) into single test `test_inventory_for_patrimonio_has_rows_with_template_field` that calls `inventory_for_page("patrimonio.html")` once and asserts both `len(rows) > 0` and `row.template == "patrimonio.html"` for all rows

## 3. Remove trivial find_interactive tests

- [x] 3.1 Delete `test_find_interactive_empty_html_returns_empty` from `tests/test_audit_inventory.py` (lines 212-214)
- [x] 3.2 Delete `test_find_interactive_no_interactive_elements_returns_empty` from `tests/test_audit_inventory.py` (lines 217-220)

## 4. Verify

- [x] 4.1 Run `task test-unit` — all tests pass, no regressions
- [x] 4.2 Run `task test-integration` — all tests pass, audit_inventory merged test works
- [x] 4.3 Confirm test count decreased by 4 (net: -5 removed + 1 merged)
