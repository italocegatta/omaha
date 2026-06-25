## Purpose

Per-profile CSV triplet under `data/seed/`
(`{profile}_classes.csv`, `{profile}_assets.csv`,
`{profile}_positions.csv`) is the source of truth for class targets,
per-asset targets, and current positions. A single script reads the
triplet, validates sums and cross-references, and writes to the DB
in `--mode {reset, upsert, diff}`. Idempotent. Replaces the
hardcoded class list in `scripts/dev_reset.py`.

## Requirements

### Requirement: CSV schema for per-profile class targets

The system SHALL provide, for each seeded profile, a CSV file at
`data/seed/{profile}_classes.csv` with the header
`name,target_pct,display_order,quote_kind`. The file MUST be UTF-8
encoded and MUST contain exactly one header row followed by data
rows. Each data row MUST have a non-empty `name`, a numeric
`target_pct` in the range `[0, 100]`, an integer
`display_order >= 0`, and a `quote_kind` value in
`{auto, manual, none}`. The `name` column MUST be unique within the
file.

#### Scenario: Valid class CSV is accepted

- **WHEN** `data/seed/italo_classes.csv` contains
  `name,target_pct,display_order,quote_kind` header and 6 data rows
  whose `name` values are unique and whose `target_pct` values
  are decimals in `[0, 100]`
- **THEN** the seed script accepts the file and proceeds to the
  per-class sum check

#### Scenario: Missing header is rejected

- **WHEN** `data/seed/italo_classes.csv` does not contain a
  `name,target_pct,display_order,quote_kind` header row
- **THEN** the seed script aborts before any DB write and prints
  the expected header and the offending path

#### Scenario: Duplicate class name is rejected

- **WHEN** `data/seed/italo_classes.csv` contains two rows with the
  same `name`
- **THEN** the seed script aborts and prints the line number of
  the second occurrence

#### Scenario: target_pct out of range is rejected

- **WHEN** any row has `target_pct` outside `[0, 100]`
- **THEN** the seed script aborts and prints the offending line
  number and the value seen

#### Scenario: Invalid quote_kind is rejected

- **WHEN** any row has `quote_kind` not in `{auto, manual, none}`
- **THEN** the seed script aborts and prints the offending line
  number and the value seen

### Requirement: CSV schema for per-profile asset targets

The system SHALL provide, for each seeded profile, a CSV file at
`data/seed/{profile}_assets.csv` with the header
`class_name,name,target_pct,display_order`. The file MUST be
UTF-8 encoded and MUST contain exactly one header row followed by
data rows. Each data row MUST have a non-empty `class_name`, a
non-empty `name`, a numeric `target_pct` in the range `[0, 100]`,
and an integer `display_order >= 0`. The `name` column MUST be
unique within a single class. The `class_name` MUST match (by
exact string equality) a `name` in the corresponding
`{profile}_classes.csv`.

#### Scenario: Valid asset CSV is accepted

- **WHEN** `data/seed/italo_assets.csv` contains the documented
  header and rows whose `class_name` values all appear in
  `data/seed/italo_classes.csv` and whose `name` values are
  unique within each class
- **THEN** the seed script accepts the file and proceeds to the
  sum check

#### Scenario: Asset referencing a missing class is rejected

- **WHEN** `data/seed/italo_assets.csv` contains a row whose
  `class_name` does not appear in `data/seed/italo_classes.csv`
- **THEN** the seed script aborts and prints the offending row's
  line number, the offending `class_name`, and the list of
  classes that DO exist

#### Scenario: Duplicate asset name within a class is rejected

- **WHEN** `data/seed/italo_assets.csv` contains two rows with the
  same `class_name` and the same `name`
- **THEN** the seed script aborts and prints the line number of
  the second occurrence

### Requirement: Per-class and per-asset sum invariant

The seed script MUST validate that `sum(target_pct) == 100` across
the class file (one profile = 100%) AND that
`sum(target_pct) == 100` per class in the asset file. The
validation MUST use the same `validate_target_pct_sum` helper
from `omaha.validators` that the runtime PATCH routes use, so the
"Sobra X%" / "Falta X%" wording is identical. The seed script MUST
abort without writing if either sum is outside the validator's
0.01 tolerance.

