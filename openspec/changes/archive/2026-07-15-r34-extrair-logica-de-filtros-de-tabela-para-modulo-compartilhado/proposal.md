## Why

Filter JS logic (filterActive, toggleFilterPanel, clearFilter, rangeBounds, clampRange*, rangeFillStyle, filteredRows) is copy-pasted across 3 locations: `rebalance.html` (~120 lines), `test/rebalance_table_poc.html` (~120 lines), and `_patrimonio_add_asset_modal.html` (~80 lines). HTML filter panels (enum/range/composite) are duplicated between `rebalance.html` and `_rebalance_plan.html`. This creates maintenance drift — a bug fix in one location doesn't propagate. R33 already extracted shared formatters to `table-formatters.js`; this slice completes the pattern by extracting the filter logic.

## What Changes

- Create `src/omaha/static/table-filters.js` — ES module exporting reusable filter functions (rangeBounds, clampRangeMin, clampRangeMax, rangeFillStyle, rangeStep, ensureRangeBounds, filteredRows computation, filterActive, toggleFilterPanel, clearFilter, formatRangeValue)
- Create `src/omaha/templates/_table_filter_panels.html` — Jinja2 partial with the enum/range/composite filter panel HTML (reused by rebalance via Alpine x-if and by portfolio via _filter_controls.html macro)
- Refactor `rebalance.html` — replace inline filter JS with import from `table-filters.js`; replace inline filter HTML in `_rebalance_plan.html` with include of shared partial
- Refactor `_patrimonio_add_asset_modal.html` — replace inline filter JS with import from `table-filters.js`
- Refactor `test/rebalance_table_poc.html` — replace inline filter JS with import from `table-filters.js`
- `_filter_controls.html` macro stays as-is (already uses Jinja2 macro pattern); it continues to consume the same Alpine method names that will now come from `table-filters.js`

## Capabilities

### New Capabilities
- `shared-table-filters`: Shared JS module + HTML partial for table column filtering (enum, range, composite types). Covers filter state management, range slider logic, panel rendering, and row filtering.

### Modified Capabilities
_(none — this is pure extraction/refactor; no behavioral change)_

## Impact

- **Files created**: `src/omaha/static/table-filters.js`, `src/omaha/templates/_table_filter_panels.html`
- **Files modified**: `rebalance.html`, `_rebalance_plan.html`, `_patrimonio_add_asset_modal.html`, `test/rebalance_table_poc.html`
- **No breaking changes**: Alpine method signatures stay identical; template markup stays identical; just moved to shared locations
- **No CSS changes**: R30 already extracted shared CSS; this slice is JS + HTML only
- **Dependencies**: None new. Uses same ES module pattern as `table-formatters.js` (R33)
