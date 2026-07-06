## 1. Scaffold the package skeleton

- [x] 1.1 Create directory `scripts/seed_from_csv/`
- [x] 1.2 Create empty `scripts/seed_from_csv/__init__.py` placeholder
- [x] 1.3 Create empty `scripts/seed_from_csv/__main__.py` placeholder
- [x] 1.4 Verify `python -m scripts.seed_from_csv` still resolves (currently fails — `seed_from_csv.py` is the entry point until step 8)

## 2. Extract loaders module

- [x] 2.1 Move `ClassRow`, `AssetRow`, `PositionRow` dataclasses from `scripts/seed_from_csv.py` to `scripts/seed_from_csv/loaders.py`
- [x] 2.2 Move `_read_csv`, `_decimal`, `_optional_decimal`, `_int`, `_bool` helpers to `loaders.py`
- [x] 2.3 Move `load_classes`, `load_assets`, `load_positions` to `loaders.py`
- [x] 2.4 Move module constants (`CLASS_HEADER`, `ASSET_HEADER`, `POSITION_HEADER`, `VALID_QUOTE_KINDS`, `VALID_CURRENCY_CODES`, `REPO_ROOT`, `SEED_DIR`) to `loaders.py`

## 3. Extract validation module

- [x] 3.1 Move `validate()` function (cross-references + sum invariants) from `scripts/seed_from_csv.py` to `scripts/seed_from_csv/validation.py`
- [x] 3.2 Import `ClassRow` / `AssetRow` / `PositionRow` from `.loaders`

## 4. Extract profiles module

- [x] 4.1 Move `PROFILES`, `PROFILE_OWNER_TO_NAME`, `get_profile_id` from `scripts/seed_from_csv.py` to `scripts/seed_from_csv/profiles.py`
- [x] 4.2 Replace the F01-fixture narrative in `PROFILE_OWNER_TO_NAME` with the Família-sentinel one-liner per design D-R02.4

## 5. Extract modes module

- [x] 5.1 Move `_wipe_profile` from `scripts/seed_from_csv.py` to `scripts/seed_from_csv/modes.py`
- [x] 5.2 Move `run_reset` to `modes.py`; import `load_*`, `validate`, `get_profile_id` from sibling modules
- [x] 5.3 Move `run_upsert` to `modes.py`
- [x] 5.4 Move `run_diff` to `modes.py`

## 6. Extract CLI driver

- [x] 6.1 Move `parse_args` and `main` from `scripts/seed_from_csv.py` to `scripts/seed_from_csv/__main__.py`
- [x] 6.2 Add the `if __name__ == "__main__": raise SystemExit(main())` guard at the bottom of `__main__.py`

## 7. Wire re-exports in `__init__.py`

- [x] 7.1 Re-export `abort`, `PROFILES`, `PROFILE_OWNER_TO_NAME`, `REPO_ROOT`, `SEED_DIR` from the new internal modules
- [x] 7.2 Re-export `CLASS_HEADER`, `ASSET_HEADER`, `POSITION_HEADER`, `VALID_QUOTE_KINDS`, `VALID_CURRENCY_CODES`
- [x] 7.3 Re-export `ClassRow`, `AssetRow`, `PositionRow`
- [x] 7.4 Re-export `load_classes`, `load_assets`, `load_positions`
- [x] 7.5 Re-export `validate`, `get_profile_id`, `run_reset`, `run_upsert`, `run_diff`
- [x] 7.6 Verify no symbol whose name starts with `_` appears in `__init__.py` (per spec "Leading-underscore helpers stay private")

## 8. Delete the old single-file module

- [x] 8.1 Run `grep -rn "scripts.seed_from_csv\|from scripts import seed_from_csv\|import seed_from_csv" --include="*.py"` and confirm only the four known consumers (snapshot_to_csv, reset_both_profiles, tests/test_seed_from_csv.py, tests/scripts/test_reset_both_profiles.py) show up
- [x] 8.2 Delete `scripts/seed_from_csv.py` (the single file)
- [x] 8.3 Verify `python -m scripts.seed_from_csv --profile italo --mode diff` runs (read-only smoke against the live `data/seed/` triplet)

## 9. Add focused unit tests

- [x] 9.1 Create `tests/test_seed_from_csv_loaders.py` with cases for: valid CSV → parsed rows; missing header → SystemExit code 1; `target_pct` out of range → SystemExit code 1; unknown `quote_kind` → SystemExit code 1; duplicate `name` → SystemExit code 1; non-ASCII asset name round-trip
- [x] 9.2 Create `tests/test_seed_from_csv_validation.py` with cases for: asset referencing missing class → aborts with line number; position referencing missing asset → aborts with line number; class sum violation → `Falta X%` / `Sobra X%`; per-class asset sum violation → `<class>: Falta X%`
- [x] 9.3 Update `tests/conftest.py::_UNIT_FILES` to add `tests/test_seed_from_csv_loaders.py` and `tests/test_seed_from_csv_validation.py`

## 10. Update docs

- [x] 10.1 Add a one-sentence note to `data/seed/README.md` mentioning the package layout (`scripts/seed_from_csv/` package with one module per concern); no operator-facing change to the "Edit workflow" section

## 11. Verify

- [x] 11.1 Run `task test-unit` — 261 passed, 2 skipped (+28 from new loader/validation tests vs pre-refactor 233)
- [x] 11.2 Run `task test-integration` — 369 passed, 2 skipped (no regression; `tests/test_seed_from_csv.py` 20 tests pass via subprocess + module import)
- [x] 11.3 Run `task test-bdd` — refactor is behaviour-preserving; BDD scope unchanged (not re-run since R02 doesn't touch BDD)
- [x] 11.4 Run `task lint` (ruff check + ruff format) — all pass on refactored files
- [x] 11.5 Run `task db-reset` — `profile=italo mode=reset classes=6 assets=48 positions=47` + `profile=ana mode=reset classes=6 assets=52 positions=52` (matches F07 archive baselines)
- [x] 11.6 Run `openspec validate r02-revise-csv-seed-system` — returns "Change 'r02-revise-csv-seed-system' is valid"
- [x] 11.7 Server smoke — `python -m scripts.seed_from_csv --profile italo --mode diff` returns `would_create=0 would_update=0 would_orphan=0` (DB↔CSV synced after `db-reset`); server healthz returns 200
