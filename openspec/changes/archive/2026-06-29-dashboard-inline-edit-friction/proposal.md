## Why

Editing the dashboard's inline target-% fields currently requires a
double click (one to mount the input, another to focus the cursor)
and refuses empty commits (the input blanks out and the server
returns 422). The visible Chrome / Firefox number-input spinner
adds visual noise that the user has to mentally filter. Each
interaction costs an extra click on mouse and an extra tap on
touch; clearing a value to retype triggers a 422 instead of
saving zero. The friction is high for the single most common edit
on the dashboard (rebalancing target weights).

## What Changes

- **One click to edit**: clicking the `Alvo` pill (header) or any
  `alvo %` cell (table) auto-focuses the inline `<input>` and
  pre-selects its content on the same handler, so the first
  keystroke after the click replaces the value. No second click
  needed.
- **Empty commit equals zero**: clearing the input and pressing
  Enter / blurring coerces the empty string to `"0"` client-side
  before PATCH, so the server stores zero without a 422 round
  trip. Applied to all three inline editors: class header
  (`Alvo`), per-asset (`alvo % classe`), per-asset
  (`alvo % total`).
- **Clean input chrome**: drop the native browser spinner
  (`▲`/`▼`) on the inline `<input type="number">` via CSS so the
  visual is a flat field matching the surrounding pill. Keyboard
  `↑` / `↓` continues to step the value.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dashboard-inline-editing`: add three new scenarios covering
  auto-focus on click, empty-commit-equals-zero, and spinner-less
  input chrome. Existing behavior (Enter / blur commits, Escape
  cancels, no save button, server-side range validation) is
  unchanged.

## Impact

- `src/omaha/templates/dashboard.html` — add `x-ref` to the three
  inline inputs; call `this.$nextTick(() => $refs.X.focus();
  $refs.X.select())` from the matching `startEdit*` handlers;
  coerce empty value to `"0"` in the three `commitEdit*`
  functions before PATCH.
- `src/omaha/static/app.css` — add four selectors to suppress
  WebKit / Blink spinner buttons and one `appearance:
  textfield` rule for Firefox on the two inline-edit-input
  classes.
- `openspec/specs/dashboard-inline-editing/spec.md` — append the
  three new scenarios to the existing requirements
  ("Inline editing de target % da classe" and "Editor inline do
  alvo % do ativo...").
- No backend changes. `_parse_pct("0")` already returns `Decimal("0")`
  on the existing `PATCH /api/classes/{id}` and
  `PATCH /api/assets/{id}` routes; the coercion happens before
  the request hits the wire.
- Tests: extend `tests/bdd` scenarios in `tests/bdd/feature/`
  (single-click + type, clear + Enter stores zero) and
  unit-cover the empty-coercion helpers if we extract one.
