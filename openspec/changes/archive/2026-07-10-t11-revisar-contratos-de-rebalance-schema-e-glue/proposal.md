## Why

Drift between engine deviation output and spec contract: `_translate_metrics` passes `current_asset_deviation` and `projected_asset_deviation` directly to `current_deviation_pct` / `projected_deviation_pct` without converting from fraction (0-1) to percentage (0-100). Spec says percentage. Tests pass because they either use stub fixture (already percentage) or assert against known incorrect values. Fix the engine side to match spec.

Secondary: `total_buy`/`total_sell` mapping from `total_buy_amount`/`total_sell_amount` works but creates asymmetry between postprocessing dict keys and native/wire field names. Review and align.

## What Changes

1. **Engine `_translate_metrics`**: multiply `current_asset_deviation` and `projected_asset_deviation` by 100 before assigning to `current_deviation_pct` / `projected_deviation_pct` — brings output into spec-mandated percentage range (0-100).
2. **Key naming alignment**: rename postprocessing dict keys `total_buy_amount` → `total_buy` and `total_sell_amount` → `total_sell` so engine mapping is direct (no remapping needed).
3. **Test assertions**: update any test that asserts the current (fraction) deviation values to expect percentage values.
4. **No spec changes**: spec is correct (percentage 0-100). Fix code to match spec.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. Spec is already correct (percentage 0-100). Fix is in code only.

## Impact

- `src/omaha/rebalance/postprocessing.py`: rename dict keys `total_buy_amount` → `total_buy`, `total_sell_amount` → `total_sell`.
- `src/omaha/rebalance/engine.py`: add `* 100` scaling in `_translate_metrics`.
- `tests/test_rebalance_*.py`: update assertion values where they hardcode current (fraction) deviation values.
- No changes to `schemas.py`, `glue.py`, `solver_stub.py`, templates, routes, or DB.
