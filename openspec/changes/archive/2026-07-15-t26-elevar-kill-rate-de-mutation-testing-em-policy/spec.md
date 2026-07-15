# Spec: Mutation test coverage for policy.py

## Purpose

Define the behavioral contracts that tests must verify to kill surviving
mutations in `src/omaha/rebalance/policy.py`.

## Scope

Test-only change. Zero production code changes. All contracts below are
verified by assertions in `tests/test_rebalance_policy.py`.

## Contracts

### C1: Progressive sales stage acceptance

The function `_evaluate_progressive_sales_stage_solution` SHALL:

- Return `is_acceptable = True` when EITHER `category_improvement >=
  STAGED_SALES_MIN_CATEGORY_IMPROVEMENT` OR `top_asset_improvement >=
  STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT`, AND `zero_target_not_worse`
  is True.
- Return `is_acceptable = False` when NEITHER improvement meets its
  threshold, regardless of zero_target status.
- Return `is_acceptable = False` when improvements are sufficient but
  `zero_target_residual_value > previous + ZERO_TARGET_VALUE_TOLERANCE`.
- Set `stage_reason` to "nao entregou melhora material" when not
  materially better.
- Set `stage_reason` to "saldo relevante em ativos com alvo zero" when
  materially better but zero_target worsened.
- Set `stage_reason` to empty string when acceptable.
- Use `.get()` with defaults when `previous_metrics` keys are missing.

### C2: Contribution-only rejection reason

The function `_build_contribution_only_rejection_reason` SHALL:

- Include a specific PT-BR message for EACH of the 5 tolerances that is
  violated (value > tolerance + ALLOCATION_TOLERANCE).
- NOT include a message for tolerances that are within bounds
  (value <= tolerance + ALLOCATION_TOLERANCE).
- Return the default message "o plano somente com aporte nao atingiu
  os criterios configurados" when NO tolerances are violated.
- Concatenate multiple violations with "; ".

### C3: Top gaps calculation

The function `_calculate_solution_top_gaps` SHALL:

- Return the sum of the N largest relative shortfalls at asset level.
- Return the sum of the N largest relative shortfalls at category level.
- Compute relative shortfall as `max(target - projected, 0) / max(target, SHORTFALL_RELATIVE_FLOOR_VALUE)`.
- Return 0.0 when all projected values meet or exceed targets.
- Handle empty simulation frames (return 0.0).

### C4: Overweight projected value floor

The function `_build_overweight_projected_value_floor` SHALL:

- Set floor to `target_value - DISPLAY_TOLERANCE` for assets where
  `target_weight > ALLOCATION_TOLERANCE` AND `current_weight > target_weight
  + ALLOCATION_TOLERANCE` AND `current_value > DISPLAY_TOLERANCE`.
- Set floor to 0.0 for all other assets.
- Clamp negative floors to 0.0 via `np.maximum`.
- Compute `total_final_value = sum(current_values) + contribution`.

### C5: Overweight sell mask

The function `_build_overweight_sell_mask` SHALL:

- Include assets where `sell_enabled AND (target_weight <= ALLOCATION_TOLERANCE
  OR current_weight > target_weight + ALLOCATION_TOLERANCE)`.
- Exclude assets where `sell_enabled` is False.
- Exclude assets where `target_weight > ALLOCATION_TOLERANCE` AND
  `current_weight <= target_weight + ALLOCATION_TOLERANCE`.

### C6: Zero target sell mask

The function `_build_zero_target_sell_mask` SHALL:

- Include assets where `sell_enabled AND target_weight <= ALLOCATION_TOLERANCE
  AND current_value > DISPLAY_TOLERANCE`.
- Exclude assets where `current_value <= DISPLAY_TOLERANCE`.

### C7: Relative improvement

The function `_relative_improvement` SHALL:

- Return `(previous - current) / max(previous, ALLOCATION_TOLERANCE)`
  when `previous > current`.
- Return 0.0 when `current >= previous`.
- Use `ALLOCATION_TOLERANCE` as baseline when `previous < ALLOCATION_TOLERANCE`.

### C8: Sum largest values

The function `_sum_largest_values` SHALL:

- Return 0.0 when `values` is empty or `count <= 0`.
- Return the sum of all values when `count >= len(values)`.
- Sort descending and sum the first `count` values.

### C9: Stage rejection reason

The function `_build_stage_rejection_reason` SHALL:

- Delegate to `_build_contribution_only_rejection_reason` when
  `stage_name == CONTRIBUTION_ONLY_POLICY`.
- Return `stage_reason` from acceptance when non-empty.
- Return default "nao atingiu os criterios" when stage_reason is empty
  and stage is not contribution-only.

### C10: Solution metrics collection

The function `_collect_solution_metrics` SHALL:

- Return exactly 8 keys: `asset_deviation`, `category_deviation`,
  `top_asset_gap`, `top_category_gap`, `residual_cash_ratio`,
  `total_sell_amount`, `zero_target_residual_value`,
  `zero_target_residual_share`.
- Compute `residual_cash_ratio` as `residual_cash / total_final_value`.
- Compute `zero_target_residual_share` as `zero_target_residual_value / total_final_value`.
- Return 0.0 for `zero_target_residual_value` when `zero_target_mask`
  has no True values.

## Verification

After implementation:
1. `task test-unit` — all tests pass
2. `mutmut run --paths-to-mutate src/omaha/rebalance/policy.py` — < 30 survived
3. `mutmut results` — verify specific survivors are eliminated
