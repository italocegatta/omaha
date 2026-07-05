# cross-profile-sharing

## MODIFIED Requirements

### Requirement: The patrimonio page exposes a household aggregate view mode

The `GET /patrimonio` endpoint SHALL render the family aggregate
view whenever the session's active profile is a `Profile` row
with `is_family_sentinel=True` (the Família sentinel). The
sentinel is selectable via the same `profile-switcher` `<select>`
that lists Italo and Ana — Família is a **peer** of the real
profiles, not a separate mode accessed via querystring or
toggle. The legacy `?view=household` querystring continues to
work for backward compatibility (deep links and tests written
against F06 keep resolving).

When the family view is active the page MUST aggregate, for
every `Profile` row in the database (excluding the Família
sentinel itself and any system-profile sentinel row), the same
three metrics the per-profile view already exposes
(`Investido`, `Valor atual`, `Ganho`), summed across **every
position in the database**. The aggregator MUST reuse the
per-row summation rules defined by `broker-csv-import-totals`
(sum the broker-published `Position.total_invested` and
`Position.total_current` directly; never recompute `qty *
price`). The aggregate MUST be identical regardless of which
family operator is logged in.

#### Scenario: family aggregate is symmetric across operators

- **WHEN** the database contains positions under multiple `Profile`
  rows owned by different `User` rows
- **AND** operator A selects Família from the profile-switcher
  and the dashboard renders
- **THEN** the rendered `patrimonio-portfolio-header` displays
  `Investido` equal to the sum of `total_invested` across **all**
  `Position` rows in the database (summed globally, excluding
  any sentinel)
- **AND** `Valor atual` equals the sum of `total_current` across
  the same positions
- **AND** `Ganho` equals `Valor atual − Investido`
- **AND** `Ganho` carries a signed percent badge against the summed
  `Investido`
- **AND** the **same** totals render when operator B selects
  Família from the profile-switcher with the same database state

#### Scenario: family aggregate omits target allocation columns

- **WHEN** the database contains `AssetClass` rows with non-uniform
  `target_pct` across profiles
- **AND** the active profile is the Família sentinel
- **THEN** the rendered page does NOT display any per-class
  `target_pct` value (the allocation target is undefined for an
  aggregated portfolio)
- **AND** the page still renders `current_pct` and `current_value`
  per aggregated class (those ARE well-defined on the sum)

#### Scenario: family mode is read-only

- **WHEN** the active profile is the Família sentinel (or
  `?view=household` is on the querystring for backward compat)
- **THEN** the rendered page disables the `+ Classe`,
  `+ Ativo`, and `Importar CSV` action buttons
- **AND** the inline class-edit affordances (rename class, retarget
  percentage, delete class) are absent or disabled
- **AND** every mutation endpoint (`POST /classes`,
  `POST /api/assets`, `DELETE /api/assets/{id}`,
  `PATCH /api/assets/{id}`, `POST /import`) returns `409 Conflict`
  with a JSON error body naming `"reason": "household_read_only"`
  while the family view is active
- **AND** `POST /rebalanceamento` returns the same 409

#### Scenario: family mode triggered by sentinel profile selection

- **WHEN** the operator is logged in with `active_profile_id`
  pointing to the Família sentinel row
- **THEN** `GET /patrimonio` renders the family aggregate view
  (no querystring needed; the sentinel flag alone is sufficient)
- **AND** the profile-switcher's `<select>` shows "Família" as
  the selected option
- **AND** no `?view=household` toggle button is rendered in the
  header (Família is reachable via the chip alone)

### Requirement: The header exposes a household mode toggle

`templates/base.html` SHALL NOT render a household toggle button.
The family aggregate view is accessible via the
`profile-switcher` `<select>` (the Família sentinel is the
canonical entry point), not via a separate header button. The
legacy `?view=household` querystring continues to work for
backward compatibility (deep links from F06 keep resolving),
but the only first-class UI affordance for entering family
mode is selecting the Família sentinel in the
`profile-switcher`.

The profile-switcher SHALL render one `<option>` per real
`Profile` row (i.e., every profile with `is_family_sentinel=
False`) **plus** the Família sentinel as a visually-distinct
entry separated by a CSS rule (border, optgroup label, or
similar — implementation detail). The Família sentinel is
always listed (it is not gated on profile count, since the
aggregate is the family itself).

#### Scenario: family mode triggered via sentinel, no toggle button

- **WHEN** the database contains any real `Profile` row
- **THEN** the rendered header includes a `profile-switcher`
  `<select>` whose options include both the real profiles
  (Italo, Ana, …) and the Família sentinel
- **AND** the rendered header does NOT include any element
  with `data-testid="family-toggle"` (the toggle is gone)
- **AND** selecting the Família sentinel via the `<select>`
  activates the family aggregate view (the dashboard renders
  the cross-User aggregate, the chip shows "Família"
  selected, no querystring is needed)

#### Scenario: family sentinel hidden with no real profiles

- **WHEN** the database contains zero real `Profile` rows
  (only the Família sentinel exists)
- **THEN** the `profile-switcher` is hidden (no profile to
  show)
- **AND** the operator cannot activate the family aggregate
  from the chip (the sentinel is not enough — the chip
  requires a real profile to render)

## REMOVED Requirements

### Requirement: Household mode preserves per-profile isolation

**Reason**: F06 deliberately removed the intra-User aggregation
constraint. F07 consolidates the family-view entry point as a
profile-sentinel option in the `profile-switcher`, not a
querystring toggle. The sentinel row is the canonical
"family aggregate profile" — there is no longer an
intra-`User` vs cross-`User` invariant to preserve because
the aggregate is the family itself, accessible as a profile
option.

**Migration**: No migration needed. Operators authenticate
with the shared family password (`PRD §1.2`); selecting the
Família sentinel exposes no data they could not already see
by switching profiles. If the product later introduces
differentiated per-User authentication, a new requirement
must re-introduce the isolation invariant and gate the
family aggregator accordingly.

## ADDED Requirements

### Requirement: Family aggregate collapses classes and assets by name (full-join)

The family aggregator MUST collapse `AssetClass` rows whose
`name` is identical across profiles into a **single** rendered
class row, summing `total_invested` and `total_current` per
`broker-csv-import-totals`. Within each aggregated class,
`Asset` rows whose `name` is identical across the underlying
profiles MUST also collapse into a single asset row. The
collapsed class retains the `color` of the first occurrence in
display order. The collapse MUST NOT walk across distinct
`name` values — every aggregated row has a homogeneous `name`
within itself.

#### Scenario: classes with identical names collapse across profiles

- **WHEN** the database contains `AssetClass` row C1 (profile P1,
  name "Renda Fixa", total_invested = 1000) and `AssetClass` row
  C2 (profile P2, name "Renda Fixa", total_invested = 2000)
- **AND** the active profile is the Família sentinel
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
