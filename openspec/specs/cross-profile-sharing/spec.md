# cross-profile-sharing Specification

## Purpose
TBD - created by archiving change direct-landing-with-header-profile-switcher. Update Purpose after archive.
## Requirements
### Requirement: Any logged-in user can view any profile's dashboard data

The system SHALL render the dashboard at `GET /` for whichever
profile `active_profile_id` points to, regardless of which
`User` owns that profile. Cross-profile viewing is the explicit
contract; the prior implicit isolation guarantee is removed.

#### Scenario: Ana views Italo's classes
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and Italo's profile has at least one
  `AssetClass` row
- **THEN** `GET /` returns 200 with those `AssetClass` rows
  rendered in the dashboard's `class-summary` section

#### Scenario: Ana views Italo's positions
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and Italo's `AssetClass` rows own `Asset` +
  `Position` rows
- **THEN** `GET /` returns 200 with the portfolio aggregates
  computed from Italo's rows (invested, current value, gain)
- **AND** the rendered asset table includes Italo's `Asset`
  rows with their position counts

#### Scenario: Ana can mutate Italo's portfolio
- **WHEN** Ana is logged in with `active_profile_id` pointing
  to Italo's profile
- **THEN** `POST /classes`, `POST /api/assets`, `DELETE
  /api/assets/{id}`, `PATCH /api/assets/{id}`, and
  `POST /import` succeed against Italo's profile (the
  per-profile ownership gates in `routes/classes.py`,
  `routes/assets.py`, `routes/imports.py` are loosened to
  "must belong to the active profile" only)

### Requirement: Cross-profile previews and assets no longer 404 by ownership

The system SHALL NOT raise 404 on the basis of viewer-vs-owner
mismatch. API endpoints that previously raised 404 when the
active session pointed at a profile different from the
resource's owner MUST accept the operation when the resource
belongs to the active profile (regardless of viewer).

#### Scenario: PATCH /api/assets/{id} for active-profile asset
- **WHEN** Ana is logged in, `active_profile_id` points to
  Italo's profile, and the asset id belongs to a class under
  Italo's profile
- **THEN** the PATCH returns 200 with `{"id", "target_pct"}`
  (no 404)

#### Scenario: POST /import commits against the active profile
- **WHEN** Ana is logged in with `active_profile_id` pointing
  to Italo's profile and posts a CSV preview commit
- **THEN** the committed `Position` rows land under Italo's
  profile (not Ana's), regardless of the viewer

### Requirement: BDD profile_sharing feature asserts cross-profile visibility

The BDD suite SHALL ship a `profile_sharing.feature` (renamed
from `profile_isolation.feature`) whose scenarios assert the
new contract: any logged-in user can switch to another
profile's dashboard and see that profile's classes and
positions.

#### Scenario: Ana sees Italo's seeded classes after switching
- **WHEN** Ana logs in, switches to Italo's profile via the
  header chip, and Italo's profile has at least one seeded
  class
- **THEN** the dashboard renders Italo's class summary (not
  Ana's empty state)

#### Scenario: Italo sees Ana's seeded classes after switching
- **WHEN** Italo logs in, switches to Ana's profile via the
  header chip, and Ana's profile has at least one seeded
  class
- **THEN** the dashboard renders Ana's class summary (not
  Italo's empty state)

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
