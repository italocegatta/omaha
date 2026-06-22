## Context

The dashboard today is a tree of `<article class="class-section">` cards. Each
card owns a `<ul class="dashboard-asset-list">` of assets, each asset carries a
4-cell percentage grid (alvo% classe / atual% classe / alvo% total / atual%
total), and one cell (`asset-target-pct-class`) is editable through a click →
input → PATCH dance that runs the server-side `validate_target_pct_sum` gate.
Per-class cards are collapsed by default (D016) and the user has to click a
chevron to see the assets inside. There is no global sort, no way to edit
`alvo% total` directly, and the 422 rejection on a sum ≠ 100 forces the user
into a tight "edit → 422 → cancel → edit" loop without a clear path back to
100%.

The change reshapes this surface into a single flat table grouped by class
with sortable columns, makes both `alvo% classe` and `alvo% total` editable,
removes the rejection gate, defaults class sections to expanded, and surfaces
the deviation through a sticky alert card and per-class inline badges with
green/yellow/red severity tiers.

## Goals / Non-Goals

**Goals:**

- One table view across all assets, grouped by class, with sortable columns.
- Both `alvo% classe` and `alvo% total` editable inline. Editing either
  updates the other with a deterministic, client-visible formula.
- All edits accepted (no 422). Deviation surfaced through alert card and
  per-class badges.
- Class sections default to expanded and stay expanded after any edit
  within them.
- Sticky alert card with severity coloring shows portfolio-level and
  per-class deviation at all times while deviation exists.
- Testids that are still meaningful after the refactor are preserved;
  testids that only made sense in the card layout are dropped (e.g. the
  per-class `+ Ativo` form).

**Non-Goals:**

- No new backend write surface. `PATCH /api/assets/{id}` continues to
  accept `{target_pct: "..."}`; the body does not grow a `target_pct_total`
  field. The total is always derived from `target_pct * class.target_pct / 100`.
- No new model column. `Asset.target_pct_total` remains a derived value
  computed by `pages.py::_build_dashboard_context` and on the client.
- No persistence of the sort order. Reload resets to default.
- No removal of the standalone `/assets` page (already 302-redirects to
  `/` per S03/T05). The redirect stays.
- No change to the CSV import flow (`/api/import/*`).

## Decisions

### D1. Table is `<table>` HTML, not a CSS grid of divs

Native `<table>` with `<thead>` and `<tbody>`. Per-class grouping is a
`<tr class="asset-group-header">` inside the same `<tbody>`, carrying
`color`, `name`, `target %`, `current %`, and a delta badge. Native table
gives us column sort for free (via JS-controlled `<th>` clicks) and
sticky-header behavior in CSS without reinventing keyboard nav. Sort
indicators are unicode triangles in the `<th>`.

### D2. Sort is in-memory Alpine state, default = class asc + alvo% classe asc

A `sortKey` and `sortDir` pair on a new top-level `assetTable` Alpine
component. A computed getter `sortedAssets` walks the assets, groups by
class, and sorts each group by the active key. Class header bands stay
attached to their group. Click on `<th>` toggles `sortDir` if the key
matches, otherwise sets `sortKey` and `sortDir = 'asc'`. Default keys
on every load (no `localStorage`).

### D3. Edit `alvo % classe` → derive `alvo % total` (same as today)

When the user commits a new `target_pct` for an asset, the PATCH handler
updates `Asset.target_pct`. The Alpine component recomputes
`a.target_pct_total = (a.target_pct * self.classTargetPct) / 100` in the
local row model, identical to the existing `commitEdit` behavior. No
client math change. Server is the source of truth for `target_pct`;
client mirrors for display.

### D4. Edit `alvo % total` → back-solve `alvo % classe` against class anchor (option B)

