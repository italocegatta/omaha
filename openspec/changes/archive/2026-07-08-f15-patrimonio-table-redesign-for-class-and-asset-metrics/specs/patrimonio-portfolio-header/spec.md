## MODIFIED Requirements

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
