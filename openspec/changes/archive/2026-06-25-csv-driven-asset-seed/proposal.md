## Why

`scripts/dev_reset.py` (which is the only "seed" path that populates
`AssetClass` rows for the Italo profile) hardcodes a 6-class list with
`target_pct` values that **diverged from the canonical reference** in
`~/github/investing/input/setup_italo.xlsx` — three of six class targets
are off by 1–5 pp (RF Dinâmica 26→25, RF Pós 16→20, Internacional 21→18)
and the per-asset allocation (47 assets) is not seeded at all, forcing
the user to populate the editor by hand. Both divergences are silent
(no test guards the contract) and the source of truth is a binary
spreadsheet that the user wants to edit as text in the future.

The same problem exists for **positions**: the broker CSVs in
`~/github/investing/input/posicao_{italo,ana}.csv` carry the current
`qty` / `avg_price` / `current_price` for 47 / 43 holdings, and the
runtime import flow is the only path that creates `Position` rows. The
user's end-state is to log into each profile and see the dashboard
fully populated — classes with target bars, assets with target_pct,
and the per-asset current position rendered against the broker truth.

This change moves the source of truth for **classes, assets, and
positions** to CSV files under `data/seed/`, generates the initial
files from the xlsx + posicao references for both Italo and Ana, and
replaces the hardcoded reset with a single CSV-driven seed script
that validates and writes idempotently.

## What Changes

- **NEW `data/seed/italo_classes.csv` and `data/seed/italo_assets.csv`**:
  per-profile class targets and per-asset targets (within class). 6
  classes, 47 assets, source values taken from the `categoria` and
  `ativo` sheets of `setup_italo.xlsx`.
- **NEW `data/seed/ana_classes.csv` and `data/seed/ana_assets.csv`**:
  same shape, 6 classes + 46 assets, source from `setup_ana.xlsx`.
- **NEW `data/seed/italo_positions.csv` and `data/seed/ana_positions.csv`**:
  per-profile current positions. Italo: 48 rows (47 tradeable + 7
  non-tradeable RDB/CDB with `qty=1` sentinel). Ana: 43 rows.
  Source values from `posicao_italo.csv` and `posicao_ana.csv`
  (European number format → CSV-decimal format conversion done in
  the apply phase; the broker CSVs are not a runtime dependency
  after this change is merged).
- **NEW `scripts/seed_from_csv.py`**: reads a `{profile}_classes.csv` +
  `{profile}_assets.csv` + `{profile}_positions.csv` triplet, validates
  `sum(class.target_pct) == 100` and `sum(asset.target_pct) per class == 100`
  (reusing `omaha.validators.validate_target_pct_sum`), cross-references
  positions against the assets file, and writes classes + assets +
  positions idempotently. Supports `--mode {reset,upsert,diff}` with
  `--profile {italo,ana}`. `--mode reset` (default) wipes
  `positions` / `import_previews` / `assets` / `asset_classes` for the
  profile (same destructive behavior as the current `dev_reset.py`),
  then re-seeds all three layers from the CSV.
- **NEW `tests/test_seed_from_csv.py`** (integration): happy-path reset
  with positions, upsert preserves unrelated rows, sum-violating CSV is
  rejected, asset referencing a missing class is rejected, position
  referencing a missing asset is rejected, non-tradeable position
  preservation, idempotency (running reset twice yields the same DB
  state including positions).
- **NEW taskipy tasks:** `db-seed-from-csv` (reset, default), `db-seed-diff`,
  `db-seed-upsert`.
- **MODIFIED `scripts/dev_reset.py`**: deleted. Replaced by
  `scripts/seed_from_csv.py --mode reset --profile italo`. The `db-reset`
  task in `pyproject.toml` repoints to the new entry point.
- **MODIFIED `AGENTS.md`**: relax the "Seed data — classes only, never
  assets" rule to permit asset AND position seeding **via the CSV-driven
  path exclusively** (no parallel inline/hardcoded asset or position
  seeds).
- **MODIFIED `tests/conftest.py`**: add the new test file prefix to
  `_INTEGRATION_PREFIXES` so it gets the `integration` marker (DB +
  TestClient).
