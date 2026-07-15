# patrimonio-portfolio-header Specification

## Purpose
TBD - created by archiving change f02-top-level-tab-nav-and-patrimonio. Update Purpose after archive.
## Requirements
### Requirement: patrimonio-portfolio-header renders three profile-level metrics

The system SHALL render an element with
`data-testid="patrimonio-portfolio-header"` at the top of the
`/patrimonio` page body. The header SHALL display exactly three
metrics for the active profile, in this left-to-right order:
`Investido`, `Valor atual`, and `Ganho`.

`Investido` and `Valor atual` MUST render as currency values using the
existing PT-BR numeric separators. `Ganho` MUST render both the absolute
currency delta and the percentage delta, but the presentation SHALL use
separate sub-elements so the absolute value and percentual value can be
aligned and styled independently. The `Ganho` metric MUST also expose a
sign-state visual treatment:

- positive gain → positive color + upward iconography
- negative gain → negative color + downward iconography
- zero gain → neutral styling, no positive/negative state class

#### Scenario: Header renders split gain metrics for populated profile

- **WHEN** an authenticated user visits `/patrimonio` with at least one `Position`
  in the active profile
- **THEN** the page contains `data-testid="patrimonio-portfolio-header"`
- **AND** the element renders labelled metrics `Investido`, `Valor atual`, `Ganho`
- **AND** the `Ganho` metric exposes separate sub-elements for absolute and percentual values

#### Scenario: Positive gain shows positive state and upward iconography

- **WHEN** the portfolio `gain` is greater than zero
- **THEN** the `Ganho` metric renders positive-state styling
- **AND** the metric includes upward iconography

#### Scenario: Negative gain shows negative state and downward iconography

- **WHEN** the portfolio `gain` is less than zero
- **THEN** the `Ganho` metric renders negative-state styling
- **AND** the metric includes downward iconography

#### Scenario: Header renders zeros for empty profile

- **WHEN** an authenticated user visits `/patrimonio` with zero positions in the active profile
- **THEN** the header still renders
- **AND** `Investido` and `Valor atual` both display `R$ 0,00`
- **AND** `Ganho` displays `R$ 0,00` and `0,0%` in neutral styling

### Requirement: Header is profile-scoped, not class-scoped

The header SHALL aggregate across **all** classes of the active
profile, summing position cost basis and current value. The
header MUST NOT duplicate or nest `class-section-totals` (which
remains class-level and unchanged by this spec).

#### Scenario: Header aggregates across all classes

- **WHEN** the active profile has 3 classes with mixed positions
- **THEN** `Investido` equals the sum of `Position.cost_basis`
  across all classes
- **AND** `Valor atual` equals the sum of `Position.current_value`
  across all classes
- **AND** `Ganho` equals `Valor atual - Investido`

### Requirement: Header survives the dashboard rename

The header SHALL render correctly after the template rename
`dashboard.html → patrimonio.html`. No `data-testid`, no class, no
copy changes between the old and new template path.

#### Scenario: Header renders identically post-rename

- **WHEN** `/patrimonio` is served from `templates/patrimonio.html`
  (post-rename) with the same active profile and positions
- **THEN** the rendered HTML contains
  `data-testid="patrimonio-portfolio-header"`
- **AND** the three metric labels are `Investido`, `Valor atual`,
  `Ganho` in that order

### Requirement: Portfolio class section Alpine component
The `classSection()` Alpine component SHALL consume formatters from the shared `table-formatters.js` module instead of defining them inline. The component's method signatures and return values SHALL remain identical to the pre-refactor implementation.

#### Scenario: Formatter output unchanged after refactor
- **WHEN** the portfolio page renders with the same asset/class data
- **THEN** all formatted values (money with currency, percentages, quantities, sign classes, sign icons) produce identical output to the pre-refactor version

#### Scenario: Multi-currency preserved
- **WHEN** `formatMoney` is called with a USD asset
- **THEN** the output uses USD currency symbol, not BRL

#### Scenario: Import modal formatters also shared
- **WHEN** the import modal (`$store.importModal`) formats values
- **THEN** it uses the same shared formatters as the class section component
