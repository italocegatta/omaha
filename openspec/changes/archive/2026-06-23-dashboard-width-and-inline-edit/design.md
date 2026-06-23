## Context

The dashboard template (`src/omaha/templates/dashboard.html`,
1759 lines) is the most-edited screen in the app. Two pieces of
friction were raised in a UI review:

1. **Narrow viewport.** `main { max-width: 760px }` at
   `src/omaha/static/app.css:473` (a dashboard-specific override of
   the 640px global default at line 201) pins the content to roughly
   the central third of any monitor above ~1500px wide. The asset
   table has eight sortable columns and reads as cramped at 760px.
2. **Two-click commit.** Three inline editors (class header target,
   asset `%` of class, asset `%` of total) render a `salvar` /
   `cancelar` button row alongside the `<input>`. The input already
   listens for `@keyup.enter` (commits) and `@keyup.escape.window`
   (cancels), so the buttons are redundant ceremony for the most
   common edit on the page.

Stakeholders: the dashboard user (visual + interaction) and the
test suite (e2e selectors + HTML string asserts). No backend
behavior changes; this is a frontend-only patch.

## Goals / Non-Goals

**Goals:**

- Dashboard content reaches ~73% of a 1920px-class monitor without
  sacrificing margin on smaller windows.
- Target-pct edits commit on Enter **or** blur of the input, with
  Escape as the only cancel path.
- Editor cells render only the input (and the existing live-preview
  hint + error span); no button row.
- Dead CSS for the deleted buttons is removed.
- Existing tests that referenced the removed `data-testid="*-commit"`
  / `*-cancel` attributes are updated to press Enter instead.

**Non-Goals:**

- Restructuring the asset table columns or sort order.
- Adding a debounce or autosave on input `input` event (commit
  remains explicit, on Enter or blur).
- Mobile/narrow-screen redesign — `@media` rules below 480px
  already collapse the table; left untouched.
- Backend or API changes.
- Adding a new "cancel on blur" mode — blur commits.

## Decisions

### Width: `max-width: 1400px` on `main`

**Why 1400:** the asset table has 8 columns; at 1200px columns
still pinch below ~110px each, and at full-width (no `max-width`)
the page loses its centered rhythm on ultrawide monitors. 1400px
is the smallest value that gives every column at least ~140px on
a 1920px monitor (where the dashboard reaches ~73% width with the
2rem auto margin) while still centering on 1500px-class screens.

**Alternatives:**

- `1200px` (~62%) — safer but still cramped on a 1920px monitor.
- `100%` (full bleed) — kills centered rhythm; only worth it for
  power-user dashboards with 16+ columns.
- `min(1400px, 95vw)` — slightly more robust at very narrow
  viewports, but `@media (max-width: 480px)` already collapses the
  table so the floor is already handled. Adds complexity for no
  current payoff.

### Blur commits, not cancels

**Why commit:** the user explicitly framed the goal as "type and
go — no bureaucracy". Blur-as-cancel forces an extra Escape keypress
or click-outside-aware flow. Blur-as-commit matches the "direct
input" feel the user asked for. The `@keyup.escape.window` handler
remains as the safety valve.

**Risk:** a stray click on an adjacent cell could save an
incomplete value. Mitigation: the input is `<input type="number">`,
so a stray click on whitespace outside the cell still triggers
blur on a clean parse or no-op (the `commit*` functions already
guard against `parseFloat` returning `NaN` and bail out without
calling the API — see `dashboard.html:837`, `:1125`).

### Delete the button rows, not just hide them

**Why not `display: none`:** the AGENTS.md "Seed data — classes
only, never assets" rule is a precedent for the project preferring
real removals over commented-out code. The buttons are pure
ceremony; leaving them in HTML would make a future reader wonder
what they're for. Dead CSS is removed in the same commit.

### Test migration: Enter press, not click

The e2e flow that opened the editor, typed, then clicked `salvar`
becomes: open editor, type, press Enter. The Playwright call
swaps from `.locator('[data-testid="*-commit"]').click()` to
`page.keyboard.press("Enter")` after the `.fill()`. The
integration test `test_t03_pages_routes.py` was asserting on raw
HTML for the presence of the `data-testid` attributes — those
asserts are dropped, since the dashboard HTML no longer contains
them by design.

## Risks / Trade-offs

- **[Accidental save on misclick]** → input is `type="number"` and
  the commit guards bail on `NaN`. Server-side validation also
  rejects negative or >100% values. Worst case: user re-opens and
  corrects.
- **[Asset table stretches too wide on 4K monitors]** → 1400px cap
  prevents this; if a future column is added and 1400px becomes
  cramped, the cap can be raised without structural change.
- **[E2e tests that depended on the commit button testid silently
  drift]** → updated in the same change. After the change, the
  selector dict entries for `*_commit` / `*_cancel` are removed.
- **[Historical OpenSpec archive still references the testids]** →
  archived changes are immutable history; no edit needed. The
  delta spec only updates the live spec at
  `openspec/specs/dashboard-inline-editing/spec.md`.

## Open Questions

None remaining. The three decision points (width, blur behavior,
button fate) were resolved in the explore conversation before this
proposal was drafted.
