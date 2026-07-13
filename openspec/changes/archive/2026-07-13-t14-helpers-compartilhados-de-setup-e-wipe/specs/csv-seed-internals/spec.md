# csv-seed-internals

## MODIFIED Requirements

### Requirement: One module per concern

The package SHALL split responsibilities into one module per concern, following the section headers present in the pre-refactor single file:

- `scripts/seed_from_csv/loaders.py` — row dataclasses, the `_read_csv` reader, the row-parsing helpers (`_decimal`, `_optional_decimal`, `_int`, `_bool`), and the three `load_classes` / `load_assets` / `load_positions` functions.
- `scripts/seed_from_csv/validation.py` — the `validate()` function (cross-references + sum invariants).
- `scripts/seed_from_csv/profiles.py` — `PROFILES`, `PROFILE_OWNER_TO_NAME`, and `get_profile_id` (profile resolution).
- `scripts/seed_from_csv/wipe.py` — shared destructive wipe primitives for positions, assets, asset_classes, import_previews, and orphan cleanup, reusable by seed modes and test harness support.
- `scripts/seed_from_csv/modes.py` — `run_reset`, `run_upsert`, `run_diff`, and the thin orchestration that composes wipe primitives.
- `scripts/seed_from_csv/__main__.py` — `parse_args` and `main` (the CLI driver that makes `python -m` resolve).

#### Scenario: Each module exposes a single concern

- **WHEN** a future contributor changes wipe semantics
- **THEN** they edit `wipe.py` once
- **AND** `modes.py` imports that helper instead of duplicating SQL
- **AND** external entrypoint behavior stays unchanged
