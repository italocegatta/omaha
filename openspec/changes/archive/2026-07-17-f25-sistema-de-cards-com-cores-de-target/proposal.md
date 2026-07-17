## Why

Rebalance summary cards read like separate widgets instead of one card family. The page needs a shared visual language so target state is obvious at a glance: above target reads positive, below target reads negative.

## What Changes

- Rework rebalance class-summary cards into one shared card system with consistent shell, spacing, and typography.
- Remove label `CLASSE` from card header so emphasis stays on class name and target signal.
- Apply target-state color accents to cards: positive/above target in green, negative/below target in red.
- Keep current rebalance flow, data contract, and table behavior unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `rebalance-page`: update rebalance class-summary card contract to define shared card family styling, header hierarchy, and target-state color cues.

## Impact

- Affected templates: `src/omaha/templates/_rebalance_plan.html`
- Affected stylesheet: `src/omaha/static/app.css`
- No API, solver, or data-model changes expected.
