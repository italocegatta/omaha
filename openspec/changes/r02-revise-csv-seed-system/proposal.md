## Why

`scripts/seed_from_csv.py` is now 1010 lines in a single file, mixing
CSV parsing, dataclass definitions, cross-reference validation, three
mode implementations (`reset` / `upsert` / `diff`), profile resolution,
and the CLI driver. The script accreted over several slices
(`broker-csv-import-totals`, `asset-trade-flags`, F07 sentinel cleanup)
and is now harder to navigate than the contract it implements. Every
new column on the CSV triplet — a likely next-step as F03 (rentabilidade)
and the per-profile cash feature come online — means editing a file
that already mixes parser, validator, and three full DB-writers. A
small refactor restores the readability that the next maintainer needs
without changing what the script does.

## What Changes

- Split `scripts/seed_from_csv.py` (1010 lines, six responsibilities)
  into a small Python package with one module per concern:
  loader / dataclasses, validator, profile resolution, mode
  implementations (`reset`, `upsert`, `diff`), and the CLI driver.
  Module boundaries follow the existing section headers in the file
  (`# --- CSV row dataclasses ---`, `# --- CSV loaders ---`,
  `# --- Validation pipeline ---`, `# --- Profile resolution ---`,
  `# --- Modes ---`, `# --- Driver ---`).
- Preserve the CLI surface verbatim: same flags, same exit codes, same
  `abort()` messages on the validation paths (the contracts those
  messages implement are pinned by `data-driven-seed` scenarios). The
  `uv run python -m scripts.seed_from_csv --profile X --mode Y`
  invocation works without change.
- Drop dead history: the `PROFILE_OWNER_TO_NAME` block carries a
  stale comment about the F01 fixture `italo_rf2` that was retired by
  F07. The fixture rows are gone; the comment is noise.
- Add focused unit tests for the loader and validator modules. Today
  the script is only covered through the taskipy task wrappers
  (`db-seed-diff`, `db-seed-upsert`, `db-reset`) — there is no
  per-layer regression harness for the parsing rules.
- Update `data/seed/README.md` to reflect the new module layout. The
  "Edit workflow" section stays byte-identical (operators do not care
  which file `seed_from_csv.py` lives in).

## Capabilities

### New Capabilities

_None._ This change is a pure refactor. The CSV schema, validation
rules, mode semantics, and operator-facing CLI are all preserved.

### Modified Capabilities

_None._ The contract pinned by `openspec/specs/data-driven-seed/` is
preserved byte-for-byte. No requirement changes; no delta spec.

## Impact

- `scripts/seed_from_csv.py` (1010 lines) → `scripts/seed_from_csv/`
  package with one file per concern. The old module path keeps a
  thin re-export shim so `python -m scripts.seed_from_csv` and
  `from scripts.seed_from_csv import …` keep working — exact layout
  decided in `design.md`.
- `data/seed/README.md` (small edit: the "Edit workflow" section
  gains one line on the new module layout; nothing operator-facing).
- `tests/test_seed_from_csv_loader.py` (new, unit) — covers the three
  `load_*` functions and the row-parsing helpers (`_decimal`,
  `_optional_decimal`, `_int`, `_bool`).
- `tests/test_seed_from_csv_validate.py` (new, unit) — covers the
  `validate()` function and the abort messages it produces.
- `pyproject.toml` — no change. `scripts/` is already on `sys.path`
  via the existing `python -m` invocations; switching from
  `scripts/seed_from_csv.py` to `scripts/seed_from_csv/__main__.py`
  does not require a packaging edit.
- Taskipy tasks (`db-seed-from-csv`, `db-seed-diff`, `db-seed-upsert`)
  — no change. The task definitions call
  `python -m scripts.seed_from_csv -- …`, which resolves against
  either the module file or the package `__main__.py` identically.
- Test conftest prefix list (`tests/conftest.py`) — both new test
  files start with `test_seed_from_csv_*` which already matches the
  unit-test prefix `test_seed_from_csv_` pattern that `conftest.py`
  routes through `task test-unit`. No conftest edit required.
- No DB schema change. No Alembic migration. No runtime behavior
  change observable from the dashboard, rebalance engine, or any
  route.