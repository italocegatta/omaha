## Context

The omaha e2e/BDD suite is in a "spec-rot" state: 12 of 45 tests are
red for reasons unrelated to current code behavior. All 12 trace to
three drift points introduced by F02 (`commit 8f268fd`):

1. The `<h1 class="profile-name" data-testid="profile-name">` chip
   was replaced by `<select data-testid="profile-switcher">` per spec
   `header-profile-switcher`. Four tests still wait on the removed
   `data-testid`.
2. The top-nav link `/patrimonio` was rewritten to point at
   `/patrimonio` (not `/`). One regex wait fails.
3. `.patrimonio-page` widened to 1800px (was 1600) and used
   `width: calc(100% - 2rem)`. Pixel-alignment tests use
   hard-coded baselines measured against the old container.

A separate click-handler bug from F02 — `<section
class="patrimonio-actions">` had no `x-data` ancestor — was fixed
in commit `1755dd0`. That fix restored 19 of the 31 originally-red
tests; this slice handles the remaining 12.

Stakeholders: owner-operator (Juca), who runs `task test-e2e` and
`task test-bdd` to gate slices. No external consumers depend on the
test surface.

## Goals / Non-Goals

**Goals:**
- Bring the e2e suite to 0 red (100% green) against the post-F02 UI.
- Lock the current `data-testid` / `aria-*` inventory into a single
  importable map (`tests/e2e/selectors.py`) so future UI changes
  surface as a single failing selector rather than hidden rot.
- Add a smoke test (`test_selector_inventory.py`) that walks the
  inventory against a live `/patrimonio` render and confirms every
  named element resolves.
- Capture the F02 regression pattern (Alpine `x-data` ancestor
  requirement) as a regression test on the new
  `patrimonio-actions` element so the bug cannot return silently.

**Non-Goals:**
- No new e2e coverage beyond what F02 specs require.
- No `src/omaha/` changes — production is already correct (the F02
  bug fix landed in `1755dd0`).
- No spec delta files. `header-profile-switcher` is already correct;
  the tests are wrong.
- No pixel-perfect redesign. The alignment tests get the new
  baselines measured today, not assertions that lock the old design.
- No change to the BDD feature wording (`+ Nova classe` etc.). BDD
  step drift is real but out of scope for this slice — covered by a
  follow-up.

## Decisions

**D1 — Centralize selectors into one map.** Each test file currently
declares its own `S0X_SELECTORS` dict inline. After this change, all
tests import `from tests.e2e.selectors import SELECTORS`. *Rationale:*
a future F-slice that touches the layout has one place to update.
*Alternative considered:* keep per-file dicts and only fix the four
broken testids. Rejected: leaves the rot pattern in place for the
next UI change.

**D2 — Replace `data-testid="profile-name"` with
`data-testid="profile-switcher"`.** The `<select>` is the current
canonical identifier for the active profile in the header. Spec
`header-profile-switcher` Requirement "The dashboard h1
profile-name element is removed" is correct. *Rationale:* align
tests with the spec. *Alternative:* rename the existing testid on
the `<select>` back to `profile-name`. Rejected: violates the
header-profile-switcher spec.

**D3 — Use `/patrimonio$` (not `/$`) for the top-nav assertion.**
The nav link's `href` is `/patrimonio` (F02 D1 decision: PT-BR
slugs). *Rationale:* the URL is correct, the regex is stale.
*Alternative:* drop the URL assertion entirely. Rejected: loses
regression coverage for the nav link.

**D4 — Re-measure alignment baselines today, no production tweak.**
The five alignment / column-width tests will be run once against
the current rendered page, the pixel numbers recorded, and the
assertion constants updated. *Rationale:* the widening was a
deliberate UX fix requested by the owner; tests should track the
fix, not pin the old layout. *Alternative:* revert `.patrimonio-page`
to 1600px to placate the tests. Rejected: regresses owner-requested
improvement.

**D5 — Add `x-data` ancestor regression test.** A new test asserts
that `[data-testid="patrimonio-actions"]` carries an `x-data`
attribute. *Rationale:* prevents the exact regression that
introduced 19 of the 31 red tests in this rotation. *Alternative:*
add a generic Alpine-binding smoke. Rejected: too broad; the
specific element is what regressed.

## Risks / Trade-offs

- **R1 — Selector centralization breaks import cycles.** Mitigated
  by keeping `tests/e2e/selectors.py` free of `pytest` imports;
  pure data module. If any test file currently does `from .foo
  import SELECTORS` and that file imports pytest fixtures, the
  import graph may need a `conftest.py` shim. Verify with
  `task test-e2e` after the first test file is migrated.
- **R2 — Pixel baselines drift with browser version.** Playwright
  Chromium revs every few weeks. Mitigation: the thresholds stay
  loose (±1px); only the *baseline* values change. If a future
  Chromium rev shifts the baseline by more than 1px, the test
  fails loudly and the baseline gets re-recorded — not silently
  widened.
- **R3 — Header-profile-switcher testid gets renamed later.**
  The central map is one update point, not zero. Acceptable: the
  smoke test (`test_selector_inventory.py`) catches missing
  testids the moment they go away.

## Migration Plan

Single PR, applied via `openspec-apply-change`. No production
deploy. Rollback = revert the PR; tests go red again but no data
loss.

## Open Questions

None. All decisions are owner-resolvable from the F02 design
record. If a future test reveals a new drift class (e.g., BDD
feature text), it becomes a follow-up slice, not a T01 scope
expansion.