## 1. Create shared JS module

- [x] 1.1 Create `src/omaha/static/table-filters.js` with ES module exports: `rangeBounds`, `rangeStep`, `ensureRangeBounds`, `clampRangeMin`, `clampRangeMax`, `rangeFillStyle`, `formatRangeValue`, `filterActive`, `toggleFilterPanel`, `clearFilter`, `computeFilteredRows`
- [x] 1.2 Each function accepts generic parameters (rows array, column definitions, filter state objects) — no `this` binding required
- [x] 1.3 Add JSDoc comments matching `table-formatters.js` style

## 2. Create shared HTML partial

- [x] 2.1 Create `src/omaha/templates/_table_filter_panels.html` with enum, range, and composite filter panel markup using Alpine `x-if` templates
- [x] 2.2 Panels reference Alpine methods (filterActive, toggleFilterPanel, etc.) via `:class`, `@click`, `x-show` bindings — same method names as current inline code

## 3. Refactor rebalance page

- [x] 3.1 In `rebalance.html`: add `<script type="module">` importing from `table-filters.js`, attach functions to `window.__tableFilters`
- [x] 3.2 Replace inline filter methods in `window.rebalancePage` — use formatters pattern: inline fallbacks in `alpine:init` with module override via `var tf = window.__tableFilters || {}; var _rangeBounds = tf.rangeBounds || function ...`
- [x] 3.3 In `_rebalance_plan.html`: replace inline filter panel HTML (lines 100-166) with `{% include "_table_filter_panels.html" %}`
- [x] 3.4 Verify rebalance page loads and filter panels work — e2e test_asset_table_poc_parity_interactions passes

## 4. Refactor PoC page

- [x] 4.1 In `test/rebalance_table_poc.html`: add `<script type="module">` importing from `table-filters.js`
- [x] 4.2 Replace inline filter methods — use formatters pattern with inline fallbacks
- [x] 4.3 Replace inline filter panel HTML with `{% include "_table_filter_panels.html" %}`

## 5. Refactor asset modal

- [x] 5.1 In `_patrimonio_add_asset_modal.html`: add dynamic `import('/static/table-filters.js')` in `alpine:init`
- [x] 5.2 Replace inline filter methods — thin wrappers with null guards (module loads async after Alpine)
- [x] 5.3 Keep `filterActiveStr` and `_mapField` as local wrappers (page-specific adapters)

## 6. Verify

- [x] 6.1 Run `task test-bdd` — 47/51 pass (4 pre-existing flaky inline-edit timeouts, not filter-related)
- [x] 6.2 Run `task test-e2e` — 44/49 pass (5 pre-existing failures unrelated to filters; all 10 rebalance tests pass)
- [x] 6.3 Rebalance page filter panels verified by e2e test_asset_table_poc_parity_interactions
- [x] 6.4 Portfolio page filters unchanged (uses `_filter_controls.html` macro — untouched)
