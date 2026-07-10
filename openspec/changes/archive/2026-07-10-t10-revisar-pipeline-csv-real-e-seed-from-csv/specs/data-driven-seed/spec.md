## MODIFIED Requirements

### Requirement: CSV schema for per-profile asset targets

The system SHALL provide, for each seeded profile, a CSV file at
`data/seed/{profile}_assets.csv` with the header
`class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code`.
The file MUST be UTF-8 encoded and MUST contain exactly one header row
followed by data rows. Each data row MUST have a non-empty
`class_name`, a non-empty `name`, a numeric `target_pct` in the range
`[0, 100]`, an integer `display_order >= 0`, booleans for
`buy_enabled` / `sell_enabled` (permissive `true/false/1/0/yes/no`,
empty => `false`), and a `currency_code` in `{BRL, USD}`. The `name`
column MUST be unique within a single class. The `class_name` MUST
match (by exact string equality) a `name` in the corresponding
`{profile}_classes.csv`.

#### Scenario: Valid asset CSV is accepted

- **WHEN** `data/seed/italo_assets.csv` contains documented 7-column
  header and rows whose `class_name` values all appear in
  `data/seed/italo_classes.csv`
- **THEN** the seed script accepts the file and proceeds to the sum
  check

#### Scenario: Legacy 4-column asset header is rejected

- **WHEN** an asset CSV contains legacy header
  `class_name,name,target_pct,display_order`
- **THEN** the seed script aborts before any DB write and prints the
  expected 7-column header and offending path

### Requirement: `reset` mode wipes and re-seeds the profile

The seed script MUST, when invoked with `--mode reset --profile {name}`,
delete in order every `Position` whose `asset` belongs to a class in the
profile, every `ImportPreview` for the profile, every `Asset` whose
class is in the profile, and every `AssetClass` for the profile. The
wipe MUST also delete orphan `Position` rows whose `asset_id` no longer
references an existing `Asset`. After the wipe, the script MUST insert
the classes, then the assets, then the positions from the CSV in
documented order. Positions MUST be inserted after their asset exists so
the `asset_id` FK resolves. The script MUST commit after the inserts and
MUST print a one-line summary including created class / asset / position
counts.

#### Scenario: reset on a fresh profile creates seeded state

- **WHEN** the profile has no classes, no assets, no positions, no
  previews, and the CSV triplet is valid
- **THEN** `--mode reset` ends with 6 classes, 47 assets, and 47
  positions for Italo (or 6 classes, 52 assets, and 52 positions for
  Ana) — matching the current CSV triplet exactly

#### Scenario: reset on a populated profile wipes first

- **WHEN** the profile already has imported previews, assets, classes,
  or positions
- **THEN** `--mode reset` deletes them before re-inserting the current
  CSV triplet for that profile

### Requirement: Non-tradeable position convention

Canonical positions CSVs MAY represent non-tradeable instruments (RDB,
CDB, treasury bond held to maturity, similar placeholders) with zeroed
unit fields plus explicit broker-published totals:

- `qty = 0`
- `avg_price = 0`
- `current_price = 0`
- `total_invested = <broker truth>`
- `total_current = <broker truth>`

The seed path MUST store those five fields verbatim. Dashboard
aggregates MUST use `total_invested` / `total_current` when present, so
portfolio totals preserve broker truth without any qty-based sentinel.

#### Scenario: Non-tradeable position preserves current_value via explicit totals

- **WHEN** the positions CSV contains row
  `RDB Pós 100% CDI 01/08/2033` with
  `qty=0, avg_price=0, current_price=0,
  total_invested=20000.0000, total_current=27212.2000`
- **THEN** after `--mode reset`, stored `Position` row keeps those CSV
  values verbatim
- **AND** dashboard aggregate includes R$ 27.212,20 from
  `Position.total_current`

### Requirement: Taskipy wiring

`pyproject.toml` SHALL provide following tasks under
`[tool.taskipy.tasks]`:

- `db-seed-from-csv`: `uv run python -m scripts.seed_from_csv --profile italo --mode reset`
  (single-profile destructive reset; supports override via
  `task db-seed-from-csv -- --profile ana --mode reset|diff|upsert`).
- `db-seed-diff`: same command with `--mode diff`.
- `db-seed-upsert`: same command with `--mode upsert`.
- `db-reset`: `uv run python -m scripts.reset_both_profiles`
  (destructive reseed of both canonical profiles in one invocation).

#### Scenario: db-reset seeds both profiles

- **WHEN** a developer runs `uv run task db-reset`
- **THEN** both Italo and Ana are wiped/reseeded from their canonical
  CSV triplets in one invocation

#### Scenario: db-seed-from-csv remains single-profile override entrypoint

- **WHEN** a developer runs `uv run task db-seed-from-csv -- --profile ana --mode diff`
- **THEN** only Ana's CSV triplet is read and no DB write occurs

### Requirement: Position unit prices stay verbatim and aggregates rely on explicit totals

The seed script MUST store `qty`, `avg_price`, and `current_price`
exactly as they appear in `{profile}_positions.csv`. It MUST NOT
normalise unit prices to force `qty * current_price == total_current` or
`qty * avg_price == total_invested`. Broker footer parity comes from the
explicit `total_invested` / `total_current` columns, which are stored
verbatim and used by dashboard aggregates.

#### Scenario: Tradeable row keeps raw unit price while totals stay verbatim

- **WHEN** `SMH` row carries `qty=14`, `current_price=3066.33000000`,
  and `total_current=42928.5800`
- **THEN** `--mode reset` stores both values verbatim
- **AND** dashboard aggregate uses `42928.5800` from explicit totals,
  not recomputed `14 × 3066.33 = 42928.62`
