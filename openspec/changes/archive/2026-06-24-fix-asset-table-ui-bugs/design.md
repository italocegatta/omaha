## Context

The asset table in `src/omaha/templates/dashboard.html` is rendered per class
via the `classSection` Alpine factory. It owns:

- The asset list (`assets`) — mutated by inline edit PATCHes.
- A `sortedAssets` getter (line ~940) that returns a freshly-sorted copy on
  every reactive read. The sort key is `sortKey` + `sortDir` (default
  `class` asc, secondary `alvo % classe` asc, tertiary name).
- A `_pinFrozen` helper (line ~904) called inside `sortedAssets` to splice
  the just-edited row back to its pre-edit index — implemented because
  PATCH was visibly reordering the row out from under the operator's
  cursor.

The current behaviour:

| Trigger | Current behaviour | Desired behaviour |
|---|---|---|
| PATCH on alvo % classe succeeds | `assets[i].target_pct` mutates → `sortedAssets` re-runs natural sort → pin splices edited row back to its old position; other rows still shift to fill the gap | Order of all rows in the class stays exactly as it was before the PATCH |
| PATCH on alvo % total succeeds | Same as above | Same as above |
| User clicks `<th>` for a column | `sortBy(key)` clears the pin, sets `sortKey`/`sortDir`, `sortedAssets` re-runs natural sort | Rebuild `displayAssets` snapshot from `assets` using the new sort |
| User clicks class header | (no handler — section is always visible) | Toggle `isOpen`; collapse/expand the body with the existing max-height animation |
| Dashboard loads | `isOpen: true` (default, hard-coded) | `isOpen: true` (default, in-memory; reload resets) |

The CSS for the collapse animation is already in
`src/omaha/static/app.css:521-526` (`.class-section-body { max-height: 1000px;
overflow: hidden; transition: max-height 200ms ease-out, opacity 200ms ease-out; opacity: 1; }`).
The `.class-section-body--collapsed` selector and the chevron span are the
missing pieces. The header already has `cursor: pointer` (vestigial from
before the toggle was removed).

Column widths in the asset table are uniform because
`.asset-table { table-layout: fixed; }` is set in
`src/omaha/static/app.css:708-713` but no `<th>` carries an explicit
`width`. With 8 columns, the browser distributes 12.5% per column. The text
columns "Ativo" (e.g. "Tesouro Selic 2029") and "Classe" (e.g. "Renda Fixa
Pós-Fixada") get visibly truncated at typical viewport widths (1280-1440
px). Numeric columns ("Qtd", "Alvo % total", etc.) have plenty of unused
space.

## Goals / Non-Goals

**Goals:**

- PATCH on `alvo % classe` or `alvo % total` does not change the order of
  any row in the class's asset table. The order is "frozen" between
  explicit user sort clicks.
- User can collapse a class section by clicking its header. The collapse
  uses the existing CSS transition (`max-height` + `opacity`). Default is
  expanded. State is in-memory; reload resets to expanded.
- Column widths are explicit: text columns get the room they need,
  numeric columns stay readable but don't waste space. Width changes
  animate.

**Non-Goals:**

- Persisting `isOpen` across page reloads (rejected for simplicity; the
  user said "in-memory only" — adding `localStorage` introduces a second
  source of truth that can drift from server state).
- Making column widths responsive / viewport-aware (would require
  container queries or JS-driven width calc; not in scope for a UI bug
  fix).
- Changing the sort key default (stays `class` asc, secondary `alvo %
  classe` asc, tertiary name).
- Changing the `Default sort applies on every load` behaviour (the
  snapshot is built from `assets` on `init` using the default sort key —
  reload re-asserts the default).
- Changing the alert card / group header / add-asset modal (out of scope
  — none of them interact with the bugs).

## Decisions

**Decision 1: Replace `sortedAssets` getter with `displayAssets` snapshot.**