When the user commits a new `alvo % total`, the client computes
`new_target_pct = total * 100 / classTargetPct` and PATCHes the resulting
`target_pct` to the server. The same `PATCH /api/assets/{id}` endpoint
handles the write. No new endpoint. The client surfaces a confirm hint
inline next to the input ("isso vai recalcular a distribuição dentro da
classe Ações — outros ativos não mudam") so the user knows the effect is
contained. The 422 gate is removed (D6), so the write always commits and
the resulting per-class sum is whatever the math produces; the alert
card surfaces the new deviation.

### D5. `alvo % classe` and `alvo % total` are mutually exclusive edit cells

Only one cell per row is in edit mode at a time. The other displays the
last-computed value. Clicking a different cell on the same row commits
the in-flight value (if valid range) and opens the new cell. If the
in-flight value is empty or out of range, the in-flight edit shows an
error and the new cell does not open. This is the same per-class-section
mutual exclusion that the current `editingAssetId` field already
enforces, lifted to per-row.

### D6. Per-class sum gate is removed from PATCH and POST `/api/assets`

The 422 rejection in `routes/assets.py` lines 294 (POST) and 390 (PATCH)
is removed. Per-row range check (`0 ≤ pct ≤ 100`) stays. The
`validate_target_pct_sum` helper stays as the canonical
formatter for the alert message — both the per-class delta badge and
the sticky alert card call it. Unit tests for the helper
(`tests/test_t01_asset_target.py`) are unchanged. The route tests that
pinned the 422 behavior in `tests/test_t99_assets_patch.py` are inverted
to assert 200 + the row mutated + a per-class sum that exceeds 100
stored on disk.

### D7. Class sections default to expanded; force-expanded after any edit

`classSection` Alpine component's `isOpen` initializes to `true` (was
`false` per D016). On a successful `commitEdit` (asset or class) the
component sets `self.isOpen = true` so the user always sees the result
of their edit without scrolling back up. The chevron still toggles
manually for users who want to close a section to declutter. The
"default closed" D016 rule is removed.

### D8. Alert card severity tiers

```
|delta|   | severity  | color token         |
|---------|-----------|---------------------|
| ≤ 0.01  | ok        | --alert-ok          |
| 0.01<d≤5| warn      | --alert-warn        |
| > 5     | danger    | --alert-danger      |
```

The 0.01 tolerance mirrors `SUM_TOLERANCE` in `omaha.validators`. The 5%
threshold is fixed for v1 (no user setting). Applied identically to the
per-class badge and the portfolio-level sticky card. Both severities
update reactively from the same `classSum` store extended to track
per-class deltas.

### D9. Sticky alert card lives inside the "Ativos" section, not the page

`position: sticky; top: 0;` on `.asset-allocation-alert` so it pins to
the top of the section as the user scrolls through assets, but releases
when the user scrolls past the section into the portfolio header / nav.
The card carries the portfolio-level delta and a list of class-level
deviations. When every class and the portfolio are at 100% the card
hides (no DOM presence) and the per-class badges show "OK" in green.

### D10. `+ Ativo` collapses from N per-class buttons into one dashboard-level control

Each class's `dashboard-add-asset-btn` and `dashboard-add-asset-form`
testids are dropped. A single `dashboard-add-asset-open` button sits
above the table and opens a modal (reusing the import modal's overlay
markup, not its state). The modal carries a class `<select>` (using the
established `x-init $nextTick` + `x-effect` pattern for dynamic options)
and the asset name + `target_pct` inputs. Submit POSTs to
`/api/assets` and reloads the page on 201. The form's `target_pct` is
optional and ranges 0-100; off-100 sums are accepted (D6).

### D11. Testids kept vs dropped

**Kept** (still meaningful on the new layout):
- `data-testid="asset-row-name"`, `asset-current-value`,
  `asset-target-pct-class`, `asset-target-pct-class-editing`,
  `asset-inline-edit-input`, `asset-inline-edit-commit`,
  `asset-inline-edit-cancel`, `asset-current-pct-class`,
  `asset-target-pct-total`, `asset-current-pct-total`,
  `asset-pct-grid` (now wraps the row's editable cells, not a 4-cell
  grid), `dashboard-asset-row` (on the new `<tr>`), `class-color-swatch`,
  `class-section-name`, `class-target-pct-view`,
  `class-inline-edit-input`, `class-inline-edit-commit`,
  `class-inline-edit-cancel`, `class-inline-edit-error`,
  `class-delta-badge`, `class-current-pct`, `class-summary`,
  `class-summary-row`, `class-summary-total`, `class-compare-bar`,
  `dashboard-class-section`.

**Dropped** (card-layout only):
- `data-testid="dashboard-add-asset-btn"`,
  `data-testid="dashboard-add-asset-form"`, `data-testid="dashboard-add-asset-name-input"`,
  `data-testid="empty-state-create-asset"` (per-class `+ Ativo` empty
  state).