#### Scenario: Class sum is 100 → proceeds

- **WHEN** `data/seed/italo_classes.csv` `target_pct` values sum
  to exactly 100 (or within 0.01 of 100)
- **THEN** the seed script proceeds to validate the asset file

#### Scenario: Class sum is not 100 → aborts

- **WHEN** `data/seed/italo_classes.csv` `target_pct` values sum
  to, say, 99
- **THEN** the seed script aborts and prints
  `"Falta 1%"` (using the same wording the inline editor shows)

#### Scenario: Asset sum per class is not 100 → aborts

- **WHEN** the `RF Dinâmica` class has assets whose `target_pct`
  values sum to 90
- **THEN** the seed script aborts and prints
  `"RF Dinâmica: Falta 10%"` with the class name and the
  validator's diagnostic

### Requirement: `reset` mode wipes and re-seeds the profile

When the seed script is invoked with `--mode reset --profile {name}`,
it MUST delete, in order, every `Position` whose `asset` belongs to
a class in the profile, every `ImportPreview` for the profile, every
`Asset` whose class is in the profile, and every `AssetClass` for
the profile. The wipe MUST also delete any orphan `Position` whose
`asset_id` no longer references an existing `Asset` row (so a
prior `scripts.clear_assets` run does not leak orphaned positions
into the freshly-seeded state via SQLite ROWID reuse). After the
wipe, the script MUST insert the classes, then the assets, then
the positions from the CSV in `display_order` ascending order.
Positions MUST be inserted AFTER their asset exists so the
`asset_id` FK resolves. The script MUST commit after the inserts
and MUST print a one-line summary including `classes=N assets=M
positions=K`.

#### Scenario: reset on a fresh profile creates the seeded state

- **WHEN** the profile has no classes, no assets, no positions, no
  previews, and the CSV triplet is valid
- **THEN** `--mode reset` ends with 6 classes, 48 assets, and 47
  positions for Italo (or 6 + 46 + 43 for Ana) — matching the CSV
  triplet exactly

#### Scenario: reset on a populated profile wipes first

- **WHEN** the profile has 5 imported positions, 1 import preview,
  3 assets, and 2 classes
- **THEN** `--mode reset` deletes all 5 positions, the preview,
  the 3 assets, and the 2 classes before re-inserting from the
  CSV triplet (the freshly seeded state has 6 + 48 + 47 for Italo
  regardless of what was there before)

#### Scenario: reset is idempotent

- **WHEN** `--mode reset` is run twice in succession with no CSV
  change
- **THEN** the second run produces the same class/asset counts
  and the same `target_pct` values as the first

### Requirement: `upsert` mode reconciles CSV against DB without deleting

When the seed script is invoked with `--mode upsert --profile {name}`,
it MUST NOT delete any rows. It MUST create classes that don't
exist in the DB (matching by `(profile_id, name)`), update
`target_pct`, `display_order`, and `quote_kind` on classes that
DO exist, and apply the same create-or-update logic to assets
(matched by `(asset_class_id, name)`). The script MUST print a
per-row diff summary (`created` / `updated` / `unchanged` counts)
and MUST still enforce the sum invariant before any write.

#### Scenario: Upsert updates a changed class target

- **WHEN** the DB has `RF Dinâmica target_pct = 26` and the CSV
  says `25`
- **THEN** `--mode upsert` updates the row to `25` and prints
  `"updated: RF Dinâmica 26 → 25"`

#### Scenario: Upsert creates a new asset

- **WHEN** the DB has no asset named `NUCL11` in `Internacional`
  and the CSV lists it
- **THEN** `--mode upsert` creates the row and prints
  `"created: Internacional / NUCL11"`

#### Scenario: Upsert with invalid sum aborts

- **WHEN** the CSV's class sum is 99
- **THEN** `--mode upsert` aborts before any write, regardless
  of the DB's current state

### Requirement: `diff` mode prints the planned changes without writing

