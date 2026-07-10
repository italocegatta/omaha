## 1. Fix postprocessing dict keys

- [x] 1.1 Rename `"total_buy_amount"` → `"total_buy"` and `"total_sell_amount"` → `"total_sell"` in `src/omaha/rebalance/postprocessing.py` `_build_plan_metrics` return dict.

## 2. Fix engine deviation scaling

- [x] 2.1 In `src/omaha/rebalance/engine.py` `_translate_metrics`, multiply `current_asset_deviation` and `projected_asset_deviation` by 100 before assigning to `current_deviation_pct` / `projected_deviation_pct`.

## 3. Update tests

- [x] 3.1 Search all `tests/test_rebalance_*.py` for hardcoded `current_deviation_pct` / `projected_deviation_pct` assertion values that assume fraction format. Update to percentage (multiply by 100).
- [x] 3.2 Verify `test_rebalance_engine_glue.py::test_cvxpy_solver_directly_returns_native_shape` passes with new scaled values.
- [x] 3.3 Run `uv run task test-file tests/test_rebalance_schemas.py tests/test_rebalance_glue.py tests/test_rebalance_route.py tests/test_rebalance_page.py tests/test_rebalance_postprocessing.py` — all pass.

## 4. Verify spec health

- [x] 4.1 Run `openspec list --specs` (or `opsx` alias) to verify spec health gate passes.
- [x] 4.2 Confirm `rebalance-engine` and `rebalance-route` spec both declare percentage 0-100 — no further spec edits needed.
