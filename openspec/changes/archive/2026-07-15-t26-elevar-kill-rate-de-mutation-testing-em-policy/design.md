# Design: Mutation kill strategy for policy.py

## Mutation Categories

Each surviving mutation falls into one of these categories. Tests must
target the specific mutation type.

### Category 1: Comparison operators (<=, <, >=, >, ==)

**Where:** `_evaluate_progressive_sales_stage_solution`, `_build_contribution_only_rejection_reason`, `_build_overweight_projected_value_floor`

**Mutation:** `<=` → `<`, `>=` → `>`, etc.

**Kill strategy:** Test with value EXACTLY at the threshold. If code is
`x <= TOLERANCE`, test with `x = TOLERANCE` (should pass) and
`x = TOLERANCE + epsilon` (should fail). Mutant `< TOLERANCE` would
pass the boundary value when it shouldn't.

### Category 2: Boolean operators (and/or)

**Where:** `_evaluate_progressive_sales_stage_solution` (`materially_better and zero_target_not_worse`), `_build_overweight_projected_value_floor` (mask conditions)

**Mutation:** `and` → `or`, `or` → `and`

**Kill strategy:** Test cases where one condition is True and the other
is False. If `and` mutated to `or`, the test would incorrectly accept.

### Category 3: Constant replacement

**Where:** All functions using `ALLOCATION_TOLERANCE`, `DISPLAY_TOLERANCE`, `STAGED_SALES_MIN_*`, `ZERO_TARGET_VALUE_TOLERANCE`

**Mutation:** Constant → 0, constant → different value

**Kill strategy:** Tests must verify exact numeric outcomes, not just
"result is positive" or "result is acceptable". Use `pytest.approx`
with tight tolerance.

### Category 4: Return value / assignment mutations

**Where:** `_build_overweight_projected_value_floor` (np.maximum, np.zeros), `_calculate_solution_top_gaps` (sort direction, sum)

**Mutation:** `np.maximum` → `np.minimum`, `[::-1]` removed, `.sum()` → 0

**Kill strategy:** Verify exact computed values. For floor function,
verify specific array elements match expected floor values.

### Category 5: Conditional branch elimination

**Where:** `_build_contribution_only_rejection_reason` (5 if-blocks), `_evaluate_progressive_sales_stage_solution` (stage_reason branching)

**Mutation:** Remove `if` condition, swap branch bodies

**Kill strategy:** Test each branch independently. For rejection reasons,
verify the EXACT string content for each violated tolerance.

### Category 6: Negation / boundary mask mutations

**Where:** `_build_overweight_sell_mask`, `_build_zero_target_sell_mask`

**Mutation:** `> ` → `<=`, `<=` → `>`, `& ` → `|`

**Kill strategy:** Construct frames where mask result differs under
mutation. Verify mask array exactly.

## Test Plan by Function

### `_evaluate_progressive_sales_stage_solution` (44 survived → target < 8)

Tests needed:
1. **Category improvement only** — stage improves category but not top
   asset → acceptable (verifies `or` logic)
2. **Top asset improvement only** — stage improves top asset but not
   category → acceptable
3. **Neither improvement** — both below threshold → not acceptable,
   reason contains "nao entregou melhora"
4. **Both improvements** — both above threshold → acceptable
5. **Zero target worsened** — improvement present but zero-target
   residual increased → not acceptable, reason contains "saldo relevante"
6. **Boundary: improvement exactly at threshold** — `STAGED_SALES_MIN_CATEGORY_IMPROVEMENT` = 0.05, test with exactly 0.05 improvement
7. **Boundary: zero target exactly at tolerance** — residual exactly
   `previous + ZERO_TARGET_VALUE_TOLERANCE`
8. **Previous metrics with missing keys** — `.get()` defaults

### `_build_contribution_only_rejection_reason` (16 survived → target < 3)

Tests needed:
1. **Each tolerance violated individually** — 5 tests, each violating
   exactly one tolerance. Verify the reason string contains ONLY the
   violated tolerance message.
2. **Boundary: value exactly at tolerance + ALLOCATION_TOLERANCE** —
   should NOT trigger (tests `<=` vs `<`)
3. **Boundary: value exactly at tolerance + ALLOCATION_TOLERANCE + epsilon** —
   should trigger

### `_calculate_solution_top_gaps` (14 survived → target < 3)

Tests needed:
1. **Known shortfall distribution** — 5 assets with known shortfalls,
   verify top-2 sum is exact
2. **All assets above target** — no shortfalls → gap = 0
3. **Single asset shortfall** — count > assets → sum all
4. **Zero target weight** — shortfall relative to floor value
5. **Empty frame edge case**

### `_build_overweight_projected_value_floor` (13 survived → target < 3)

Tests needed:
1. **Overweight asset gets floor** — verify exact floor value for
   overweight asset
2. **Non-overweight asset gets zero** — verify floor is 0 for balanced
   asset
3. **Zero target weight excluded** — asset with target=0 not in
   overweight_positive_target_mask
4. **Contribution effect on total_final_value** — verify floor changes
   with contribution
5. **Negative floor clamped to zero** — `np.maximum(floor, 0.0)`

### `_relative_improvement` (existing tests cover basic cases)

Additional:
1. **Boundary: previous = ALLOCATION_TOLERANCE** — baseline clamped
2. **Large improvement** — verify exact fraction

### `_build_overweight_sell_mask` / `_build_zero_target_sell_mask`

Tests needed:
1. **Exact mask verification** — construct frame, verify boolean array
2. **Boundary: target_weight = ALLOCATION_TOLERANCE** — included in mask
3. **Boundary: current_weight = target_weight + ALLOCATION_TOLERANCE** —
   NOT overweight

### `_sum_largest_values` (existing tests cover basic cases)

Additional:
1. **count > array size** — sum all
2. **count = 0** — return 0
3. **Negative values** — sort works correctly

## Design Decisions

### D1: Unit tests over integration tests
Pure functions with deterministic inputs. No need for solver/engine
integration for most mutations. Integration tests via `simulate_rebalance`
only for cascade-level mutations.

### D2: Direct function calls, not through cascade
Call `_evaluate_progressive_sales_stage_solution` directly with
constructed metrics dicts. Avoids solver noise. Cascade integration
tested separately.

### D3: Exact value assertions
Every test asserts exact values with `pytest.approx(abs=1e-10)`. No
`assert result >= 0` type assertions (mutants survive these).

### D4: No new fixtures
Use existing `build_simple_setup`, `build_weighted_setup`, etc. Build
simulation frames via `_build_simulation_frame` where needed.
