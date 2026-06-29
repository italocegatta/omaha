## MODIFIED Requirements

### Requirement: CSV schema for per-profile current positions

The system SHALL provide, for each seeded profile, a CSV file at
`data/seed/{profile}_positions.csv` with the header
`asset_name,broker_ticker,qty,avg_price,current_price,
total_invested,total_current` (7 columns). The file
MUST be UTF-8 encoded and MUST contain exactly one header row
followed by data rows. Each data row MUST have:

- a non-empty `asset_name` matching (by exact string equality) a
  `name` in the corresponding `{profile}_assets.csv`,
- a non-empty `broker_ticker` representing the broker-side symbol
  the position was reported under (e.g. `PETR4`, `IVVB11`,
  `TESOURO_SELIC_2029`),
- a numeric `qty >= 0`,
- a numeric `avg_price >= 0`,
- a numeric `current_price >= 0`,
- a numeric `total_invested >= 0` OR an empty cell (parses to
  `NULL` and contributes `0` to the dashboard aggregate),
- a numeric `total_current >= 0` OR an empty cell (parses to
  `NULL` and contributes `0` to the dashboard aggregate).

The pair `(asset_name, broker_ticker)` is the uniqueness key
within the file: no two rows may share the same pair. The
resulting `Position` row's `broker_ticker` column is taken
verbatim from the CSV; `broker_ticker` is independent of
`asset_name` and MAY diverge (e.g. `asset_name="Petrobras PN"`
held via `broker_ticker="PETR4"`). Multi-broker per asset
(distinct positions on the same asset with distinct
`broker_ticker` values) is supported as a side effect of the
unique key.

#### Scenario: Valid positions CSV with broker_ticker = asset_name is accepted

- **WHEN** `data/seed/italo_positions.csv` contains the documented
  7-column header and rows where every `broker_ticker` equals the
  row's `asset_name`
- **THEN** the seed script accepts the file and proceeds to the
  cross-reference check

#### Scenario: Valid positions CSV with divergent broker_ticker is accepted

- **WHEN** `data/seed/italo_positions.csv` contains a row with
  `asset_name="Petrobras PN"` and `broker_ticker="PETR4"`
- **THEN** the seed script accepts the file and inserts a
  `Position` row with `broker_ticker="PETR4"` linked to the
  `Asset` named "Petrobras PN"

#### Scenario: Position referencing a missing asset is rejected

- **WHEN** `data/seed/italo_positions.csv` contains a row whose
  `asset_name` does not appear in `data/seed/italo_assets.csv`
- **THEN** the seed script aborts and prints the offending row's
  line number, the offending `asset_name`, and the list of assets
  that DO exist

#### Scenario: Duplicate (asset_name, broker_ticker) pair is rejected

- **WHEN** `data/seed/italo_positions.csv` contains two rows with
  the same `asset_name` and `broker_ticker`
- **THEN** the seed script aborts and prints the offending line
  numbers; this mirrors the DB-level `(asset_id, broker_ticker)`
  unique constraint

#### Scenario: Empty broker_ticker is rejected

- **WHEN** a positions CSV row has an empty `broker_ticker` cell
- **THEN** the seed script aborts and prints the offending line
  number

#### Scenario: Negative price or qty is rejected

- **WHEN** any row has `qty < 0` or `avg_price < 0` or
  `current_price < 0`
- **THEN** the seed script aborts and prints the offending line
  number and the value seen

### Requirement: `reset` mode also seeds positions

The seed script MUST, when invoked with `--mode reset --profile {name}`,
in addition to the class and asset wipe-and-reseed, wipe every
`Position` whose `asset` belongs to a class in the profile,
then insert one `Position` row per row in the positions CSV.
The resulting `Position` row MUST carry the CSV's `broker_ticker`
cell **verbatim** (not aliased to `asset_name`); the `qty`,
`avg_price`, `current_price`, `total_invested`, and
`total_current` cells MUST likewise be inserted verbatim — the
seed path MUST NOT recompute `total_invested` from `qty * avg_price`
or `total_current` from `qty * current_price` (per the
`broker-csv-import-totals` invariant; those arithmetic paths are
the exact drift source this code eliminates). Empty totals cells
MUST parse to `NULL` and contribute `Decimal('0')` to the dashboard
aggregate. The `asset_id` MUST be resolved by looking up the
asset's `id` from the freshly inserted assets via the row's
`asset_name`. The one-line summary MUST include
`positions_created=N`.

#### Scenario: reset seeds the full triplet with broker_ticker and totals

- **WHEN** the profile has no rows and the three CSVs are valid,
  including a positions CSV with the 7-column header
- **THEN** `--mode reset` ends with 6 classes, 48 assets, and 47
  positions for Italo (or 6 + 46 + 43 for Ana), and every
  position row's `broker_ticker` equals the CSV value, and
  every non-empty `total_invested` / `total_current` cell
  survives verbatim

#### Scenario: reset is idempotent for positions

- **WHEN** `--mode reset` is run twice in succession with no CSV
  change
- **THEN** the second run produces the same position count and
  the same `qty` / `avg_price` / `current_price` /
  `broker_ticker` / `total_invested` / `total_current` values
  as the first

### Requirement: `upsert` and `diff` modes handle positions

