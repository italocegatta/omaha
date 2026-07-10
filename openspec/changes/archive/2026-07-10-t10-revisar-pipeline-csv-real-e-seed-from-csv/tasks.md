## 1. Audit `scripts/seed_from_csv/` package against `csv-seed-internals` spec

- [x] 1.1 Verify module layout matches spec: `loaders.py`, `validation.py`, `profiles.py`, `modes.py`, `__main__.py`, `__init__.py` — all present. Flag if any module is missing or extra.
- [x] 1.2 Verify `__init__.py` re-export surface matches `csv-seed-internals` spec's explicit list (58 symbols). Flag any missing or extra re-export.
- [x] 1.3 Verify underscore-prefixed names are NOT re-exported from `__init__.py` (per `csv-seed-internals` "Leading-underscore helpers stay private" requirement).
- [x] 1.4 Verify `profiles.py` does NOT mention `italo_rf2`, `Italo RF2`, or `F01 fixture` (per `csv-seed-internals` "Dead F01-fixture narrative is removed" requirement).
- [x] 1.5 Verify internal imports are acyclic: `modes.py` imports from `loaders.py` and `profiles.py` directly, not through `__init__.py` (per spec scenario).
- [x] 1.6 Verify per-layer unit tests exist at `tests/test_seed_from_csv_loaders.py` and `tests/test_seed_from_csv_validation.py` and both test files are in `tests/conftest.py` `_UNIT_FILES`.

## 2. Audit `data/seed/` CSV triplet + README against `data-driven-seed` spec

- [x] 2.1 Verify `italo_classes.csv` header matches spec: `name,target_pct,display_order,quote_kind`. Verify `italo_assets.csv` header matches spec: `class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code`. Verify `italo_positions.csv` header matches spec: `asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current`. Repeat for ana profiles.
- [x] 2.2 Verify `data/seed/README.md` validation rules (1-9) match `data-driven-seed` spec requirements exactly. Flag any divergence between README rule and spec requirement.
- [x] 2.3 Spot-check 3-5 rows per CSV: verify `target_pct` values are in `[0, 100]`, `qty >= 0`, `currency_code` in `{BRL, USD}`, `quote_kind` in `{auto, manual, none}`. Note any violations.
- [x] 2.4 Verify non-tradeable position convention documented in README (`qty=0, avg=0, cur=0` + explicit totals) matches actual rows in `italo_positions.csv`. Spot-check CSV rows against spec scenario for `RDB Pós 100% CDI 01/08/2033`.
- [x] 2.5 Verify `data/seed/fixtures/` directory: currently empty. Document its purpose in a comment or recommend explicit removal. If kept, add a `.gitkeep` or README note explaining intent.

## 3. Audit `test_real_csv_flow.py` fixtures/assertions against `seeded-state` spec

- [x] 3.1 Verify `_seed_assets()` and `_expected_class_by_ticker()` helper logic matches current `data/seed/italo_*` CSV content. Spot-check 5 mappings.
- [x] 3.2 Verify `_ASSIGNMENTS` list (5 unmatched rows) matches current `_unmatched_tickers()` output from `load_positions`. If CSV changed since test was written, update `_ASSIGNMENTS`.
- [x] 3.3 Verify `TestPortfolioTotalsFromCsv` assertions match `seeded-state` spec's portfolio totals scenario for Italo. Check portfolio footer values still align.
- [x] 3.4 Verify the `_clean_data` fixture wipes all 4 tables (`Position`, `Asset`, `AssetClass`, `ImportPreview`) — confirm no test leaves stale DB state.

## 4. Audit `test_seed_from_csv.py` constants and paths

- [x] 4.1 Check `SEED_FROM_CSV` constant (line 57): currently `.../seed_from_csv.py` but package is `.../seed_from_csv/`. Determine if constant is used anywhere. If unused, document as dead. If used, update path to correct package directory.
- [x] 4.2 Verify `_run_seed` subprocess invocation uses `python -m scripts.seed_from_csv` (correct) and the monkeypatch/env setup is correct.
- [x] 4.3 Verify all 20 test cases in this file still match their docstring descriptions. If a test was removed or added, update docstring.

## 5. Run full CSV test suite and log results

- [x] 5.1 Run `uv run task test-file tests/test_real_csv_flow.py` — record pass/fail and runtime.
- [x] 5.2 Run `uv run task test-file tests/test_seed_from_csv.py` — record pass/fail and runtime.
- [x] 5.3 Run `uv run task test-file tests/test_seed_from_csv_loaders.py tests/test_seed_from_csv_validation.py` — record pass/fail and runtime.
- [x] 5.4 Document any non-determinism or fixture brittleness observed across runs.

## 6. Apply minority-side fixes for discovered drift

- [x] 6.1 For each drift item found in tasks 1-4: classify whether spec is wrong or code/CSV/README is wrong. Fix the minority side (fewer lines changed).
- [x] 6.2 If `data/seed/README.md` is updated, regenerate or verify the change is editorial only.
- [x] 6.3 If spec comment corrected, create delta spec file at `specs/<spec-name>/spec.md` per OpenSpec workflow.
- [x] 6.4 Verify all tests still pass after fixes.

## 7. Register gap log for deferred items

- [x] 7.1 Compile a gap log of any drift found but not fixed (e.g., test weakness that requires a follow-up slice, spec requirement that was never implemented, CSV data that diverges from spec constraint).
- [x] 7.2 If gap log is non-empty, recommend follow-up slice(s) in the gap log.

## Audit notes

- Package audit: module layout, direct internal imports, re-export surface, underscore privacy, and unit-test allow-list all matched live implementation.
- CSV audit: headers matched live files for both profiles; spot-checks found no out-of-range `target_pct`, negative qty/price, invalid `currency_code`, or invalid `quote_kind`.
- Drift fixed on minority side:
  - `data-driven-seed` delta spec added for current 7-column asset header, current Italo/Ana row counts, two-profile `db-reset` wiring, explicit-totals non-tradeable convention, and verbatim unit-price storage.
  - `data/seed/README.md` updated to match live contract and to document `data/seed/fixtures/` purpose.
  - `tests/test_seed_from_csv.py` stale `SEED_FROM_CSV` constant removed; stale test-count / sentinel / retired-F01 comments corrected.
  - `tests/test_real_csv_flow.py` stale "real broker extract" / footer-parity narrative corrected to describe current seed-fixture coverage.

## Verification log

- `uv run task test-file tests/test_real_csv_flow.py` → 18 passed in 4.31s pytest time (`real 7.35s`).
- `uv run task test-file tests/test_seed_from_csv.py` → 20 passed in 32.25s pytest time (`real 35.77s`).
- `uv run task test-file tests/test_seed_from_csv_loaders.py tests/test_seed_from_csv_validation.py` → 28 passed in 0.79s pytest time (`real 3.63s`).
- Non-determinism: none observed across single focused runs.
- Fixture brittleness: `tests/test_seed_from_csv.py` mutates canonical CSV files in place and restores backups; safe in serial, poor candidate for parallel execution.

## Gap log / follow-up

- `tests/test_real_csv_flow.py` currently uploads `data/seed/italo_positions.csv`, not a raw broker export fixture. Import-path totals coverage therefore documents current zero-total behavior instead of true broker-footer parity.
- Follow-up recommendation: dedicated slice to audit `src/omaha/csv_import.py` + `/api/import/preview|commit` totals propagation against a real broker-export fixture, outside T10 scope.
