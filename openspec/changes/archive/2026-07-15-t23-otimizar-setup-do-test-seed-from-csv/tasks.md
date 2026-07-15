## 1. Add snapshot fixture to test_seed_from_csv.py

- [x] 1.1 Add `import shutil` to imports
- [x] 1.2 Add session-scoped `_seed_db_snapshot` fixture that calls `run_alembic_and_seed` once and returns the SQLite file path
- [x] 1.3 Refactor `omaha_db` to accept `_seed_db_snapshot`, copy snapshot to `tmp_path` via `shutil.copy2`, keep module save/restore/reimport logic

## 2. Remove omaha_db from loader-only tests

- [x] 2.1 `test_auto_class_fixture_loads_with_quote_kind`: remove `omaha_db` parameter
- [x] 2.2 `test_loader_rejects_unknown_quote_kind`: remove `omaha_db` parameter
- [x] 2.3 `test_legacy_four_column_asset_header_is_rejected`: remove `omaha_db` parameter
- [x] 2.4 `test_invalid_currency_in_assets_csv_aborts`: remove `omaha_db` parameter

## 3. Verify all 20 tests pass

- [x] 3.1 Run `pytest tests/test_seed_from_csv.py -v` — all 20 pass (13.5s, down from ~50s)
- [x] 3.2 Verify serial execution preserved (`xdist_group("serial")` marker still active)
- [x] 3.3 Verify timing improvement: ~13.5s total (session snapshot ~2.5s once + per-test copy ~10ms × 16 + subprocess calls)
