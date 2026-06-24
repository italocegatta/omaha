## Why

Three UI bugs in the dashboard asset table (`src/omaha/templates/dashboard.html`)
make the table frustrating to operate in a portfolio with multiple classes and
frequent rebalancing:

1. **PATCH reorders rows.** Editing "Alvo % classe" (or "Alvo % total") and
   committing the value PATCHes the server, but the row order visibly shifts
   on success. The operator perceives this as "the value didn't persist" or
   "the table is jumping under my cursor". The current `_pinFrozen` mechanism
   only holds the *edited* row in place — every other row in the same class
   re-sorts to fill the gap because `sortedAssets` is a reactive getter that
   re-runs on every `assets` mutation.
2. **Class collapse was removed.** A previous change
   (`openspec/changes/archive/2026-06-22-asset-table-view/`) intentionally
   removed the chevron toggle and pinned `isOpen: true` to keep sections
   always visible (D016 was retired). Users with many classes need to be able
   to collapse sections they're not actively editing. The CSS for
   `.class-section-body` already has the max-height/opacity transition — the
   toggle is the only piece missing.
3. **Column widths are uniform.** `.asset-table` uses `table-layout: fixed`
   with no explicit `<th>` widths, so the browser distributes 8 columns at
   12.5% each. Text columns ("Ativo" like "Tesouro Selic 2029", "Classe" like
   "Renda Fixa Pós-Fixada") get truncated while narrow numeric columns waste
   space. Spec already says table is sortable but says nothing about widths.

This change captures the fix for all three in one proposal because they share
the same file (`dashboard.html`), the same spec
(`openspec/specs/dashboard-inline-editing/spec.md`), and the same test file
(`tests/e2e/test_asset_table.py`).

## What Changes

- **`src/omaha/templates/dashboard.html` — `classSection` Alpine component:**
  - Replace the reactive `sortedAssets` getter with a `displayAssets` snapshot
    array. `init()` and `sortBy()` rebuild the snapshot from `assets` using
    the current `sortKey`/`sortDir`. `commitEdit()` / `commitEditTotal()` /
    `commitEditClassPct()` mutate `target_pct` **in place** on `displayAssets`
    (no re-sort). The `<template x-for>` iterates `displayAssets` instead of
    `sortedAssets`.
  - Remove the `_pinFrozen` helper, the `frozenAssetId` / `frozenIndex`
    fields, and the pinning logic in `startEdit` / `startEditTotal` /
    `cancelEdit` / `cancelEditTotal`. They are no longer needed because the
    order never changes between explicit sort clicks.
  - Bind the existing `isOpen: true` state to the class header and body:
    header `@click="isOpen = !isOpen"`, body `:class="{'class-section-body--collapsed': !isOpen}" x-show="isOpen"`.
    Add a chevron span (`▸` / `▾`) inside the header that rotates on toggle.
    `isOpen` stays in-memory only (no `localStorage`); reloading the page
    resets to `isOpen: true`.
- **`src/omaha/static/app.css`:**
  - Add `.class-section-body--collapsed { max-height: 0; opacity: 0; }` to
    drive the existing transition.
  - Add `.class-chevron` with `transform: rotate(0deg)` and
    `.class-chevron--open` with `transform: rotate(90deg)`, plus a
    `transition: transform 150ms` so the chevron rotates smoothly.
  - Add explicit `width` declarations on `.asset-table th:nth-child(N)` for
    each of the 8 columns (Ativo 24%, Classe 18%, Qtd 6%, Valor 14%, Alvo %
    classe 11%, Atual % classe 11%, Alvo % total 9%, Atual % total 7%).
    Add `transition: width 200ms` on `.asset-table th` so any width change
    (initial paint, future responsive adjustments) animates smoothly.
- **`tests/e2e/test_asset_table.py`:** add `test_patch_does_not_reorder_rows`
  that seeds one class with three assets at distinct `target_pct` values,
  edits the first asset to a value that would naturally sort it to the end
  of the asc list, and asserts the order of `[data-asset-id]` attributes is
  unchanged after the PATCH lands. Also add
  `test_class_header_toggle_collapses_and_expands_assets` that clicks the
  header and asserts the asset rows go from visible → hidden → visible.
- **`openspec/specs/dashboard-inline-editing/spec.md`:** replace the
  "Seções colapsáveis" requirement (which currently mandates no chevron and
  no toggle) with a new requirement that:
  - Renders a chevron in the class header.
  - Toggles `isOpen` on header click.
  - Defaults to `isOpen: true` on every load (in-memory only, no persistence).
  - The "Seções colapsáveis" scenarios are updated to assert toggle
    behavior, not the absence of the chevron.

## Capabilities

### New Capabilities

*(none)*

### Modified Capabilities

- `dashboard-inline-editing`: rewrite the "Seções colapsáveis" requirement
  to describe the header-click toggle and the default-expanded / in-memory
  state. The other requirements (sortable table, inline edit, group
  header) stay as-is; the new column-width rule is added under the table
  requirement as a new sub-requirement.

## Impact

- **Affected code:**
  - `src/omaha/templates/dashboard.html` (`classSection` factory, header
    template, body template, asset row template)
  - `src/omaha/static/app.css` (column widths, chevron, body collapse)
  - `tests/e2e/test_asset_table.py` (two new E2E tests)
  - `openspec/specs/dashboard-inline-editing/spec.md` (delta: replace
    "Seções colapsáveis" requirement, add column-width sub-requirement
    under the table requirement)
- **Affected users:** anyone with 2+ classes who edits target percentages
  inline. The reorder bug is most visible in classes with 4+ assets at
  distinct `target_pct` values; the collapse bug is most visible in
  profiles with 4+ classes.
- **Affected tests:** the 5 stale comments in `tests/e2e/test_visual_gate.py`,
  `test_user_journey.py`, `test_asset_crud.py`, and `test_inline_edit.py`
  that say "class sections are always visible" / "Sections collapse on
  reload (D016)" get a one-line comment update to reflect the new
  default-expanded + user-toggleable state. The assertions in those tests
  (waiting for `dashboard-asset-row` to be visible) still pass because
  `isOpen: true` is the default.
- **Migration:** none. No data model change, no DB migration, no API
  change. The behaviour is purely UI.
- **Performance:** the `displayAssets` snapshot is a single `.slice()` of
  the assets array (no per-render sort), so PATCH-driven renders are
  cheaper than the current reactive getter. Sort clicks are slightly more
  expensive (rebuild snapshot) but only fire on user action.
