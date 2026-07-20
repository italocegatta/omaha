## Why

18 E2E and BDD tests are failing after recent feature commits (F46 decimal formatting, F47 filter teleport fix, F39 margin revision). Two are real production bugs (stale filter bounds after PATCH, double R$ prefix in import modal). Three are test assertion drift (decimal format expectations, column count, missing selector). All 18 must pass for the suite gate to be green.

## What Changes

### Code fixes (production bugs)

- **Stale filter bounds after PATCH** (GROUP 2 — 13 tests): `_initFilterBounds()` runs once in `init()`. After a PATCH mutates `displayAssets`, the `headerRangeFilters` stay at init-time min/max. `_computeFilteredRows` then filters out rows whose values exceed stale bounds. Fix: re-run `_initFilterBounds()` after each successful `commitEdit` and `commitEditTotal`.

- **Double R$ prefix in import modal** (GROUP 4 — 1 test): Template lines 265-266 and 351-352 of `_patrimonio_add_asset_modal.html` render `<td>R$ <span x-text="formatBRL(...)">`. `formatBRL` delegates to `formatMoney` which already includes the `R$` currency symbol. Result: `"R$ R$\xa0NUMBER"`. Fix: remove hardcoded `R$ ` from the `<td>`.

### Test-only fixes

- **F46 decimal format assertions** (GROUP 1 — 2 tests): `formatPctRounded` now uses configurable decimals; templates pass `1`. Tests still assert `"40.00"` and `"20"` instead of `"40.0"` and `"20.0"`.

- **F39 column count** (GROUP 3 — 1 test): `_N_COLS = 19` but F39 removed the "Moeda" column. Template now has 16 `<th>` elements.

- **Missing import_upload_btn selector** (GROUP 5 — 1 test): Upload button replaced with file `<input @change>`. `page.set_input_files()` already handles upload. `page.click(SELECTORS["import_upload_btn"])` fails with KeyError.

## Capabilities

### New Capabilities

None. This is a bugfix/alignment change.

### Modified Capabilities

- `dashboard-inline-editing`: Filter bounds must stay in sync with displayed assets after PATCH mutations. Requirement change: "after any PATCH that mutates `displayAssets`, filter bounds SHALL be recomputed."

## Impact

### Files changed (code fixes)

| File | Change |
|------|--------|
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | (1) Add `this._initFilterBounds()` call at end of `commitEdit` and `commitEditTotal` success handlers. (2) Remove hardcoded `R$ ` prefix from 4 `<td>` lines (265, 266, 351, 352). |

### Files changed (test-only)

| File | Change |
|------|--------|
| `tests/e2e/test_inline_edit.py` | Lines 354, 360: `"40.00"` → `"40.0"`, `"24.00"` → `"24.0"` |
| `tests/e2e/test_asset_table.py` | Line 212: `"20"` → `"20.0"`. Line 489: `_N_COLS = 19` → `_N_COLS = 16` |
| `tests/e2e/test_user_journey_rebalance.py` | Line 102: remove `page.click(SELECTORS["import_upload_btn"], force=True)` |
| `tests/e2e/test_import_modal.py` | Line 222: update regex to allow 1-decimal format if needed (verify after GROUP 4 fix) |

### No impact on

- Database schema or migrations
- API contracts
- Production config
- Other specs beyond `dashboard-inline-editing`