When the seed script is invoked with `--mode diff --profile {name}`,
it MUST read the CSV triplet (classes + assets + positions), run
the full validation pipeline, compute the per-row diff against the
current DB state, and print a human-readable report. The report
MUST list `would-create`, `would-update`, and `would-orphan` (rows
in the DB but not in the CSV) sections for each of the three
layers. The script MUST NOT issue any INSERT / UPDATE / DELETE.

#### Scenario: Diff on a fresh DB lists every class, asset, and position

- **WHEN** the profile has no rows
- **THEN** `--mode diff` prints a `would-create` section listing
  every class, every asset, and every position from the CSV
  triplet

#### Scenario: Diff on a populated DB lists only the changes

- **WHEN** the DB already has 5 of 6 classes and 20 of 48 assets
  and 30 of 47 positions matching the CSV exactly
- **THEN** `--mode diff` prints `would-create: 1 class, 28 assets,
  17 positions` and `would-update: 0` and `would-orphan: 0`

#### Scenario: Diff aborts on invalid CSV before printing

- **WHEN** the CSV fails the sum check
- **THEN** `--mode diff` aborts with the same diagnostic as
  `reset` and `upsert`, and prints nothing about DB state

### Requirement: CSV schema for per-profile current positions

The system SHALL provide, for each seeded profile, a CSV file at
`data/seed/{profile}_positions.csv` with the header
`asset_name,qty,avg_price,current_price`. The file MUST be UTF-8
encoded and MUST contain exactly one header row followed by data
rows. Each data row MUST have a non-empty `asset_name` matching
(by exact string equality) a `name` in the corresponding
`{profile}_assets.csv`, a numeric `qty >= 0`, a numeric
`avg_price >= 0`, and a numeric `current_price >= 0`. The
`broker_ticker` for the seeded `Position` row MUST equal
`asset_name` (1:1 mapping; multi-broker is a future change).

#### Scenario: Valid positions CSV is accepted

- **WHEN** `data/seed/italo_positions.csv` contains the documented
  header and rows whose `asset_name` values all appear in
  `data/seed/italo_assets.csv`
- **THEN** the seed script accepts the file and proceeds to the
  cross-reference check

#### Scenario: Position referencing a missing asset is rejected

- **WHEN** `data/seed/italo_positions.csv` contains a row whose
  `asset_name` does not appear in `data/seed/italo_assets.csv`
- **THEN** the seed script aborts and prints the offending row's
  line number, the offending `asset_name`, and the list of assets
  that DO exist

#### Scenario: Negative price or qty is rejected

- **WHEN** any row has `qty < 0` or `avg_price < 0` or
  `current_price < 0`
- **THEN** the seed script aborts and prints the offending line
  number and the value seen

### Requirement: Non-tradeable position convention

For a position whose underlying asset is a non-tradeable
instrument (RDB, CDB, treasury bond held to maturity) the
positions CSV MUST represent the position with `qty = 1`,
`avg_price = total_investido`, and `current_price = total_atual`.
This sentinel is required because the `Position` model declares
`qty` and `avg_price` as NOT NULL and the dashboard computes
`current_value = qty × current_price` and
`invested = qty × avg_price`. With the sentinel, both derivations
yield the broker-truth numbers (`total_atual` and
`total_investido` respectively). The convention is documented in
`data/seed/README.md`.

#### Scenario: Non-tradeable position preserves current_value

- **WHEN** the positions CSV contains a row for
  `RDB Pós 100% CDI 01/08/2033` with
  `qty=1, avg_price=20000.00, current_price=26475.01`
- **THEN** after `--mode reset`, the dashboard's
  `portfolio.current_value` includes the R$ 26.475,01 contribution
  from this position (i.e. the sentinel is rendered correctly, not
  as zero)

#### Scenario: Tradeable position uses raw values

- **WHEN** the positions CSV contains a row for `SMH` with
  `qty=14, avg_price=992.67, current_price=2264.47`
- **THEN** after `--mode reset`, the dashboard's
  `portfolio.current_value` includes
  `14 × 2264.47 = 31.702,58` from this position

### Requirement: `reset` mode also seeds positions

