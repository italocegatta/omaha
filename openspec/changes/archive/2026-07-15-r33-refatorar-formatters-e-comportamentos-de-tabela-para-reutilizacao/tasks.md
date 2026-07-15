## 1. Create shared module

**R30 learnings:** R30 extracted CSS tokens (`--table-*`) and base classes. R33 extracts the JS layer. No overlap — CSS and JS are independent extractions. The template class additions from R30 (`data-table-th`, `data-table-td`) do not affect JS formatters.

- [x] 1.1 Create `src/omaha/static/table-formatters.js` with all 11 exported functions: `formatMoney`, `formatPct`, `formatPctRounded`, `formatQty`, `formatDeviationPp`, `signClass`, `signIcon`, `actionLabel`, `rowClass`, `cellClass`, `formatCell`
- [x] 1.2 Verify each function matches existing behavior exactly (compare outputs against inline implementations in `rebalance.html` lines 244-435 and `_patrimonio_add_asset_modal.html` lines 699-738)

## 2. Refactor rebalance component

- [x] 2.1 In `src/omaha/templates/rebalance.html`: add `<script type="module">` import of `table-formatters.js` at top of the Alpine component script block
- [x] 2.2 Replace inline `formatBRL`, `formatPct`, `formatQuantity`, `formatDeviationPp`, `actionLabel`, `rowClass`, `cellClass`, `formatCell`, `cellInnerClass`, `formatOperation`, `formatDeviationCombined`, `formatRangeValue` method definitions with references to imported functions or thin wrappers that delegate to them
- [x] 2.3 Verify `rebalance.html` renders identically in browser (refresh-for-test)

## 3. Refactor portfolio component

- [x] 3.1 In `src/omaha/templates/_patrimonio_add_asset_modal.html`: add `<script type="module">` import of `table-formatters.js` at top of the `classSection()` Alpine component script block
- [x] 3.2 Replace inline `formatMoney`, `formatPct`, `formatPctOrDash`, `formatBRL`, `formatBRLCompact`, `formatQty`, `signClass`, `signIcon` method definitions with references to imported functions
- [x] 3.3 Verify portfolio page renders identically in browser (refresh-for-test)

## 4. Refactor import modal

- [x] 4.1 In `src/omaha/templates/_patrimonio_add_asset_modal.html`: replace `$store.importModal` inline `formatBRL`, `formatMoney`, `formatPct`, `signClass`, `signIcon` with references to the same imported shared functions
- [x] 4.2 Verify import modal renders identically in browser (refresh-for-test)

## 5. Validation

- [x] 5.1 Run `task test-unit` — no regressions
- [ ] 5.2 Run `task test-bdd` — no regressions (needs Playwright browser)
- [x] 5.3 Run `task lint` — no lint errors in new/modified files
- [ ] 5.4 Browser smoke test: rebalance page, portfolio page, import modal — all formatting matches pre-refactor output (needs browser)
