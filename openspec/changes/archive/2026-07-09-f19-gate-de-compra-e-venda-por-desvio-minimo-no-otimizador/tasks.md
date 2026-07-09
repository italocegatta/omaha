## 1. Request and page contract

- [x] 1.1 Extend `RebalanceRequest` and route parsing with `min_deviation_value`
  and `min_deviation_pct`, including defaults and finite/non-negative
  validation.
- [x] 1.2 Update `/rebalanceamento` form handling so threshold inputs submit as
  real fields and re-render with current values.

## 2. Threshold gate in rebalance pipeline

- [x] 2.1 Thread threshold parameters through glue / solver-facing helpers to
  native plan post-processing.
- [x] 2.2 Suppress rows failing absolute-or-percent threshold checks by zeroing
  buy/sell, resetting projected value, and preserving existing buy/sell locks.
- [x] 2.3 Recompute category totals, projected metrics, residual cash, and final
  action derivation from gated rows.

## 3. Rebalance page rendering

- [x] 3.1 Update `_rebalance_plan.html` and/or `rebalance.html` so threshold
  inputs are submitted fields and rendered plan copy reflects execution gating.
- [x] 3.2 Ensure asset rows and summary cards consume the gated server result
  without client-side recomputation drift.

## 4. Verification

- [x] 4.1 Add or update tests for request defaults/validation and exact AND
  gating semantics.
- [x] 4.2 Add or update tests for gated projected totals / residual cash and
  rendered hold-vs-buy-sell behavior.
- [x] 4.3 Run `uv run task lint`, targeted rebalance tests, and
  `openspec list --specs`.
