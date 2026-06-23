## Why

The dashboard is capped at 760px wide on a 1920px-class monitor, so
content crowds into the central third and the eight-column asset table
reads as stacked noise. Editing a target percentage on the other hand
demands two mouse clicks (open input, then click "salvar") for a
single-digit change — too bureaucratic for the most common edit on
the page.

## What Changes

- Bump dashboard `<main>` max-width from 760px to 1400px so content
  covers ~73% of a 1920px screen with margin to breathe.
- Drop the `salvar` / `cancelar` buttons from the three inline
  target-pct editors (class header, asset %-of-class, asset %-of-total).
- Add `@blur` handlers on each input that call the existing commit
  function — typing then leaving the cell saves.
- Enter keeps saving (already wired via `@keyup.enter`); Escape keeps
  cancelling (already wired via `@keyup.escape.window`). No
  behavioural regression there.
- Remove the now-dead CSS rules for the deleted buttons.
- Update the e2e + integration tests that reference the removed
  `*-commit` / `*-cancel` selectors to press Enter instead.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dashboard-inline-editing`: the "Inline editing de target % da
  classe" and asset-side equivalents change their commit trigger from
  a `salvar` button click to **Enter OR blur on the input**, and
  the editor UI no longer renders the button row.

## Impact

- `src/omaha/static/app.css` — 1-line width change + ~50 lines of
  dead button CSS removed.
- `src/omaha/templates/dashboard.html` — 3 button rows removed
  (class header, asset %-class, asset %-total); 3 `@blur="commit*()"`
  handlers added.
- `tests/e2e/test_s01_inline_edit.py` — drop unused
  `*_commit` / `*_cancel` selectors from the locator dict.
- `tests/e2e/test_s10_asset_table.py` — swap one `.click()` on the
  commit button to `.press("Enter")`; drop unused selectors.
- `tests/test_t03_pages_routes.py` — drop three string asserts that
  check for the removed `data-testid="*-commit"` attributes in the
  raw HTML response.
- `openspec/specs/dashboard-inline-editing/spec.md` — delta to
  REQUIREMENTS replacing the save-button trigger with Enter-or-blur
  and removing the button-rendering expectation.

No backend change. No new dependencies. No migration. Single visual
+ interaction change scoped to one route.
