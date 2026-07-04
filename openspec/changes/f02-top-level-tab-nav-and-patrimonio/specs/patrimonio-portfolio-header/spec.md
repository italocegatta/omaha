## ADDED Requirements

### Requirement: patrimonio-portfolio-header renders three profile-level metrics

The system SHALL render an element with
`data-testid="patrimonio-portfolio-header"` at the top of the
`/patrimonio` page body. The header SHALL display exactly three
metrics for the active profile, in this left-to-right order:
`Investido` (sum of position cost basis, R$), `Valor atual` (sum of
position current value, R$), and `Ganho` (absolute difference plus
percent change vs Investido). Each metric MUST be rendered with a
label (PT-BR), the formatted currency value (R$ prefix, thousands
separator `.`, decimal separator `,`), and for `Ganho` a signed
percent badge.

#### Scenario: Header renders three metrics for populated profile

- **WHEN** an authenticated user visits `/patrimonio` with at least
  one `Position` in the active profile
- **THEN** the page contains an element with
  `data-testid="patrimonio-portfolio-header"`
- **AND** the element renders three labelled sub-elements:
  `Investido`, `Valor atual`, `Ganho`
- **AND** the `Ganho` sub-element shows a signed percent (e.g.
  `+12,34%` or `-2,10%`) with a class indicating sign
  (`.gain-positive` or `.gain-negative`)

#### Scenario: Header renders zeros for empty profile

- **WHEN** an authenticated user visits `/patrimonio` with zero
  positions in the active profile
- **THEN** the header still renders
- **AND** `Investido` and `Valor atual` both display `R$ 0,00`
- **AND** `Ganho` displays `R$ 0,00 (0,00%)` without a sign class

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