When the seed script is invoked with `--mode reset --profile {name}`,
in addition to the class and asset wipe-and-reseed, it MUST wipe
every `Position` whose `asset` belongs to a class in the profile
(covered by the existing positions-cascade delete from the asset
wipe in `scripts/dev_reset.py:39-62`), then insert one `Position`
row per row in the positions CSV with
`broker_ticker = asset_name`, `qty` / `avg_price` /
`current_price` taken verbatim from the CSV, and `asset_id`
resolved by looking up the asset's `id` from the freshly
inserted assets. The one-line summary MUST include
`positions_created=N`.

#### Scenario: reset seeds the full triplet

- **WHEN** the profile has no rows and the three CSVs are valid
- **THEN** `--mode reset` ends with 6 classes, 48 assets, and 47
  positions for Italo (or 6 + 46 + 43 for Ana)

#### Scenario: reset is idempotent for positions

- **WHEN** `--mode reset` is run twice in succession with no CSV
  change
- **THEN** the second run produces the same position count and
  the same `qty` / `avg_price` / `current_price` values as the
  first

### Requirement: `upsert` and `diff` modes handle positions

`--mode upsert` MUST also handle positions: for each row in the
positions CSV, look up the `asset_id` (by `asset_name` in the
asset CSV, which must already exist) and upsert the
`Position` matched by `(asset_id, broker_ticker)`. The per-row
diff summary MUST include `positions: created=A updated=B
unchanged=C`. `--mode diff` MUST include positions in its
`would-create` / `would-update` / `would-orphan` sections.

#### Scenario: Upsert updates a changed current_price

- **WHEN** the DB has `SMH.current_price = 2000.00` and the CSV
  says `2264.47`
- **THEN** `--mode upsert` updates the row to `2264.47` and
  prints `"updated: SMH current_price 2000.00 → 2264.47"`

#### Scenario: Diff flags orphan positions

- **WHEN** the DB has a position for an asset that's been removed
  from the assets CSV
- **THEN** `--mode diff` prints it under
  `would-orphan: positions`

### Requirement: AGENTS.md permits asset and position seeding only via the CSV path

The `AGENTS.md` "Seed data" rule SHALL be updated to permit
automated creation of `Asset` AND `Position` rows when, and only
when, the source is a CSV file under `data/seed/` consumed by
`scripts/seed_from_csv.py`. The rule MUST still forbid inline
literal / hardcoded asset or position seeds, ad-hoc scripts, and
demo wiring that create assets or positions outside the CSV path.
New profiles or new asset/position schema columns still require a
change proposal.

#### Scenario: New asset or position seed via CSV is allowed

- **WHEN** a developer adds a row to `data/seed/italo_assets.csv`
  and runs `task db-seed-from-csv`
- **THEN** the new asset appears in the DB and the rule permits
  the change because the source is the CSV path
- **AND WHEN** the developer also adds a row to
  `data/seed/italo_positions.csv` referencing the new asset
- **THEN** the new position is also created and the rule permits
  the change for the same reason

#### Scenario: Asset or position seed via hardcoded list is rejected

- **WHEN** a developer adds `Asset(asset_class_id=1, name=...)` or
  `Position(asset_id=1, qty=..., avg_price=..., current_price=...)`
  to `scripts/seed_from_csv.py` as a hardcoded fallback
- **THEN** code review flags the violation per the rule

### Requirement: Taskipy wiring

`pyproject.toml` SHALL provide the following tasks under
`[tool.taskipy.tasks]`:

- `db-seed-from-csv`: `uv run python -m scripts.seed_from_csv
  --profile italo --mode reset` (default; supports override via
  the standard `task db-seed-from-csv -- --profile ana --mode diff`
  pattern).
- `db-seed-diff`: same command with `--mode diff`.
- `db-seed-upsert`: same command with `--mode upsert`.
- `db-reset`: repointed to
  `uv run python -m scripts.seed_from_csv --profile italo
  --mode reset` (preserves the current destructive behaviour for
  backward compat).

#### Scenario: db-reset preserves prior behaviour

- **WHEN** a developer runs `uv run task db-reset` after this
  change
- **THEN** the result is identical to the pre-change behaviour:
  Italo's classes are wiped and reseeded from the CSV with the
  same destructive semantics

