# asset-trade-flags Specification

## Purpose

Define per-asset trade-control attributes that the CVXPY-based
rebalance solver (Fase 2+ do plano `.planning/REBALANCE_PLAN.md`)
uses as hard locks, plus the per-asset currency code that resolves
which quote source backs the asset's price.

These attributes also drive the dashboard's inline toggle UI
(per-asset, one-at-a-time) and the import preview modal's defaults
(since broker CSV uploads do not carry this metadata).

## Requirements

### Requirement: Asset carries buy/sell/currency attributes

The system SHALL store on each `Asset` row three trade-control
attributes in addition to the existing columns
(`id`, `asset_class_id`, `name`, `target_pct`, `display_order`,
`created_at`):

- `buy_enabled: Boolean` — whether the rebalance solver is
  authorized to issue buy orders against this asset.
- `sell_enabled: Boolean` — whether the rebalance solver is
  authorized to issue sell orders against this asset.
- `currency_code: String(8)` — the currency in which the asset
  is quoted, restricted to the allowlist `{"BRL", "USD"}` by a
  database CHECK constraint.

All three columns SHALL be `NOT NULL` with `server_default` so
existing rows backfill cleanly on migration without a data
migration step.

#### Scenario: New asset has the trade-control columns

- **WHEN** an asset row is inserted without explicitly providing
  `buy_enabled`, `sell_enabled`, or `currency_code`
- **THEN** the persisted row reads `buy_enabled=True`,
  `sell_enabled=True`, `currency_code="BRL"`

#### Scenario: Backfill after migration

- **WHEN** Alembic `upgrade head` runs against a database with
  pre-existing asset rows
- **THEN** every existing row reads
  `buy_enabled=True, sell_enabled=True, currency_code="BRL"`
  after the migration completes

### Requirement: Currency code is restricted to BRL or USD

The system SHALL enforce via a CHECK constraint that
`assets.currency_code` is one of the values `BRL` or `USD`. No
other value SHALL be accepted at the database layer.

#### Scenario: Reject non-allowlist currency

- **WHEN** code attempts to insert or update an asset row with
  `currency_code = "EUR"`
- **THEN** the database raises `IntegrityError`

#### Scenario: Migration adds the CHECK constraint

- **WHEN** Alembic `upgrade head` runs against an existing
  database
- **THEN** the `assets` table has a CHECK constraint named
  `ck_asset_currency_code` enforcing `currency_code IN ('BRL',
  'USD')`

### Requirement: Asset defaults favor opt-out over opt-in

The system SHALL default `buy_enabled`, `sell_enabled`, and
`currency_code` to values that minimize friction on first use.
Specifically: `buy_enabled=True`, `sell_enabled=True`,
`currency_code="BRL"`. The user may opt-out of any individual
flag via the dashboard's inline toggle or the import preview.

This inverts the originally proposed conservative default (all
`False`) per owner decision 2026-06-26 — operational friction
of clicking 96 toggles across 48 assets before the first
rebalance was deemed unacceptable.

#### Scenario: First-time seed yields all-liberated assets

- **WHEN** `task db-reset` runs against a fresh database
- **THEN** every asset in Italo's profile and Ana's profile
  reads `buy_enabled=True, sell_enabled=True,
  currency_code="BRL"` regardless of whether the asset is
  tradeable (FII, Ações) or hold-to-maturity (RDB, CDB,
  Tesouro)

### Requirement: PATCH /api/assets/{id} accepts trade-control fields

The system SHALL extend `PATCH /api/assets/{id}` to accept a
JSON body containing any subset of the four fields
`target_pct`, `buy_enabled`, `sell_enabled`, `currency_code`.
Each field is validated independently when present; absent
fields are no-ops. A body that is missing all four fields is
rejected with HTTP 422.

#### Scenario: PATCH buy_enabled alone

- **WHEN** an authenticated user PATCHes
  `{"buy_enabled": false}` against an asset in the active
  profile
- **THEN** the asset's `buy_enabled` is updated to `false`,
  `target_pct` / `sell_enabled` / `currency_code` are
  unchanged, and the response is 200

#### Scenario: PATCH multiple fields at once

- **WHEN** an authenticated user PATCHes
  `{"target_pct": "50", "buy_enabled": false,
  "currency_code": "USD"}`
- **THEN** all three fields are persisted atomically and the
  response is 200

#### Scenario: PATCH rejects non-allowlist currency

- **WHEN** an authenticated user PATCHes
  `{"currency_code": "EUR"}`
- **THEN** the response is 422 with a `detail` message naming
  the invalid currency

#### Scenario: PATCH rejects empty body

- **WHEN** an authenticated user PATCHes an empty JSON object
- **THEN** the response is 422 with a `detail` message
  indicating at least one field must be supplied

### Requirement: POST /api/assets accepts trade-control fields

The system SHALL extend `POST /api/assets` to accept
optional `buy_enabled`, `sell_enabled`, and `currency_code`
fields in the JSON body. When omitted, the new asset inherits
the project-wide defaults (`True`, `True`, `"BRL"`).

#### Scenario: POST with all defaults omitted

- **WHEN** an authenticated user POSTs
  `{"name": "PETR4", "asset_class_id": 7}` without trade-
  control fields
