## Why

CSV pipeline (`scripts/seed_from_csv/` + `src/omaha/csv_import.py` + `data/seed/` CSVs) is the single source of truth for asset classes, assets, and positions (PRD §4.3). Two test files (`test_real_csv_flow.py`, `test_seed_from_csv.py`) exercise this pipeline end-to-end. Current checkout: both suites pass (38 tests, ~35s). However, no recent audit has verified that the specs (`data-driven-seed`, `csv-seed-internals`, `seeded-state`) accurately reflect the running contract, or that the seed CSVs haven't drifted from documented invariants. This slice audits the full pipeline, identifies any spec/code/CSV drift, corrects the minority side, and registers fixture gaps.

## What Changes

- Audit `scripts/seed_from_csv/` package source against `csv-seed-internals` spec (module layout, re-export surface, per-concern split).
- Audit `data/seed/` CSV triplet + `data/seed/README.md` against `data-driven-seed` spec (header schema, validation rules, sum invariants, position totals contract, non-tradeable sentinel).
- Audit `test_real_csv_flow.py` fixtures and assertions against `seeded-state` spec and `broker-csv-import-totals` invariants.
- Verify `data/seed/fixtures/` directory (currently empty) — document its intended purpose or remove if dead.
- Verify `test_seed_from_csv.py`'s `SEED_FROM_CSV` path constant points at old single-file name (`scripts/seed_from_csv.py`) when the package is now `scripts/seed_from_csv/` — fix if the constant is stale.
- Run full CSV test suite, capture any non-determinism or fixture brittleness.
- Document all drift findings in `tasks.md`; fix the minority side (code or spec); leave a clear gap log for deferred work.

## Capabilities

### New Capabilities

None — audit-only slice. No spec-level behavior changes introduced.

### Modified Capabilities

None — if contract drift is found between spec and implementation, the minority side (typically a spec comment or a missing test assertion) is corrected. No requirement semantics change.

## Impact

- `scripts/seed_from_csv/` — source reading only; no logic changes expected unless drift is found.
- `data/seed/*.csv` — read-only unless CSV content has drifted from spec.
- `data/seed/README.md` — possible doc update if spec/README mismatch found.
- `tests/test_real_csv_flow.py` — minor assertion or fixture tweak if contract drift surfaces.
- `tests/test_seed_from_csv.py` — minor assertion or constant fix if drift surfaces.
- `openspec/specs/data-driven-seed/spec.md` — possible comment-level correction.
- `openspec/specs/csv-seed-internals/spec.md` — possible comment-level correction.
- `openspec/specs/seeded-state/spec.md` — possible comment-level correction.
