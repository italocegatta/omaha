## ADDED Requirements

### Requirement: The patrimonio page exposes a household aggregate view mode

The `GET /patrimonio` endpoint SHALL accept an optional
`view=household` query parameter that, when present, switches the
rendered template from profile-scoped to household-scoped. In
household mode the page MUST aggregate, for the logged-in viewer,
the same three metrics the per-profile view already exposes
(`Investido`, `Valor atual`, `Ganho`), summed across **every**
`Profile` row that belongs to the viewer. The aggregator MUST
reuse the per-row summation rules defined by
`broker-csv-import-totals` (sum the broker-published
`Position.total_invested` and `Position.total_current` directly;
never recompute `qty * price`).

#### Scenario: viewer with two profiles sees household totals

- **WHEN** the logged-in viewer owns two profiles (Italo + Ana
  Livia), each with at least one `Position`
- **AND** the viewer visits `GET /patrimonio?view=household`
- **THEN** the rendered `patrimonio-portfolio-header` element
  displays `Investido` equal to the sum of `total_invested`
  across all viewer-owned positions
- **AND** `Valor atual` equals the sum of `total_current` across
  the same positions
- **AND** `Ganho` equals `Valor atual − Investido`
- **AND** `Ganho` carries a signed percent badge against the
  summed `Investido`

#### Scenario: household mode is read-only

- **WHEN** the viewer visits `GET /patrimonio?view=household`
- **THEN** the rendered page disables the `+ Classe`,
  `+ Ativo`, and `Importar CSV` action buttons
- **AND** the inline class-edit affordances (rename class,
  retarget percentage, delete class) are absent or disabled
- **AND** the per-row `×` delete button still renders when the
  household view falls back to per-class sections, but each
  mutation endpoint (`POST /classes`, `POST /api/assets`,
  `DELETE /api/assets/{id}`, `PATCH /api/assets/{id}`,
  `POST /import`) returns `409 Conflict` with a JSON error body
  naming `"reason": "household_read_only"` while `view=household`
  is active

### Requirement: The header exposes a household mode toggle

`templates/base.html` SHALL render a household toggle adjacent to
the existing profile chip when the viewer owns two or more
profiles. The toggle SHALL submit a `GET /patrimonio` request
with `view=household` (or `view=profile` to revert) via a native
form — no client-side fetch, no Alpine state. The toggle MUST be
hidden when the viewer owns a single profile (the household
aggregate equals the only profile — no value added).

#### Scenario: household toggle visible with two profiles

- **WHEN** the logged-in viewer owns two or more profiles
- **AND** the viewer is on any authenticated page
- **THEN** the rendered header includes a form whose
  `data-testid="household-toggle"` and whose default-submit
  target is `/patrimonio?view=household`
- **AND** the form's submit button reads `Casa`

#### Scenario: household toggle hidden with one profile

- **WHEN** the logged-in viewer owns exactly one profile
- **THEN** the rendered header does not include any element with
  `data-testid="household-toggle"`
- **AND** visiting `/patrimonio?view=household` is harmless —
  the page renders the single profile (household view equals
  profile view when only one profile exists)

### Requirement: Household mode preserves per-profile isolation

The household aggregator SHALL only sum positions whose owning
`Profile` row is bound to the logged-in viewer via the existing
foreign key (`Profile.user_id == viewer.id`). The aggregator
MUST NOT walk across `User` boundaries — even though
`cross-profile-sharing` lets the viewer mutate any of their own
profiles, the household aggregate is always intra-`User`.

#### Scenario: household totals do not leak across User rows

- **WHEN** the logged-in viewer is Ana
- **AND** Ana owns profiles P1 (Ana) and P2 (Ana-Livia) but the
  database also contains profile P3 owned by a different User
- **THEN** `GET /patrimonio?view=household` aggregates positions
  from P1 and P2 only
- **AND** P3's `AssetClass` / `Asset` / `Position` rows are NOT
  summed into the household totals

#### Scenario: household mode does not mutate cross-User state

- **WHEN** Ana is logged in with `view=household` active
- **THEN** the chip's `<select>` continues to list Ana-owned
  profiles only (the existing `header-profile-switcher` contract
  is unchanged)
- **AND** the toggle never exposes a profile the viewer does
  not own