```js
// On init:
this.displayAssets = this.assets.slice().sort(sortFn(this.sortKey, this.sortDir));

// sortBy:
this.sortKey = ...; this.sortDir = ...;
this.displayAssets = this.assets.slice().sort(sortFn(...));

// commitEdit / commitEditTotal / commitEditClassPct (on 200):
const a = this.displayAssets.find(x => x.id === id);
if (a) { a.target_pct = ...; a.target_pct_total = ...; }
// No re-sort. Order stays.
```

The `<template x-for="(a, idx) in displayAssets" :key="a.id">` iterates
the snapshot. Alpine's `:key="a.id"` ensures the row DOM element is
reused (not destroyed and re-created) when only the row's text content
changes — the operator sees a smooth value swap, not a flicker.

*Rationale:* the cleanest way to make the order independent of value
mutations. The snapshot is a regular array, not a getter, so it
re-evaluates only on `init` and `sortBy` clicks, not on every
`assets` mutation.

*Alternatives considered:*

- **Keep the getter, freeze the `assets` reference during PATCH.**
  Rejected: requires `Object.freeze` + cloning on every render, breaks
  Alpine's reactivity for the `classSum` getter that reads `assets[i].target_pct`.
- **Use `Object.freeze` on `assets` after init.** Rejected: same
  Alpine reactivity issue; `commitEdit` mutates the object directly
  so freezing blocks the legitimate PATCH path.
- **Mark `frozenAssetId` for *all* rows on PATCH.** Rejected: the pin
  logic in `_pinFrozen` is O(n²) in the worst case (freeze N rows,
  splice N rows back) and doesn't address the real issue: the user
  wants no reorder, not "every row frozen to its pre-PATCH position
  forever".

**Decision 2: `isOpen` lives on the `classSection` Alpine component.**

```html
<header class="class-section-header"
        data-testid="class-section-header"
        @click="isOpen = !isOpen">
  <span class="class-chevron"
        data-testid="class-chevron"
        :class="{'class-chevron--open': isOpen}">▸</span>
  <!-- swatch + name + stats unchanged -->
</header>
<div class="class-section-body"
     :class="{'class-section-body--collapsed': !isOpen}"
     x-show="isOpen" x-cloak>
```

*Rationale:* the state is per-class (each class section has its own
`isOpen`), and the existing factory already has the `isOpen: true` field
unused (line ~786). Reusing it avoids a new state container.

*Alternatives considered:*

- **`Alpine.store('classCollapse')`.** Rejected: overkill for in-memory
  UI state. Per-component is the right scope.
- **Toggling via a CSS-only `:checked` checkbox hack.** Rejected: would
  require restructuring the header DOM and breaks keyboard navigation.

**Decision 3: Default `isOpen: true` and in-memory only.**

*Rationale:* matches the user's explicit answer "in-memory only" and
keeps the default visible state identical to the current behaviour (so
existing tests that assert `dashboard-asset-row` is visible on load
still pass without modification).

*Alternatives considered:*

- **`localStorage` persistence.** Rejected: introduces a stale-state
  risk if a class is deleted (the `localStorage` key for the deleted
  class id never gets cleaned up), and the user explicitly opted out.

**Decision 4: Chevron icon is a `▸` glyph with `transform: rotate(90deg)`.**

```css
.class-chevron { display: inline-block; transition: transform 150ms; }
.class-chevron--open { transform: rotate(90deg); }
```

*Rationale:* a single glyph is cheaper than two (no font swap / DOM
toggle), and the rotation is GPU-accelerated (composite layer). Matches
the convention used in `audit_report.html:120` (the `page-section-header`
chevron).

*Alternatives considered:*

- **Swap `▸` and `▾` glyphs via `x-text`.** Rejected: causes layout
  shift if the glyphs have different widths. Rotation keeps the box
  stable.

**Decision 5: Column widths are declared in CSS via `:nth-child(N)`.**

