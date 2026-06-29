## Why

`data/seed/{profile}_*.csv` is the source of truth for `AssetClass`,
`Asset`, and `Position` rows per the AGENTS.md "Seed data" rule and
the `data-driven-seed` capability spec. The CSVs are edited by hand
and the dev DB is reset via `task db-reset` to apply them.

Two practical frictions as the DB schema evolves:

1. **Hand-editing the CSV triplet is lossy and stale.** Every new
   column on `Position` (`total_invested`, `total_current`,
   `broker_ticker`), on `Asset` (`buy_enabled`, `sell_enabled`,
   `currency_code`), or on `AssetClass` (`quote_kind`) had to be
   back-propagated by hand to the CSVs in `data/seed/`. When the
   dev DB drifts ahead of the CSVs (e.g. the user adds a position
   via the import flow, then tweaks its `current_price` in the UI),
   there is no easy way to "freeze" the live state back into the
   CSV so the next `db-reset` reproduces it.

2. **Re-populating the wallet from a clean DB takes a full session.**
   The user wipes the DB to test a migration or a UI change, then
   has to re-import the broker CSV and re-check every class /
   asset / position to get back to the same dashboard state. The
   hand-edited CSV triplet is the closest thing to a snapshot, but
   it is not authoritative — it can drift from the live DB.

`scripts/backup.py` is a binary SQLite dump for prod disaster
recovery, not a dev workflow tool. The CSV triplet is the
authoritative source for the dev DB, but there is no path that
goes **DB → CSV** in the current codebase.

This change adds a single-purpose dev tool that exports the live
state of `AssetClass`, `Asset`, and `Position` rows for **every
profile in the canonical set** into the six CSV files under
`data/seed/`. The output is the same shape `seed_from_csv.py`
already consumes, so `task db-snapshot && task db-reset` is a
deterministic round-trip.

## What Changes

- **NEW `scripts/snapshot_to_csv.py`**: reads the dev DB, iterates
  over the canonical profile set (`italo`, `ana`), and writes
  `data/seed/{profile}_classes.csv`, `{profile}_assets.csv`, and
  `{profile}_positions.csv`. Idempotent (re-running overwrites
  the same files with the same content). **Internal dev tool** —
  not part of the runtime, not exposed via the UI, not wired into
  the prod stack. Fails fast with `exit 1` if a profile outside
  the canonical set exists in the DB (operator-visible signal that
  a stray test profile was left behind).
- **MODIFIED `scripts/seed_from_csv.py`**: the positions CSV
  pipeline gains a `broker_ticker` column. Header becomes
  `asset_name,broker_ticker,qty,avg_price,current_price`. The
  loader parses the column, the `PositionRow` dataclass carries
  it, `reset` / `upsert` insert it verbatim, and the
  cross-reference check is keyed by `(asset_name, broker_ticker)`
  pair (not just `asset_name`). Existing CSVs in `data/seed/`
  without the column fail the header check until updated —
  matches the current "header change is a hard fail" rule from
  the `data-driven-seed` spec.
- **NEW taskipy task `db-snapshot`**: runs the script for both
  profiles in one invocation. Output is a one-line summary
  (`italo: 6 classes, 48 assets, 47 positions → 3 files written`)
  per profile, plus a final aggregate. Added to the
  `[tool.taskipy.tasks]` table in `pyproject.toml` and documented
  in the project's root `README.md` Development tasks table
  (next to `db-reset`, alphabetical placement per existing
  convention).
- **NEW `tests/test_snapshot_to_csv.py`** (integration): round-trip
  test (`snapshot → reset → snapshot` produces identical DB state),
  unknown-profile error path, `broker_ticker` preserved verbatim,
  `display_order` preserved, idempotent re-run produces byte-equal
  CSVs.
- **MODIFIED `tests/conftest.py`**: add `tests/test_snapshot_to_csv`
  to `_INTEGRATION_PREFIXES` (per the AGENTS.md "Test marker rule").
- **MODIFIED `openspec/specs/data-driven-seed/spec.md`** (delta):
  positions CSV header changes from 4 columns to 5; `broker_ticker`
  is now a first-class column with its own requirement and
  scenarios. The `(asset_name, broker_ticker)` pair becomes the
  cross-reference key.
- **MODIFIED `data/seed/README.md`**: document the new positions
  header, the `broker_ticker` field semantics, and the new
  `task db-snapshot` workflow at the bottom of the edit workflow
  section.

