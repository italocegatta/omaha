## Why

The rebalance page already exposes minimum deviation thresholds, but they only
color the UI. The optimizer still recommends buys and sells for rows that the
operator considers too small to act on, creating noise and forcing manual
filtering before placing orders.

## What Changes

1. Extend rebalance request handling so threshold inputs become server-visible
   parameters instead of Alpine-only visual state.
2. Apply a trade gate after the optimizer solves: a buy or sell stays enabled
   only when the asset exceeds both minimum absolute deviation (R$) and minimum
   percentual deviation (%).
3. Zero suppressed buy/sell amounts in the final plan, recalculate projected
   rows/aggregates from the gated plan, and surface any residual cash created by
   suppression.
4. Keep page defaults aligned with current UI (`R$ 1000`, `1%`) when the caller
   omits thresholds.
5. Update rebalance page copy/tests so operators understand that thresholds now
   affect suggested execution, not only highlighting.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rebalance-engine`: native plan post-processing now suppresses trades that do
  not clear operator thresholds and recomputes the gated plan totals.
- `rebalance-route`: request contract now accepts threshold inputs and passes
  them unchanged to the rebalance pipeline.
- `rebalance-page`: threshold inputs participate in form submission and the
  rendered plan reflects the gated execution suggestions.

## Impact

- `src/omaha/rebalance/` — threshold gate, plan recomputation, and metrics
  alignment after suppression.
- `src/omaha/routes/rebalance.py` and `src/omaha/rebalance/schemas.py` — request
  contract for threshold inputs.
- `src/omaha/routes/pages.py`, `src/omaha/templates/rebalance.html`, and
  `src/omaha/templates/_rebalance_plan.html` — page submission + rendered
  defaults.
- `tests/test_rebalance_*.py` — coverage for request defaults, gating semantics,
  and rendered behavior.
- No DB migration, no new endpoint, no external dependency.
