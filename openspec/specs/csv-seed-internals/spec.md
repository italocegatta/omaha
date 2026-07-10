# csv-seed-internals

## Purpose

The CSV-driven seed path (`scripts/seed_from_csv/` package,
invoked via `python -m scripts.seed_from_csv`) is the only
sanctioned way to create `AssetClass`, `Asset`, and `Position` rows
(PRD §4.3; cross-references `data-driven-seed` and `seeded-state`).
This capability describes the **internal module layout** of the
seed script — the file-level organisation that keeps parsing,
validation, profile resolution, and the three mode implementations
in separate, discoverable units.

The CSV schema, validation rules, abort messages, exit codes, and
operator-facing CLI are pinned by `data-driven-seed` and stay
unchanged by this capability.

## Requirements

### Requirement: Seed script is organised as a Python package

The seed script SHALL be organised as a Python package at
`scripts/seed_from_csv/` rather than a single `.py` file. The
package SHALL expose the same public API as the pre-refactor single
file so external consumers (`scripts/snapshot_to_csv.py`,
`scripts/reset_both_profiles.py`, `tests/test_seed_from_csv.py`,
`tests/scripts/test_reset_both_profiles.py`) continue to import
without change.

#### Scenario: Module resolves via `python -m scripts.seed_from_csv`

- **WHEN** an operator runs
  `uv run python -m scripts.seed_from_csv --profile italo --mode reset`
- **THEN** Python resolves the entry point against
  `scripts/seed_from_csv/__main__.py` and the CLI runs to completion
  with the same exit code, abort messages, and summary output as the
  pre-refactor single-file build

#### Scenario: External consumer imports stay green

- **WHEN** `scripts/snapshot_to_csv.py` runs
  `from scripts.seed_from_csv import abort`
- **THEN** Python resolves `abort` from
  `scripts/seed_from_csv/__init__.py` (re-export) and the import
  succeeds without the calling module changing

#### Scenario: Re-export surface is complete

- **WHEN** any of the following names are imported via
  `from scripts.seed_from_csv import <name>`
- **THEN** the import resolves to a symbol exposed by
  `__init__.py` without the calling module changing:
  `abort`, `PROFILES`, `PROFILE_OWNER_TO_NAME`, `REPO_ROOT`,
  `SEED_DIR`, `CLASS_HEADER`, `ASSET_HEADER`, `POSITION_HEADER`,
  `VALID_QUOTE_KINDS`, `VALID_CURRENCY_CODES`, `ClassRow`,
  `AssetRow`, `PositionRow`, `load_classes`, `load_assets`,
  `load_positions`, `validate`, `get_profile_id`, `run_reset`,
  `run_upsert`, `run_diff`

### Requirement: One module per concern

The package SHALL split responsibilities into one module per concern,
following the section headers present in the pre-refactor single file:

- `scripts/seed_from_csv/loaders.py` — row dataclasses, the
  `_read_csv` reader, the row-parsing helpers (`_decimal`,
  `_optional_decimal`, `_int`, `_bool`), and the three
  `load_classes` / `load_assets` / `load_positions` functions.
- `scripts/seed_from_csv/validation.py` — the `validate()`
  function (cross-references + sum invariants).
- `scripts/seed_from_csv/profiles.py` — `PROFILES`,
  `PROFILE_OWNER_TO_NAME`, and `get_profile_id` (profile
  resolution).
- `scripts/seed_from_csv/modes.py` — `_wipe_profile`,
  `run_reset`, `run_upsert`, `run_diff` (the three mode
  implementations).
- `scripts/seed_from_csv/__main__.py` — `parse_args` and `main`
  (the CLI driver that makes `python -m` resolve).

#### Scenario: Each module exposes a single concern

- **WHEN** a future contributor adds a new CSV column to the
  triplet
- **THEN** the contributor edits exactly one of `loaders.py`
  (parser), `validation.py` (rule), `modes.py` (DB write), or
  `__init__.py` (header re-export) — the per-concern split makes
  the affected file obvious from the section header

#### Scenario: Internal imports stay acyclic

- **WHEN** `modes.py` needs `load_classes` or `get_profile_id`
- **THEN** it imports via `from scripts.seed_from_csv.loaders
  import load_classes` and
  `from scripts.seed_from_csv.profiles import get_profile_id`,
  not through `__init__.py`, so the dependency graph stays
  acyclic

### Requirement: Leading-underscore helpers stay private

`scripts/seed_from_csv/__init__.py` SHALL NOT re-export any symbol
whose name starts with an underscore. The internal helpers
(readers, parsers, the wipe helper) remain importable via their
owning module but are not part of the package's public surface.

#### Scenario: Underscore-prefixed names absent from `__init__.py`

- **WHEN** a contributor reads `scripts/seed_from_csv/__init__.py`
- **THEN** the file does not list any symbol whose name starts
  with `_` (other than `__all__` if present)

### Requirement: Dead F01-fixture narrative is removed

`scripts/seed_from_csv/profiles.py` MUST NOT mention the retired
F01 fixture `italo_rf2`. The Família sentinel lives in `seed.py`
(not the CSV path) and is referenced only by a brief comment that
names the current invariant.

#### Scenario: Comment does not mention F01 or the retired fixture

- **WHEN** a contributor reads `scripts/seed_from_csv/profiles.py`
- **THEN** the file does not contain the strings `italo_rf2`,
  `Italo RF2`, or `F01 fixture`

### Requirement: Per-layer unit tests exist

The package SHALL have focused unit tests for the loader and
validator layers:

- `tests/test_seed_from_csv_loaders.py` — covers the three
  `load_*` functions and the row-parsing helpers. Uses `tmp_path`
  + inline CSV strings + `monkeypatch` on
  `scripts.seed_from_csv.SEED_DIR`.
- `tests/test_seed_from_csv_validation.py` — covers `validate()`
  and its abort messages over pre-built row lists.

Both files SHALL be listed in `_UNIT_FILES` in `tests/conftest.py`
so they pick up the `unit` marker without triggering the
`UnknownTestPath` warning.

#### Scenario: Loader tests cover valid + invalid CSV inputs

- **WHEN** `task test-unit` runs after the refactor lands
- **THEN** `tests/test_seed_from_csv_loaders.py` passes with at
  least one assertion per `load_*` function covering: a valid
  CSV (parses to expected row count), a missing header
  (SystemExit code 1), an out-of-range `target_pct` (SystemExit
  code 1), an unknown `quote_kind` (SystemExit code 1), a
  duplicate `name` (SystemExit code 1), and a non-ASCII asset
  name (round-trip)

#### Scenario: Validation tests cover abort paths

- **WHEN** `task test-unit` runs after the refactor lands
- **THEN** `tests/test_seed_from_csv_validation.py` passes with
  at least one assertion per cross-reference rule: asset
  referencing a missing class (aborts with line number), position
  referencing a missing asset (aborts with line number), class
  sum violation (`Falta X%` / `Sobra X%`), per-class asset sum
  violation (`<class>: Falta X%`)