**New**:
- `data-testid="asset-allocation-alert"` (sticky card),
- `data-testid="asset-allocation-alert-portfolio"` (portfolio total in
  the card),
- `data-testid="asset-allocation-alert-class"` (per-class list item
  inside the card),
- `data-testid="asset-group-header"` (per-class `<tr>` band),
- `data-testid="asset-group-header-alert"` (inline badge on the band),
- `data-testid="asset-table-th-{column}"` (each sortable header),
- `data-testid="asset-table-sort-{column}"` (sort indicator),
- `data-testid="asset-target-pct-total-editing"` (the new editable
  cell for `alvo % total`),
- `data-testid="asset-target-pct-total-edit-input"`,
- `data-testid="asset-target-pct-total-edit-commit"`,
- `data-testid="asset-target-pct-total-edit-cancel"`,
- `data-testid="dashboard-add-asset-open"` (single dashboard-level
  button),
- `data-testid="dashboard-add-asset-modal"`,
- `data-testid="dashboard-add-asset-modal-class"`,
- `data-testid="dashboard-add-asset-modal-name"`,
- `data-testid="dashboard-add-asset-modal-target"`,
- `data-testid="dashboard-add-asset-modal-submit"`.

## Risks / Trade-offs

- **Risk:** dropping `dashboard-add-asset-btn` testid breaks the
  `test_t03_assets_e2e.py` empty-state assertion (line 265) and the
  per-class add flow in `test_s03_user_journey.py`.
  **Mitigation:** replace those assertions with the modal selectors
  (D11). The user-visible behavior (add an asset from the dashboard)
  is preserved.

- **Risk:** removing the 422 gate allows the DB to store a per-class
  sum that exceeds 100 indefinitely. If the user closes the tab
  without resolving, the next load still shows the deviation but the
  data is inconsistent.
  **Mitigation:** the alert card persists across reloads; the data
  invariant is now advisory (alert-driven) rather than enforced. The
  user explicitly requested this. The `Asset.target_pct` column still
  enforces `Numeric(5, 2)` so the per-row range is safe.

- **Risk:** back-solving `target_pct` from `target_pct_total` (D4) can
  produce fractional `target_pct` values that, summed across the
  class, no longer equal 100. Example: class.target_pct = 30, user
  edits PETR4's total to 20 → target_pct = 66.67. Other assets in the
  class stay at their current values. If those don't sum to 33.33,
  the class is off-100.
  **Mitigation:** the alert card shows the resulting deviation so the
  user can adjust. The math is honest: editing the total is a precise
  back-solve, not a guess.

- **Risk:** sticky positioning on the alert card interacts with the
  existing portfolio header sticky. The dashboard already has a
  multi-section layout where the portfolio header pins to the top of
  the page on scroll.
  **Mitigation:** the alert card sticks to the top of the "Ativos"
  section, not the page. The two stickies don't overlap.

- **Risk:** in-memory sort state is lost on every page reload. Users
  who customize a sort lose it on F5.
  **Mitigation:** documented as a non-goal. If the user later wants
  persistence, add a `localStorage` key in a follow-up change.

## Migration Plan

No data migration. The `Asset` table is unchanged. The change is a
template + client-state + route-validation refactor. Roll back by
restoring `dashboard.html`, `routes/assets.py` to its gate-enforcing
state, and the test suite's 422 assertions in `test_t99_assets_patch.py`.

Deploy order:
1. Land the template + Alpine changes behind a feature flag (or
   directly — the change is fully client-visible on load).
2. Remove the gate in `routes/assets.py`. The 422 removal is the only
   server-side change.
3. Invert the affected tests in `test_t99_assets_patch.py` and any
   e2e selectors that asserted the disabled save button.

## Open Questions

- **Q1.** For the `alvo % total` edit cell, should the confirm hint
  appear *before* the save (modal/alert on click) or *inline next to
  the input*? My pick: inline next to the input (less interruption,
  matches the rest of the inline-edit style). User to confirm.
- **Q2.** Sort default key for secondary tie-break within a class —
  `name asc`? `display_order asc`? My pick: `name asc` (stable,
  human-readable). User to confirm.
- **Q3.** When the table is empty (no classes or no assets), should
  the alert card render a "Cadastre uma classe para começar" empty
  state, or stay hidden? My pick: hidden, with the existing
  `empty-state` markup at the section root showing instead. User to
  confirm.
