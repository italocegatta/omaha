## Why

Today `/rebalanceamento` forgets the operator's aporte whenever the page is reloaded or the user navigates through `/patrimonio`, and the page falls back to a placeholder instead of showing the current plan. The owner wants rebalance to behave like a live operational view: always ready for the active profile, defaulting to zero when no aporte was entered yet, and reflecting portfolio mutations without forcing the operator to retype state.

## What Changes

- Persist the current aporte as ephemeral per-profile UI state for the logged-in session only; app restart or logout resets it to `0`.
- Make `GET /rebalanceamento` materialize and render a plan automatically whenever the active profile has classes, using the persisted aporte or `0` by default.
- Make `POST /rebalanceamento` normalize an empty aporte to `0`, persist the submitted finite value for the active profile, and re-render the plan from current DB state.
- Ensure navigation away from `/rebalanceamento` and later return to the page preserves the last aporte for that profile while recomputing the plan from fresh class/asset/position data.
- Align the JSON rebalance contract with the same zero-default behavior so HTML and API flows do not drift on omitted aporte input.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `rebalance-page`: replace the placeholder-first contract with an always-materialized plan contract driven by persisted per-profile aporte state.
- `rebalance-route`: allow omitted contribution to resolve as `0` so the rebalance wire contract matches the page's zero-default behavior.

## Impact

- `src/omaha/routes/pages.py` - session-backed aporte helpers, automatic plan materialization on GET, and POST normalization/persistence.
- `src/omaha/routes/rebalance.py` plus rebalance request/schema glue - omitted `contribution` defaults to zero without changing finite-number validation for explicit values.
- `src/omaha/templates/rebalance.html` - input value/state must reflect persisted aporte and render plan by default instead of placeholder for populated profiles.
- `src/omaha/rebalance/` - shared parsing/schema surface may need a small adjustment so page and JSON route use one zero-default contribution contract.
- `openspec/specs/rebalance-page/spec.md`, `openspec/specs/rebalance-route/spec.md` - update behavioral contract.
- `tests/test_pages_routes.py`, rebalance route tests, and browser coverage around navigation/profile switching - update expectations from placeholder to always-ready plan.