- **MODIFIED `openspec/config.yaml`**: add project context (CSV-driven
  seed location, PT-BR UI, SQLite, AGENTS.md rule references) so future
  agents have the right framing.

## Capabilities

### New Capabilities

- `data-driven-seed`: per-profile CSV triplet under `data/seed/`
  (`{profile}_classes.csv`, `{profile}_assets.csv`,
  `{profile}_positions.csv`) is the source of truth for class targets,
  per-asset targets, and current positions. A single script reads the
  triplet, validates sums and cross-references, and writes to the DB
  in `--mode {reset, upsert, diff}`. Idempotent. Replaces the
  hardcoded `CLASS_SPECS` in `scripts/dev_reset.py`.

### Modified Capabilities

*(none — no existing spec covers seeding; this is a new capability
with no overlap with the dashboard / import / alert specs)*

## Impact

- **Affected code:**
  - `scripts/dev_reset.py` (deleted)
  - `scripts/seed_from_csv.py` (new; reads 3 CSVs, writes 3 layers)
  - `pyproject.toml` (3 new taskipy tasks; `db-reset` repointed)
  - `AGENTS.md` (rule update for asset + position seeding)
  - `openspec/config.yaml` (project context block populated)
  - `tests/conftest.py` (`_INTEGRATION_PREFIXES` extended)
- **Affected data:**
  - `data/seed/italo_classes.csv` (new, 6 rows + header; values
    hand-derived from the `categoria` sheet of
    `~/github/investing/input/setup_italo.xlsx` during the apply
    phase; the xlsx is not accessed by the application or any
    runtime script after this change is merged)
  - `data/seed/italo_assets.csv` (new, 47 rows + header; same
    source — `ativo` sheet of the xlsx)
  - `data/seed/ana_classes.csv` (new, 6 rows + header; from
    `setup_ana.xlsx`)
  - `data/seed/ana_assets.csv` (new, 46 rows + header; from
    `setup_ana.xlsx`)
  - `data/seed/italo_positions.csv` (new, 48 rows + header;
    hand-derived from `posicao_italo.csv` during the apply phase;
    European number format and "Minha Categoria" column are
    dropped on the floor — only `qty` / `avg_price` / `current_price`
    per asset are kept; the broker CSV is not a runtime dependency)
  - `data/seed/ana_positions.csv` (new, 43 rows + header; from
    `posicao_ana.csv`)
  - `data/seed/README.md` (new; schema for all three CSV types,
    validation rules, edit workflow, non-tradeable convention)
- **Affected developers:** after this change, running `task db-reset`
  gives Italo's dashboard the full state — 6 classes at the canonical
  targets (25 / 20 / 18 / 15 / 8 / 14), 47 assets with per-class
  `target_pct`, and 48 positions (47 tradeable + 7 non-tradeable
  with the `qty=1` sentinel). Same for Ana (6 classes at 25 / 29 /
  20 / 15 / 0.1 / 10.9, 46 assets, 43 positions). The `db-clear-assets`
  task still works for the "wipe assets only" use case.
- **Affected runtime:** the seed is dev-DB only (mirrors current
  `dev_reset.py` scope). Production DB is untouched. `--mode reset` is
  destructive (wipes positions + previews + assets + classes) — the
  taskipy wrapper does not change the destructive default.
- **Affected tests:** adds 1 new integration test file; no existing
  test should regress.
- **Migration:** none for users. Existing dev DBs need `task db-reset`
  to pick up the new class targets AND the seeded positions;
  otherwise the old `dev_reset.py` hardcoded values stay.
- **Out of scope (explicit non-goals):**
  - Seed for the production DB. Dev-only path, same as today.
  - Adding `currency` / `fl_comprar` / `fl_vender` / `nm_arca` columns
    to the `Asset` model — xlsx has them, model doesn't, this change
    drops them on the floor. A separate change can extend the schema.
  - Auto-running seed on app startup. The seed remains a deliberate,
    taskipy-triggered op.
  - Multi-broker per asset (the seed produces one `Position` per
    asset with `broker_ticker = asset_name`). The import flow still
    exists for cases where the user wants to track the same asset
    across brokers.
