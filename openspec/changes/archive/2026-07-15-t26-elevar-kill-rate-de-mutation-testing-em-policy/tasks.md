# Tasks: Elevar kill rate de mutation testing em policy.py

## T1: Kill mutations in `_evaluate_progressive_sales_stage_solution`

Target: 44 survived → < 8

- [ ] 1.1 Test: category improvement above threshold, top asset below → acceptable
- [ ] 1.2 Test: top asset improvement above threshold, category below → acceptable
- [ ] 1.3 Test: both improvements below threshold → not acceptable, reason "nao entregou melhora"
- [ ] 1.4 Test: both improvements above threshold → acceptable, stage_reason empty
- [ ] 1.5 Test: improvement present but zero_target worsened beyond tolerance → not acceptable, reason "saldo relevante"
- [ ] 1.6 Test: boundary — improvement exactly at `STAGED_SALES_MIN_CATEGORY_IMPROVEMENT` (0.05)
- [ ] 1.7 Test: boundary — zero_target_residual exactly at `previous + ZERO_TARGET_VALUE_TOLERANCE`
- [ ] 1.8 Test: previous_metrics with missing keys (`.get()` defaults)
- [ ] 1.9 Verify: run `task test-unit` — all pass

## T2: Kill mutations in `_build_contribution_only_rejection_reason`

Target: 16 survived → < 3

- [ ] 2.1 Test: only asset_deviation violated → reason contains only that tolerance
- [ ] 2.2 Test: only category_deviation violated → reason contains only that tolerance
- [ ] 2.3 Test: only top_asset_gap violated → reason contains only that tolerance
- [ ] 2.4 Test: only top_category_gap violated → reason contains only that tolerance
- [ ] 2.5 Test: only residual_cash_ratio violated → reason contains only that tolerance
- [ ] 2.6 Test: boundary — value exactly at `TOLERANCE + ALLOCATION_TOLERANCE` → NOT violated
- [ ] 2.7 Test: boundary — value at `TOLERANCE + ALLOCATION_TOLERANCE + 1e-10` → violated
- [ ] 2.8 Verify: run `task test-unit` — all pass

## T3: Kill mutations in `_calculate_solution_top_gaps`

Target: 14 survived → < 3

- [ ] 3.1 Test: 5 assets with known shortfalls → verify top-2 sum exact
- [ ] 3.2 Test: all assets above target → gap = 0.0
- [ ] 3.3 Test: single asset shortfall with count > assets → sum all
- [ ] 3.4 Test: zero target weight → shortfall computed against `SHORTFALL_RELATIVE_FLOOR_VALUE`
- [ ] 3.5 Test: empty simulation frame → gap = 0.0
- [ ] 3.6 Test: two categories with known shortfalls → verify top-1 category gap
- [ ] 3.7 Verify: run `task test-unit` — all pass

## T4: Kill mutations in `_build_overweight_projected_value_floor`

Target: 13 survived → < 3

- [ ] 4.1 Test: overweight asset → verify exact floor value
- [ ] 4.2 Test: balanced asset → floor = 0.0
- [ ] 4.3 Test: zero target weight → NOT in overweight mask → floor = 0.0
- [ ] 4.4 Test: contribution changes total_final_value → floor changes accordingly
- [ ] 4.5 Test: negative floor clamped to 0.0 via `np.maximum`
- [ ] 4.6 Test: current_value <= DISPLAY_TOLERANCE → excluded from mask
- [ ] 4.7 Verify: run `task test-unit` — all pass

## T5: Kill mutations in mask builders

- [ ] 5.1 Test: `_build_overweight_sell_mask` — exact boolean array for known frame
- [ ] 5.2 Test: boundary — `target_weight = ALLOCATION_TOLERANCE` → included
- [ ] 5.3 Test: boundary — `current_weight = target_weight + ALLOCATION_TOLERANCE` → NOT overweight
- [ ] 5.4 Test: `_build_zero_target_sell_mask` — exact boolean array
- [ ] 5.5 Test: boundary — `current_value = DISPLAY_TOLERANCE` → excluded (> not >=)
- [ ] 5.6 Verify: run `task test-unit` — all pass

## T6: Kill mutations in helpers

- [ ] 6.1 Test: `_sum_largest_values` — count > array size → sum all
- [ ] 6.2 Test: `_sum_largest_values` — count = 0 → 0.0
- [ ] 6.3 Test: `_relative_improvement` — previous = ALLOCATION_TOLERANCE → baseline clamped
- [ ] 6.4 Test: `_relative_improvement` — exact fraction for known values
- [ ] 6.5 Test: `_build_stage_rejection_reason` — contribution-only path
- [ ] 6.6 Test: `_build_stage_rejection_reason` — stage with non-empty stage_reason
- [ ] 6.7 Verify: run `task test-unit` — all pass

## T7: Integration — cascade-level mutation kills

- [ ] 7.1 Test: `_solve_hierarchical_policy` — contribution <= ALLOCATION_TOLERANCE → CURRENT_PORTFOLIO_REBALANCE_POLICY
- [ ] 7.2 Test: `_solve_hierarchical_policy` — contribution-only acceptable → correct policy assigned
- [ ] 7.3 Test: `_solve_contribution_only_rebalance` — sells disabled (all zeros mask)
- [ ] 7.4 Test: `_collect_solution_metrics` — verify all 8 keys with exact values
- [ ] 7.5 Test: `_calculate_solution_deviations` — known projected values → exact deviations
- [ ] 7.6 Verify: run `task test-unit` — all pass

## T8: Verify mutation score

- [ ] 8.1 Run `mutmut run --paths-to-mutate src/omaha/rebalance/policy.py`
- [ ] 8.2 Run `mutmut results` — verify < 30 survived
- [ ] 8.3 If >= 30: analyze survivors, add targeted tests, repeat
- [ ] 8.4 Update `.mutmut-baseline` if improved
