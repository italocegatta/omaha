# bdd-e2e-coverage Specification

## Purpose

Define the required coverage of the BDD e2e suite under
`tests/bdd/`: the seven scenario groups, the dual-profile
parametrization, the combinatorial-coverage rule, the single
full-journey regression guard, and the PT-BR `.feature` file
format. This capability exists so a non-developer can read the
suite's intent and so a regression guard has a stable list of
flows that MUST remain green.

## Requirements

### Requirement: Login + profile picker covered

The system SHALL provide BDD scenarios that exercise the login
flow (shared family password) and the profile picker for both
seeded profiles (`Italo` and `Ana`), including a negative login
case (wrong password).

#### Scenario: Login + profile pick OK (Italo)
- **WHEN** the user fills the login form with username `Italo`
  and the shared password
- **AND** clicks `Entrar`
- **THEN** the user lands on `/profiles`
- **AND** selecting the `Italo` profile row navigates to `/`
- **AND** the dashboard shows the profile name `Italo`

#### Scenario: Login + profile pick OK (Ana)
- **WHEN** the user fills the login form with username `Ana` and
  the shared password
- **AND** selects the `Ana` profile row
- **THEN** the dashboard shows the profile name `Ana`

#### Scenario: Login fail — senha errada
- **WHEN** the user fills the login form with username `Italo`
  and a wrong password
- **AND** clicks `Entrar`
- **THEN** the page re-renders with an error message and the
  user does NOT land on `/profiles`

### Requirement: Class CRUD covered

The system SHALL provide BDD scenarios that exercise the class
CRUD paths: snapshot create (2 classes via `POST /classes` form),
inline add + `PATCH /api/classes/{id}` target, and duplicate-name
409.

#### Scenario: Snapshot create 2 classes
- **WHEN** the user opens the class editor
- **AND** fills row 1 with `Renda Fixa` at 60%
- **AND** fills row 2 with `Ações` at 40%
- **AND** submits
- **THEN** the dashboard renders 2 class sections
- **AND** the section named `Renda Fixa` shows `60%`
- **AND** the section named `Ações` shows `40%`

#### Scenario: Inline add + PATCH class target
- **WHEN** the user clicks the dashboard's `+` class button
- **AND** types `Reserva` and `10` in the inline form
- **THEN** a third class section appears
- **WHEN** the user clicks the section's target cell and types
  `15` and presses `Enter`
- **THEN** the section shows `15%`
- **AND** the database `asset_classes.target_pct` for that row
  reads `15`

#### Scenario: Negative — duplicate class name
- **WHEN** the user creates `Renda Fixa` via inline add
- **AND** attempts to create `Renda Fixa` again via inline add
- **THEN** the API returns 409
- **AND** the dashboard renders an inline error message

### Requirement: Asset CRUD (manual) covered

The system SHALL provide BDD scenarios that exercise manual asset
creation (2 ativos em cada classe) via the dashboard's inline
asset form and the per-class sum validator (`validate_target_pct_sum`).

#### Scenario: Manual add 2 ativos em cada classe
- **WHEN** the user opens the inline asset form for `Renda Fixa`
- **AND** adds `Tesouro Selic 2029` at 50%
- **AND** adds `Tesouro IPCA+ 2029` at 50%
- **AND** opens the inline asset form for `Ações`
- **AND** adds `PETR4` at 60%
- **AND** adds `VALE3` at 40%
- **THEN** the dashboard renders 4 asset rows
- **AND** `Renda Fixa` contains 2 rows
- **AND** `Ações` contains 2 rows

#### Scenario: Negative — per-class sum != 100
- **WHEN** the user attempts to set `PETR4.target_pct` to `60`
  and `VALE3.target_pct` to `50` (sum = 110)
- **THEN** the API returns 422
- **AND** the dashboard renders an inline error message
- **AND** neither value is persisted

### Requirement: Asset import covered

The system SHALL provide BDD scenarios that exercise the import
modal flow with the tiny fixture
(`tests/fixtures/tiny_portfolio.csv`, 4 rows), covering the
happy path, per-row manual class assignment, and an empty-CSV
negative case.

#### Scenario: Import 4-row CSV happy
- **WHEN** the user opens the import modal
- **AND** uploads `tiny_portfolio.csv`
- **AND** assigns `Renda Fixa` to all rows in the
  `RF Pos` category
- **AND** assigns `Ações` to all rows in the `Ações` category
- **AND** confirms
- **THEN** the dashboard renders 4 asset rows
- **AND** each row has at least 1 position

#### Scenario: Import + per-row assign
- **WHEN** the user opens the import modal
- **AND** uploads `tiny_portfolio.csv`
- **AND** manually picks `Renda Fixa` for
  `TESOURO_SELIC_2029`
- **AND** manually picks `Ações` for `PETR4`
- **AND** leaves the other two rows on the default placeholder
- **AND** attempts to confirm
- **THEN** the modal blocks confirmation (the commit handler
  skips empty `class_id` assignments and the modal surfaces an
  inline error)
- **WHEN** the user assigns the remaining two rows
- **AND** confirms
- **THEN** the dashboard renders 4 asset rows

#### Scenario: Import CSV vazio
- **WHEN** the user opens the import modal
- **AND** uploads a CSV with no data rows (header only)
- **THEN** the modal renders an inline error message
- **AND** no `import_previews` row is created

### Requirement: Target PATCH (per-class-of-portfolio) covered

