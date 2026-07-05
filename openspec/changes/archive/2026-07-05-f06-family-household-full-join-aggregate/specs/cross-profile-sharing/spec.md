# cross-profile-sharing

## MODIFIED Requirements

### Requirement: The patrimonio page exposes a household aggregate view mode

The `GET /patrimonio` endpoint SHALL accept an optional
`view=household` query parameter that, when present, switches the
rendered template from profile-scoped to **family-wide** mode. In
family mode the page MUST aggregate, for every `Profile` row in the
database (excluding any system-profile sentinel row), the same three
metrics the per-profile view already exposes (`Investido`,
`Valor atual`, `Ganho`), summed across **every position in the
database**. The aggregator MUST reuse the per-row summation rules
defined by `broker-csv-import-totals` (sum the broker-published
`Position.total_invested` and `Position.total_current` directly;
never recompute `qty * price`). The aggregate MUST be identical
regardless of which family operator is logged in.

#### Scenario: family aggregate is symmetric across operators

- **WHEN** the database contains positions under multiple `Profile`
  rows owned by different `User` rows
- **AND** operator A logs in and visits `GET /patrimonio?view=household`
- **THEN** the rendered `patrimonio-portfolio-header` displays
  `Investido` equal to the sum of `total_invested` across **all**
  `Position` rows in the database (summed globally)
- **AND** `Valor atual` equals the sum of `total_current` across
  the same positions
- **AND** `Ganho` equals `Valor atual − Investido`
- **AND** `Ganho` carries a signed percent badge against the summed
  `Investido`
- **AND** the **same** totals render when operator B logs in and
  visits the same URL with the same database state

#### Scenario: family aggregate omits target allocation columns

- **WHEN** the database contains `AssetClass` rows with non-uniform
  `target_pct` across profiles
- **AND** the viewer visits `GET /patrimonio?view=household`
- **THEN** the rendered page does NOT display any per-class
  `target_pct` value (the allocation target is undefined for an
  aggregated portfolio)
- **AND** the page still renders `current_pct` and `current_value`
  per aggregated class (those ARE well-defined on the sum)

#### Scenario: family mode is read-only

- **WHEN** the viewer visits `GET /patrimonio?view=household`
- **THEN** the rendered page disables the `+ Classe`,
  `+ Ativo`, and `Importar CSV` action buttons
- **AND** the inline class-edit affordances (rename class, retarget
  percentage, delete class) are absent or disabled
- **AND** every mutation endpoint (`POST /classes`,
  `POST /api/assets`, `DELETE /api/assets/{id}`,
  `PATCH /api/assets/{id}`, `POST /import`) returns `409 Conflict`
  with a JSON error body naming `"reason": "household_read_only"`
  while `view=household` is active

### Requirement: The header exposes a household mode toggle

`templates/base.html` SHALL render a family aggregate toggle
adjacent to the existing profile chip when **the database** contains
two or more `Profile` rows (independent of which operator is logged
in). The toggle SHALL submit a `GET /patrimonio` request with
`view=household` (or omit the parameter to revert to per-profile)
via a native form — no client-side fetch, no Alpine state. The
button label SHALL read `Família` and SHALL carry
`data-testid="family-toggle"`. The toggle MUST be hidden when the
database contains a single `Profile` row (the family aggregate
equals that profile).

#### Scenario: family toggle visible with two profiles regardless of operator

- **WHEN** the database contains two or more `Profile` rows
- **AND** any family operator is on any authenticated page
- **THEN** the rendered header includes a form whose
  `data-testid="family-toggle"` and whose default-submit target
  is `/patrimonio?view=household`
- **AND** the form's submit button reads `Família`

#### Scenario: family toggle hidden with single profile

- **WHEN** the database contains exactly one `Profile` row
- **THEN** the rendered header does not include any element with
  `data-testid="family-toggle"`
- **AND** visiting `/patrimonio?view=household` is harmless — the
  page renders the single profile (family aggregate equals
  profile aggregate when only one profile exists)

## REMOVED Requirements

### Requirement: Household mode preserves per-profile isolation

**Reason**: F06 deliberately removed the intra-User aggregation
constraint. The seed (`src/omaha/seed.py`) creates Italo and Ana
Livia as two distinct `User` rows, so an intra-User aggregation
never represented the family aggregate the operator actually wanted.
F06 supersedes this requirement with cross-User aggregation. The
"family aggregate is symmetric across operators" requirement now
guarantees that all operators see the same total — there is no
User-to-User isolation invariant to preserve because the aggregate
is the family, not a viewer-owned subset.

**Migration**: No migration needed. Operators authenticate with the
shared family password (`PRD §1.2`); the family aggregate exposes
no data they could not already see by switching profiles. If the
product later introduces differentiated per-User authentication, a
new requirement must re-introduce the isolation invariant and gate
the family aggregator accordingly.

## ADDED Requirements

### Requirement: Family aggregate collapses classes and assets by name (full-join)

The family aggregator MUST collapse `AssetClass` rows whose `name`
is identical across profiles into a **single** rendered class row,
summing `total_invested` and `total_current` per
`broker-csv-import-totals`. Within each aggregated class, `Asset`
rows whose `name` is identical across the underlying profiles MUST
also collapse into a single asset row. The collapsed class retains
the `color` of the first occurrence in display order. The collapse
MUST NOT walk across distinct `name` values — every aggregated row
has a homogeneous `name` within itself.

#### Scenario: classes with identical names collapse across profiles

- **WHEN** the database contains `AssetClass` row C1 (profile P1,
  name "Renda Fixa", total_invested = 1000) and `AssetClass` row
  C2 (profile P2, name "Renda Fixa", total_invested = 2000)
- **AND** the viewer visits `GET /patrimonio?view=household`
- **THEN** the rendered class-summary section shows exactly one
  row for "Renda Fixa" with `current_value` equal to the sum
  3000 (modulo current/invested ratio — current analogous)

#### Scenario: assets with identical names collapse within an aggregated class

- **WHEN** the aggregated class "Renda Fixa" contains Asset A1
  (profile P1, name "Tesouro IPCA", total_invested = 500) and
  Asset A2 (profile P2, name "Tesouro IPCA",
  total_invested = 700)
- **THEN** the rendered asset table inside the aggregated "Renda
  Fixa" section shows exactly one row for "Tesouro IPCA" with
  `current_value` summing the position `total_current` of A1 and
  A2's underlying position rows

#### Scenario: classes with distinct names stay separate

- **WHEN** the database contains `AssetClass` "Renda Fixa" (P1)
  and `AssetClass` "Ações" (P2)
- **THEN** the family aggregate renders two separate class rows,
  one per distinct name
