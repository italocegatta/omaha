## Why

Visual regression suite (`task test-visual`) currently 20/20 green, but recent high-velocity feature work (F14 Catppuccin theme, F15 table redesign, F18 rebalance UI, F19 threshold gate, F20 trade quantity, T08 conftest refactor) may have introduced fragile selectors, untested states, or gaps in the baseline matrix. Need systematic triage to decide, case-by-case, whether a failure would come from outdated baseline, fragile selector, or real UI regression — before next feature slice lands and masks a true positive.

## What Changes

- Audit all 10 test functions in `tests/visual/test_snapshots.py` for selector fragility, missing wait conditions, and false-positive/false-negative potential.
- Audit `tests/visual/conftest.py` for diff/update policy correctness, pixel-tolerance adequacy, and PNG decoder edge cases.
- Audit baseline PNG set (`tests/visual/baselines/`) for intentionality: each baseline captures the intended state (not stale or intermediate).
- Audit DESIGN.md §Visual Regression for accuracy: does the documented update policy match current conftest behavior?
- Fix minor side (test helper or template) where real UI regression is confirmed — but preserve the regression signal, never suppress it.
- No BDD/e2e scope, no parallelism/harness runtime, no CSV pipeline, no rebalance solver.

## Capabilities

### New Capabilities
*(none — no new capability introduced; this is a triage+fix slice over existing contract)*

### Modified Capabilities
- `visual-regression-baseline`: update spec to reflect current conftest behavior post-T08 refactor (session-scoped browser, explicit `_browser` fixture, `reduced_motion="reduce"`, `animations="disabled"` in screenshot); clarify pixel-diff tolerance rationale; document `UPDATE_VISUAL_BASELINES=1` env-var flow.

## Impact

- **`tests/visual/test_snapshots.py`**: selector audit, wait-gap fixes, structural-assertion hardening.
- **`tests/visual/conftest.py`**: diff-policy clarity, PNG decoder maintainability notes, helper docstrings.
- **`tests/visual/baselines/*.png`**: replacement of any baseline found to capture stale/intermediate state (scope: only intentional visual drift after confirmed regression).
- **`src/omaha/templates/` and/or `src/omaha/static/app.css`**: only if triage confirms a real UI regression — fix the runtime side, not the test.
- **`DESIGN.md`**: update §Visual Regression section if conftest behavior drifted from documented flow.
- **`openspec/specs/visual-regression-baseline/spec.md`**: align with current conftest behavior and triage findings.
