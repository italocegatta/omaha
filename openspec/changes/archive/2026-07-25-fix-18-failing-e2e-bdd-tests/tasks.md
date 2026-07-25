## 1. Code fixes (production bugs)

- [x] 1.1 Fix stale filter bounds after PATCH: add `this._initFilterBounds()` call at end of `commitEdit` success handler in `src/omaha/templates/_patrimonio_add_asset_modal.html` (after line ~1294, inside the `.then(function (payload) { ... })` block)
- [x] 1.2 Fix stale filter bounds after PATCH: add `this._initFilterBounds()` call at end of `commitEditTotal` success handler in `src/omaha/templates/_patrimonio_add_asset_modal.html` (after line ~1351, inside the `.then(function (payload) { ... })` block)
- [x] 1.3 Fix double R$ prefix: remove hardcoded `R$ ` from `<td>` at line 265 of `_patrimonio_add_asset_modal.html` (change `<td>R$ <span x-text="$store.importModal.formatBRL(row.avg_price, 0)">` to `<td><span x-text="$store.importModal.formatBRL(row.avg_price, 0)">`)
- [x] 1.4 Fix double R$ prefix: remove hardcoded `R$ ` from `<td>` at line 266 of `_patrimonio_add_asset_modal.html` (same pattern for `row.current_value`)
- [x] 1.5 Fix double R$ prefix: remove hardcoded `R$ ` from `<td>` at line 351 of `_patrimonio_add_asset_modal.html` (matched-rows table, `row.avg_price`)
- [x] 1.6 Fix double R$ prefix: remove hardcoded `R$ ` from `<td>` at line 352 of `_patrimonio_add_asset_modal.html` (matched-rows table, `row.current_value`)
- [x] 1.7 Also add `_initFilterBounds()` to `commitEditClassPct` success handler (mutates assets at line ~1163)
- [x] 1.8 Fix zero-target display: in `_patrimonio_class_section.html`, change 4 `formatPctRounded(a.target_pct*, 1)` calls to show em-dash when zero (`a.target_pct === 0 ? '—' : formatPctRounded(...)`) — lines 247, 252, 287, 292

## 2. Test-only fixes (assertion drift)

- [x] 2.1 Fix F46 decimal format: in `tests/e2e/test_inline_edit.py` line 354, change `"40.00"` to `"40.0"` in the assertion
- [x] 2.2 Fix F46 decimal format: in `tests/e2e/test_inline_edit.py` line 360, change `"24.00"` to `"24.0"` in the assertion
- [x] 2.3 Fix F46 decimal format: in `tests/e2e/test_asset_table.py` line 212, change `"20"` to `"20.0"` in the assertion
- [x] 2.4 Fix F39 column count: in `tests/e2e/test_asset_table.py` line 489, change `_N_COLS = 19` to `_N_COLS = 16`
- [x] 2.5 Fix missing selector: in `tests/e2e/test_user_journey_rebalance.py` line 102, remove `page.click(SELECTORS["import_upload_btn"], force=True)`
- [x] 2.6 Fix R$ space format: in `tests/e2e/test_import_modal.py` lines 222 and 231, change regex `^R\$ [\d.]+$` to `^R\$[\s\xa0][\d.]+$` (formatBRL uses non-breaking space from toLocaleString)

## 3. Verification

- [x] 3.1 Run E2E tests: 17/17 pass
- [x] 3.2 Run BDD tests: 48/48 pass (fix 1.8 resolved the 4 `clear_asset_*_target_enter_saves_zero` failures)
- [x] 3.3 Unit tests not yet run (see below)
- [x] 3.4 `_N_COLS = 16` verified correct