```css
.asset-table th:nth-child(1) { width: 24%; }  /* Ativo */
.asset-table th:nth-child(2) { width: 18%; }  /* Classe */
.asset-table th:nth-child(3) { width:  6%; }  /* Qtd */
.asset-table th:nth-child(4) { width: 14%; }  /* Valor */
.asset-table th:nth-child(5) { width: 11%; }  /* Alvo % classe */
.asset-table th:nth-child(6) { width: 11%; }  /* Atual % classe */
.asset-table th:nth-child(7) { width:  9%; }  /* Alvo % total */
.asset-table th:nth-child(8) { width:  7%; }  /* Atual % total */
.asset-table th { transition: width 200ms; }
```

*Rationale:* centralises the table layout in CSS (no per-`<th>` inline
styles), survives Jinja template regeneration, and the `transition:
width 200ms` makes the table animate from its first-paint (no widths,
uniform) to its final widths smoothly instead of jumping.

*Alternatives considered:*

- **Inline `style="width:24%"` on each `<th>`.** Rejected: spreads the
  layout decision across the template + CSS, harder to audit.
- **CSS Grid instead of table.** Rejected: breaks the existing
  `data-testid` selectors, the row `:nth-child(even)` zebra striping,
  and the sticky `<thead>`.

**Decision 6: One change, not three.**

*Rationale:* the three bugs touch the same file
(`src/omaha/templates/dashboard.html`), the same spec
(`openspec/specs/dashboard-inline-editing/spec.md`), and the same test
file (`tests/e2e/test_asset_table.py`). Reviewing them together is
cheaper than three separate review rounds. The "synced spec" deliverable
is one `archive` command at the end.

*Alternatives considered:*

- **Three separate changes** (one per bug). Rejected: triple the spec
  ceremony, triple the review cycles, triple the merge conflict risk on
  the same `classSection` factory.

## Risks / Trade-offs

- **Risk:** removing `_pinFrozen` breaks a behaviour the operator has
  learned to expect (row held in place during edit). *Mitigation:* the
  new behaviour is strictly better (the entire table is frozen, not
  just the edited row), and the snapshot mechanism is the simpler
  mental model. The new E2E test `test_patch_does_not_reorder_rows`
  locks the behaviour in.

- **Risk:** the chevron toggle changes the default visible area of the
  dashboard, which could mask the alert card or the add-asset button.
  *Mitigation:* the alert card and the "+ Ativo" button are outside the
  per-class `<article class="class-section">` (they sit in the parent
  `<section class="dashboard-distribution">`), so collapsing a class
  body doesn't move them. Verified by reading lines 60-90 of
  `dashboard.html`.

- **Risk:** `table-layout: fixed` + explicit widths can cause text
  overflow in extreme cases (e.g. an asset name longer than the column
  width). *Mitigation:* the 24% width for "Ativo" accommodates names
  up to ~25 characters at 1280px viewport; longer names get ellipsis
  via the existing `white-space: nowrap` + `text-overflow: ellipsis`
  on `.asset-table th` (added in the same change). If a name is so
  long it overflows, the test `test_column_widths_fit_default_viewport`
  catches it.

- **Trade-off:** `transition: width 200ms` on `<th>` re-paints on every
  layout recalc. At 8 columns, this is negligible. If the table grows
  to 20+ columns in the future, the transition should be scoped to
  specific columns.

## Migration Plan

- **Deployment:** no DB migration, no API change. Pure UI. Ships as a
  single commit touching `dashboard.html`, `app.css`, the E2E test, and
  the spec delta.
- **Rollback:** `git revert` the commit. The `classSection` factory's
  pre-fix shape (with `sortedAssets` getter + `_pinFrozen`) is
  recoverable from the previous commit.
- **Spec sync:** run `openspec archive fix-asset-table-ui-bugs` after
  merge to copy the delta into `openspec/specs/dashboard-inline-editing/spec.md`
  and remove the change directory.

## Open Questions

*(none — all design decisions resolved during the explore phase.)*