The seed script MUST, when invoked with `--mode upsert`, handle
positions by looking up `asset_id` (via `asset_name` in the asset
CSV, which MUST already exist) and upserting the `Position`
matched by the `(asset_id, broker_ticker)` pair. When the CSV
row's `total_invested` / `total_current` cells are non-empty, the
upsert MUST take them verbatim; when empty (`NULL`), the upsert
MUST leave the existing row's value untouched (the CSV does not
carry an opinion, so the upsert must not overwrite). The per-row
diff summary MUST include `positions: created=A updated=B
unchanged=C` and identify each row by `asset_name=<name>
broker_ticker=<ticker>`. `--mode diff` MUST include positions in
its `would-create` / `would-update` / `would-orphan` sections,
identified by the same pair, and MUST flag any drift between the
CSV's totals cells and the DB's stored values as `would-update`
(so the operator can see when a broker CSV import brought new
totals).

#### Scenario: Upsert updates a changed current_price

- **WHEN** the DB has `SMH.current_price = 2000.00` and the CSV
  has `SMH` with `current_price = 2100.00`
- **THEN** `--mode upsert` updates the existing row's
  `current_price` to `2100.00` and prints
  `positions: updated=1 unchanged=N-1`

#### Scenario: Diff reports broker_ticker in position identifier

- **WHEN** the DB has a position with `broker_ticker="PETR4"`
  and the CSV row has `broker_ticker="PETR4A"` (typo, same
  asset)
- **THEN** `--mode diff` prints both rows under
  `would-update` and `would-create`, each prefixed with
  `asset_name=<name> broker_ticker=<old>` /
  `asset_name=<name> broker_ticker=<new>`

## ADDED Requirements

### Requirement: db-snapshot task exports live DB state to CSVs

The system SHALL provide a taskipy task `db-snapshot` that runs
`uv run python -m scripts.snapshot_to_csv` and exports the live
DB state of `AssetClass`, `Asset`, and `Position` rows for every
canonical profile (`italo`, `ana`) into the six CSV files under
`data/seed/`. The task is a dev tool only — it is not wired into
the FastAPI app, not exposed via the UI, and not packaged for the
prod image. The exported CSV header MUST exactly match the
header consumed by `seed_from_csv.py`, so the round-trip
`snapshot → reset` is deterministic.

#### Scenario: Snapshot writes all six CSVs

- **WHEN** the dev DB has the canonical Italo + Ana state from
  `task db-reset`
- **THEN** `task db-snapshot` writes `italo_classes.csv`,
  `italo_assets.csv`, `italo_positions.csv`, `ana_classes.csv`,
  `ana_assets.csv`, `ana_positions.csv` to `data/seed/` with one
  header row each and exits 0

#### Scenario: Snapshot output round-trips through reset

- **WHEN** the dev DB has the canonical state, an operator
  manually edits one `AssetClass.target_pct` via SQL, then runs
  `task db-snapshot` followed by `task db-reset`
- **THEN** the post-reset DB has the manually edited value
  restored (snapshot captured the change; reset wrote it back)
  and every other column in the four affected tables matches the
  pre-edit state

#### Scenario: Snapshot rejects unknown profile

- **WHEN** the dev DB contains a `Profile` row with a name
  outside the canonical set `{"italo", "ana"}`
- **THEN** `task db-snapshot` aborts with exit code 1, prints
  `<name> not in canonical set` to stderr, and writes no CSV
  files

#### Scenario: Snapshot rejects missing canonical profile

- **WHEN** the dev DB is missing one of the canonical profiles
  (e.g. Ana was wiped)
- **THEN** `task db-snapshot` aborts with exit code 1, prints
  `profile "<name>" missing from DB` to stderr, and writes no
  CSV files

#### Scenario: Snapshot is idempotent

- **WHEN** `task db-snapshot` is run twice in succession with no
  intervening DB writes
- **THEN** the two runs produce byte-equal output for all six
  CSVs

#### Scenario: Snapshot preserves broker_ticker divergence

- **WHEN** a `Position` row in the DB has
  `broker_ticker="PETR4"` against an `Asset` named "Petrobras PN"
- **THEN** after `task db-snapshot`, the row in
  `data/seed/italo_positions.csv` has
  `asset_name="Petrobras PN"` and `broker_ticker="PETR4"`

### Requirement: Positions CSV carries broker-published totals verbatim

The positions CSV MUST extend its header from
`asset_name,broker_ticker,qty,avg_price,current_price` (5 columns)
to `asset_name,broker_ticker,qty,avg_price,current_price,
total_invested,total_current` (7 columns). The two trailing
columns are the broker-published per-row totals; they are
inserted **verbatim** into `Position.total_invested` /
`Position.total_current` and exported **verbatim** by
`snapshot_to_csv.py` — the seed and snapshot paths MUST NOT
fall back to ``qty * price``. An empty CSV cell parses to
`NULL` and contributes `Decimal('0')` to the dashboard
aggregate (per `routes/pages.py`); a non-empty cell must parse
as a decimal `>= 0`.

#### Scenario: Verbatim totals survive snapshot → reset → snapshot

- **WHEN** a `Position` row has
  `qty=14, avg_price=992.67, current_price=2264.47`
  with `total_invested=99999.9999, total_current=88888.8888`
  (values that DO NOT equal `qty * price`)
- **THEN** after `task db-snapshot` followed by `task db-reset`
  the resulting `Position` row carries `total_invested=99999.9999`
  and `total_current=88888.8888` unchanged

#### Scenario: Empty totals cells parse to NULL

- **WHEN** a positions CSV row has empty cells for both
  `total_invested` and `total_current`
- **THEN** after `task db-reset` the resulting `Position` row has
  `total_invested=None` and `total_current=None`, contributing
  `Decimal('0')` to the dashboard aggregate

#### Scenario: Reset never recomputes totals from qty * price

- **WHEN** the seed script inserts positions from the CSV
- **THEN** `Position.total_invested` MUST equal the CSV cell's
  value (verbatim, or `NULL` if empty), never `qty * avg_price`;
  same for `total_current` vs `qty * current_price`
