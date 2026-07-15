## Why

`test_seed_from_csv.py` has 20 integration tests, all `xdist_group("serial")`. Each test invokes the `omaha_db` fixture which runs `run_alembic_and_seed` — two subprocess calls (`alembic upgrade head` + `python -m omaha.seed`) that take ~2.5s per test. Total overhead: ~50s for setup alone.

Three problems compound the cost:

1. **No snapshot reuse.** Every test runs the full migration + seed from scratch even though most tests start from the same canonical DB state.
2. **Loader tests pay for a DB they don't use.** Tests 14–17 (`test_auto_class_fixture_loads_with_quote_kind`, `test_loader_rejects_unknown_quote_kind`, `test_legacy_four_column_asset_header_is_rejected`, `test_invalid_currency_in_assets_csv_aborts`) only parse CSV via `tmp_path` + `monkeypatch`. They never touch `omaha_db["SessionLocal"]` but still trigger the full fixture.
3. **CSV-mutating tests stomp shared files.** Tests 6–8, 18 modify `data/seed/*.csv` in-place. They already have try/finally backup/restore but the fixture overhead is identical to read-only tests.

## What Changes

- **Snapshot-based fixture.** Session-scoped `_seed_db_snapshot` runs `run_alembic_and_seed` once, saves the SQLite file path. Per-test `omaha_db` copies the snapshot instead of re-running migration + seed. Per-test cost drops from ~2.5s to ~10ms (file copy).
- **Loader tests drop `omaha_db`.** Tests 14–17 remove the fixture dependency. They only need `tmp_path` and `monkeypatch` (already available). This eliminates 4 unnecessary fixture setups.
- **Test grouping by mutation type.** Tests categorized into three groups:
  - **Share snapshot** (8 tests): reset-only, no mutation — `test_reset_creates_full_italo_state`, `test_reset_is_idempotent`, `test_reset_preserves_divergent_broker_ticker`, `test_reset_preserves_totals_verbatim_no_recompute`, `test_reset_null_total_cells_contribute_zero`, `test_non_tradeable_position_explicit_totals_preserve_value`, `test_non_ascii_asset_name_round_trips`, `test_run_reset_populates_trade_fields_from_csv`
  - **Own copy** (8 tests): mutate DB or CSV — `test_reset_wipes_existing_state_first`, `test_upsert_updates_changes_creates_missing`, `test_diff_lists_changes_no_write`, `test_sum_violating_class_csv_is_rejected`, `test_asset_referencing_missing_class_is_rejected`, `test_position_referencing_missing_asset_is_rejected`, `test_upsert_rejects_sum_violation_before_write`, `test_run_diff_emits_would_update_for_trade_changes`
  - **No fixture** (4 tests): loader-only — tests 14–17

## Capabilities

### Modified Capabilities
- `csv-seed-internals`: Test infrastructure change only. The spec's "Per-layer unit tests exist" requirement is unaffected — test count and assertions stay identical.

## Impact

- **Files modified**: `tests/test_seed_from_csv.py`, `tests/support/db.py`
- **Files unchanged**: `tests/conftest.py`, `scripts/seed_from_csv/*`, `data/seed/*`
- **No behavior change**: all 20 tests keep same assertions, same coverage, same serial execution
- **No spec change**: test optimization is infra-only, no capability contract changes
- **Expected speedup**: ~45s → ~5s total (2.5s × 20 → 2.5s × 1 + ~10ms × 19 + 0s × 4)