The system SHALL provide BDD scenarios that exercise
`PATCH /api/classes/{id}` and assert the dashboard reflects the
new value on both the class summary and the per-asset derived
percentage.

#### Scenario: PATCH per-class target reflects in dashboard
- **WHEN** the user clicks the class section's target cell for
  `Renda Fixa`
- **AND** types `70` and presses `Enter`
- **THEN** the section shows `70%`
- **AND** the database `asset_classes.target_pct` for that row
  reads `70`

### Requirement: Target PATCH (per-asset-of-class) covered

The system SHALL provide BDD scenarios that exercise
`PATCH /api/assets/{id}` and assert the dashboard reflects the
new value on the asset row.

#### Scenario: PATCH per-asset target reflects in dashboard
- **WHEN** the user clicks the asset row's "dentro da classe"
  cell for `TESOURO_SELIC_2029`
- **AND** types `70` and presses `Enter`
- **THEN** the row shows `70%` in the dentro-da-classe column
- **AND** the database `assets.target_pct` for that row reads
  `70`

### Requirement: Derived portfolio % display covered

The system SHALL provide BDD scenarios that exercise the derived
display `asset.target_pct * class.target_pct / 100` on the
dashboard, asserting the value is recomputed on every PATCH to
either stored target.

#### Scenario: Derived portfolio % recomputes on class PATCH
- **GIVEN** `Renda Fixa` has target `60%` and contains
  `Tesouro Selic 2029` at `50%` of class
- **WHEN** the user PATCHes `Renda Fixa.target_pct` to `70`
- **THEN** the dashboard renders `Tesouro Selic 2029`'s
  portfolio-% cell as `35,0%`

#### Scenario: Derived portfolio % recomputes on asset PATCH
- **GIVEN** `Renda Fixa` has target `60%` and contains
  `Tesouro Selic 2029` at `50%` of class (derived `30,0%`)
- **WHEN** the user PATCHes `Tesouro Selic 2029.target_pct` to
  `70`
- **THEN** the dashboard renders the derived cell as `42,0%`

### Requirement: Dual-profile parametrization

Every BDD scenario that touches a stage owned by a profile
(login onward) SHALL execute under both seeded profiles
(`Italo` and `Ana`) via `pytest.mark.parametrize`. Scenarios
that touch only the login or the static pages MAY execute under
one profile.

#### Scenario: Each stage-touching scenario runs against both profiles
- **WHEN** `task test-bdd` runs
- **THEN** every scenario under
  `class_crud.feature`, `asset_crud.feature`, `import.feature`,
  `target_pct.feature`, `derived_display.feature`, and
  `full_journey.feature` reports at least 2 parametrized cases
  with profile names `Italo` and `Ana`

### Requirement: Single full-journey happy path

The system SHALL provide exactly one BDD scenario
(`full_journey.feature`) that exercises every stage in order on a
fresh DB for a single profile. This scenario is the regression
guard for the full loop; if any stage breaks, this scenario fails
and the failure message names the stage by its step.

#### Scenario: Full happy path — login → profile → classes → import → patches → derived
- **WHEN** the user follows the canonical operator journey:
  login, pick profile, create 2 classes via snapshot, import
  4-row CSV, PATCH per-class target, PATCH per-asset target,
  read derived portfolio %
- **THEN** every step in the journey asserts successfully and
  the dashboard renders 4 asset rows with the expected derived
  percentages

### Requirement: Combinatorial coverage

The system SHALL provide BDD scenarios that combine stages in
at least three distinct orders across the seven stage groups
(e.g. `classes → assets manual`, `classes → import → assets`,
`classes → assets → PATCH → derived`). The full-journey scenario
satisfies one combination; the partial-flow scenarios
(`class_crud`, `asset_crud`, `import`, `target_pct`,
`derived_display`) cover the others.

#### Scenario: At least three distinct stage orderings covered
- **WHEN** the suite reports its scenario inventory
- **THEN** the inventory includes scenarios that exercise at
  least three of the following stage orderings:
  classes only; classes → assets manual; classes → import;
  classes → assets → target PATCH; classes → import →
  target PATCH; classes → assets → PATCH → derived

### Requirement: Profile isolation

The system SHALL provide BDD scenarios that verify creating
classes + assets under one profile does NOT leak to the other.

#### Scenario: Italo's classes invisible to Ana
- **GIVEN** Italo has 2 classes (`Renda Fixa`, `Ações`) with 4
  assets between them
- **WHEN** the user logs out and logs back in as `Ana`
- **THEN** Ana's dashboard renders no class sections and no
  asset rows

#### Scenario: Ana's classes invisible to Italo
- **GIVEN** Ana has 1 class (`Reserva`) with 1 asset
- **WHEN** the user logs out and logs back in as `Italo`
- **THEN** Italo's dashboard renders only his own classes and
  assets

### Requirement: PT-BR feature files

The system SHALL provide `.feature` files in PT-BR
(`Funcionalidade`, `Cenário`, `Dado`, `Quando`, `Então`,
`Esquema do Cenário`, `Exemplos`). Step implementations in
`tests/bdd/step_defs/` MAY be in English; the literal
user-typed text in scenario steps MUST match the PT-BR UI labels.

#### Scenario: `.feature` files parse with PT-BR keywords
- **WHEN** pytest-bdd collects `tests/bdd/features/`
- **THEN** every `.feature` file parses without a locale
  warning and the scenario count matches the design document