## Capabilities

### New Capabilities

*(none — the export is a pure dev tool, not a runtime capability)*

### Modified Capabilities

- `data-driven-seed`: positions CSV gains a `broker_ticker` column
  AND two trailing totals columns (`total_invested`,
  `total_current`). The `(asset_name, broker_ticker)` pair becomes
  the cross-reference key, and the `broker_ticker` value is
  inserted verbatim into the `Position` row instead of being
  aliased to `asset_name`. The two totals columns are the
  broker-published per-row totals — they are written verbatim by
  `snapshot_to_csv.py` and read verbatim by `seed_from_csv.py`,
  closing the round-trip for the
  `broker-csv-import-totals` invariant: totals are never
  recomputed from `qty * price`.

## Impact

- **Affected code:**
  - `scripts/snapshot_to_csv.py` (new; ~120 lines)
  - `scripts/seed_from_csv.py` (positions pipeline: header,
    dataclass, parser, validator, inserter)
  - `pyproject.toml` (1 new taskipy task: `db-snapshot`)
  - `tests/conftest.py` (`_INTEGRATION_PREFIXES` extended)
  - `data/seed/README.md` (header doc + workflow doc)
  - `README.md` (root project README — taskipy table entry for
    `db-snapshot` in the Development tasks table, plus a new
    "Snapshot the wallet state" workflow paragraph in the
    Testing the app section that pairs with `db-reset`)
  - `openspec/specs/data-driven-seed/spec.md` (delta: header
    change, `broker_ticker` requirement, scenarios)
- **Affected data:**
  - `data/seed/italo_positions.csv` — header gains
    `broker_ticker` column. Today every `broker_ticker` equals
    `asset_name`, so the column is populated with `asset_name`
    verbatim. No semantic change to existing rows.
  - `data/seed/ana_positions.csv` — same as above.
  - All 6 CSVs are **overwritten in place** when `task db-snapshot`
    runs. The user's prior edits to the CSVs are discarded (this
    is the intentional behavior: the CSV is now a snapshot of the
    DB, not a hand-edited source). The change request explicitly
    opts for "overwrite direto, sem backup" — operator-visible
    via `git status` showing the diff.
- **Affected developers:** after this change, the dev loop becomes
  `task db-reset → fiddle in the UI → task db-snapshot → git diff
  data/seed/ → git commit`. Any time the user wants to "freeze"
  the current wallet state — before a destructive migration test,
  before a UI rework, or just to checkpoint progress — they run
  one command and commit the resulting CSV diff. The root
  `README.md` Development tasks table gains a `db-snapshot` row
  (next to `db-reset`) so the new command is discoverable from
  the project landing page; the Testing the app section gains a
  one-paragraph "Snapshot the wallet state" subsection that shows
  the snapshot → diff → commit flow.
- **Affected runtime:** none. The export is dev-DB only. The
  prod DB is untouched; prod-backup (`scripts/backup.py` +
  `task backup`) keeps its current scope (binary SQLite snapshot
  via the prod stack's `backup` service).
- **Affected tests:** 1 new integration test file. No existing
  test should regress — the `seed_from_csv.py` change is a header
  shape change with the same data semantics (existing rows have
  `broker_ticker == asset_name`, so a CSV with the new column
  populated from `asset_name` produces an identical DB).
- **Migration for existing dev DBs:** none. Running
  `task db-snapshot` once after pulling this change regenerates
  the position CSVs with the new column.
- **Out of scope (explicit non-goals):**
  - **Restore / freeze / promote subcommands.** The user explicitly
    asked for a single "DB → CSV" command, no separate restore
    flow. `task db-reset` is the existing restore path and stays
    unchanged.
  - **JSON snapshot format.** CSV aligns with the existing
    `seed_from_csv.py` pipeline; no new file format is introduced.
  - **Snapshotting the production DB.** Dev-only.
  - **Snapshotting `User`, `Quote`, `ImportPreview`, or audit
    tables.** Out of scope — the request was classes, assets,
    target allocation, and (decided in clarification) positions.
  - **Auto-snapshot on schema migration.** The user runs the
    command explicitly; no Alembic hook.
  - **Per-profile selective snapshot.** The script always runs
    over the full canonical profile set (`italo`, `ana`) — matches
    the symmetry of `scripts.reset_both_profiles.py`.