#### Scenario: db-seed-diff is non-destructive

- **WHEN** a developer runs `uv run task db-seed-diff`
- **THEN** the script prints a diff and exits with code 0 without
  modifying the DB

### Requirement: Test marker allow-list covers the new test file

`tests/conftest.py` `_INTEGRATION_PREFIXES` SHALL include the
prefix `tests/test_seed_from_csv` so the new integration test
file is assigned the `integration` marker (not `unit`). Without
this prefix, the new file would silently become `unit` and skip
the `omaha_db` fixture setup.

#### Scenario: New test runs as integration

- **WHEN** the developer runs `uv run task test-integration`
- **THEN** the new test file is collected and runs with the
  `omaha_db` fixture (real SQLite session, TestClient available)

### Requirement: Runtime import flow continues to work after the seed

The seed MUST NOT alter the behaviour of the existing
`POST /api/import/commit` endpoint
(`src/omaha/routes/imports.py`). After `--mode reset` has
pre-populated `Position` rows with `broker_ticker = asset_name`,
an upload of a broker CSV that carries the same `asset_name` as
its ticker MUST upsert into the seeded row (matched by
`(asset_id, broker_ticker)`) rather than create a duplicate.
This is guaranteed by the existing
`ON CONFLICT(asset_id, broker_ticker) DO UPDATE SET ...` clause
in the import's upsert SQL
(`src/omaha/routes/imports.py:502-510`); this change does not
modify that SQL or the import flow.

#### Scenario: Import after seed updates the seeded position

- **WHEN** the seed has created a `Position` for
  `SMH` (asset_id=42, broker_ticker="SMH", qty=14,
  current_price=2264.47)
- **AND WHEN** the user uploads a broker CSV containing
  `Código=SMH, Qtd=15, Preço atual=2300.00`
- **THEN** the import's auto-match picks `SMH` (asset_id=42)
- **AND** the upsert updates the existing row to
  qty=15, current_price=2300.00
- **AND** the `Position` table still has exactly ONE row for
  asset_id=42 (no duplicate created)

#### Scenario: Seeded positions have no impact on import matchers

- **WHEN** the seed has pre-populated positions and the user
  uploads a broker CSV
- **THEN** the import's `match_positions` still resolves
  broker tickers against the asset name (not against the
  position); the seeded `Position` rows are passive data
  and do not participate in matching

### Requirement: Position unit prices normalised so dashboard matches broker footer

For each row in `{profile}_positions.csv` corresponding to a
tradeable asset (the row's `qty` is a real number, not `-`), the
seed script MUST normalise the unit prices so
`qty × current_price == total_atual` and
`qty × avg_price == total_investido` exactly:

```
avg_price    = total_investido / qty
current_price = total_atual / qty
```

This compensates for broker data inconsistencies (the broker
CSV's `Preço atual` column sometimes does not multiply back to
the reported `Total atual`) so the dashboard's
`portfolio.current_value` equals the broker's claimed footer total
to within R$ 0.01.

The `Position.qty / avg_price / current_price` columns MUST be
`Numeric(18, 8)` to preserve the precision of the normalised
unit prices (the previous `Numeric(18, 4)` truncated unit prices
and accumulated ~R$ 0.20 of error across 40 tradeable rows for
Italo).

The non-tradeable sentinel rows (both `Qtd` and `Preço médio` are
`-` in the source) keep the original `qty=1, avg=total_investido,
cur=total_atual` representation — no division needed because `qty=1`.

#### Scenario: Italo portfolio.current_value matches the broker footer

- **WHEN** `--mode reset --profile italo` runs against a fresh DB
- **THEN** the dashboard's `portfolio.current_value` for Italo
  equals R$ 1.101.350,86 to within R$ 0.01 (the broker footer
  total for Italo's posicao CSV)

#### Scenario: Ana portfolio.current_value matches the broker footer

- **WHEN** `--mode reset --profile ana` runs against a fresh DB
- **THEN** the dashboard's `portfolio.current_value` for Ana
  equals R$ 684.763,60 to within R$ 0.01 (the broker footer
  total for Ana's posicao CSV)