- **THEN** the asset is created with `buy_enabled=True`,
  `sell_enabled=True`, `currency_code="BRL"`

#### Scenario: POST with explicit currency

- **WHEN** an authenticated user POSTs
  `{"name": "AAPL", "asset_class_id": 3, "currency_code":
  "USD"}`
- **THEN** the asset is created with `currency_code="USD"`
  and the other trade-control fields at their default values

### Requirement: Import preview carries trade-control fields

The system SHALL include `buy_enabled`, `sell_enabled`, and
`currency_code` in every row of the import preview response
(`/api/import/preview`) for both auto-matched rows (existing
asset) and unmatched rows (new asset to be created).

For auto-matched rows the value SHALL equal the asset's
current `buy_enabled`/`sell_enabled`/`currency_code` (so a
re-import preserves the user's prior toggle choices). For
unmatched rows the value SHALL equal the project defaults
`True`, `True`, `"BRL"`.

The user SHALL be able to override these values in the
preview modal before committing the import.

#### Scenario: Preview exposes current asset toggle state

- **WHEN** a user uploads a broker CSV that includes an
  asset they previously toggled to `sell_enabled=false`
- **THEN** the preview row for that asset shows
  `sell_enabled=false`, and the user may re-enable it before
  commit

#### Scenario: Preview suggests defaults for unmatched assets

- **WHEN** a user uploads a broker CSV that introduces a new
  asset not in the database
- **THEN** the preview row for that asset shows
  `buy_enabled=true, sell_enabled=true, currency_code="BRL"`
  as starting values

### Requirement: Import commit persists trade-control fields

The system SHALL persist `buy_enabled`, `sell_enabled`, and
`currency_code` from the commit request body when committing
an import. Auto-matched rows update the existing asset's
trade-control fields. Unmatched rows create the new asset
with the supplied trade-control fields. A
`currency_code` outside `{"BRL", "USD"}` is rejected with
HTTP 422.

#### Scenario: Commit updates existing asset's flags

- **WHEN** a user commits an import with
  `buy_enabled=false` for an auto-matched asset
- **THEN** the asset's `buy_enabled` is updated to `false` in
  the database

#### Scenario: Commit creates new asset with chosen flags

- **WHEN** a user commits an import with a new asset and
  `currency_code="USD"` selected in the preview
- **THEN** the new asset is created with
  `currency_code="USD"` and the supplied buy/sell flags

#### Scenario: Commit rejects invalid currency

- **WHEN** a user commits an import with `currency_code="EUR"`
- **THEN** the response is 422 and no asset is created or
  updated

### Requirement: Dashboard renders inline per-asset trade-control toggles

The system SHALL render, for each asset row in the dashboard's
asset table, inline toggle controls for `buy_enabled` and
`sell_enabled`, and a visible badge (or column) for
`currency_code`. Clicking a toggle SHALL send a
`PATCH /api/assets/{id}` with the changed field and update
the row's visual state on a 200 response. The toggle SHALL be
disabled while the PATCH is in flight.

This is per-asset only — there is no bulk toggle at the
asset-class level. The dashboard does not provide a class-
level mechanism for setting or clearing trade-control flags
across multiple assets in one action.

#### Scenario: Toggle buy_enabled inline

- **WHEN** a user clicks the buy-enabled toggle on asset row
  for PETR4
- **THEN** the dashboard sends
  `PATCH /api/assets/{id} {"buy_enabled": <new-value>}`
  and updates the toggle's visual state to reflect the new
  value on a 200 response

#### Scenario: Currency badge is visible per asset

- **WHEN** the dashboard renders the asset table
- **THEN** each asset row shows a visible currency indicator
  matching the asset's `currency_code` value

#### Scenario: Toggle buy and sell are independent

- **WHEN** a user clicks the sell-enabled toggle on asset row
  for PETR4
- **THEN** only the sell-enabled toggle disables during the
  in-flight PATCH; the buy-enabled toggle stays clickable
  and does not flicker

### Requirement: CSV seed header is extended with trade-control columns

The system SHALL extend the per-profile
`data/seed/{profile}_assets.csv` header from
`class_name,name,target_pct,display_order` to
`class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code`.

A CSV file with the legacy 4-column header SHALL be rejected
by `scripts/seed_from_csv.py` with an `abort()` error
(explicit migration required). The `load_assets()` parser
SHALL validate `currency_code` against the allowlist
`{"BRL", "USD"}` and reject other values with an `abort()`
error.

#### Scenario: Loader accepts extended header

- **WHEN** `data/seed/italo_assets.csv` has the extended
  7-column header and `task db-reset` runs
- **THEN** every asset row is created with the supplied
  trade-control values

#### Scenario: Loader rejects legacy 4-column header

- **WHEN** a CSV file has the legacy 4-column header
- **THEN** `scripts/seed_from_csv.py` aborts with exit code 1
  and a message naming the expected header

#### Scenario: Loader rejects non-allowlist currency in CSV

- **WHEN** a CSV row has `currency_code=EUR`
- **THEN** `scripts/seed_from_csv.py` aborts at that row
  with a message identifying the offending value
