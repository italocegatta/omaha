## MODIFIED Requirements

### Requirement: Alignment contract between header stats and table columns

Each class section SHALL render a dedicated class totals row that stays
visible above the asset rows and is horizontally aligned with the
redesigned asset-table columns. The old sparse header-pill alignment
contract is superseded by grouped financial columns.

The class totals row MUST align its values to these table columns:

| Class totals field (`data-testid`) | Asset table column header (`data-testid`) |
|------------------------------------|-------------------------------------------|
| `class-total-gain-value`           | `asset-table-th-gain`                     |
| `class-total-current-value`        | `asset-table-th-position`                 |
| `class-total-current-pct-class`    | `asset-table-th-class-current`            |
| `class-total-target-pct-class`     | `asset-table-th-class-target`             |
| `class-total-deviation-class`      | `asset-table-th-class-deviation`          |
| `class-total-current-pct-portfolio`| `asset-table-th-portfolio-current`        |
| `class-total-target-pct-portfolio` | `asset-table-th-portfolio-target`         |
| `class-total-deviation-portfolio`  | `asset-table-th-portfolio-deviation`      |

The horizontal alignment is verified via DOM measurement: the left-edge
`x` coordinate of each class-totals field MUST be within ±1px of the
left-edge `x` coordinate of the matching table `<th>`.

#### Scenario: Class totals row aligns with grouped class and portfolio columns

- **WHEN** the dashboard renders a populated class section
- **THEN** the class totals row fields for `Classe` and `Carteira` are within ±1px
  of their matching grouped table headers
- **AND** the row remains readable as one pre-asset summary line

#### Scenario: Gain and position totals align with financial columns

- **WHEN** the dashboard renders a populated class section
- **THEN** `data-testid="class-total-gain-value"` aligns with the visible `Ganho` column
- **AND** `data-testid="class-total-current-value"` aligns with `Posição`

#### Scenario: Class totals row remains visible when the section is collapsed

- **WHEN** the user collapses a class section
- **THEN** the asset rows are hidden
- **AND** the class totals row remains visible with the grouped column alignment intact

#### Scenario: Zero deviation renders em-dash in Classe / Desvio

- **GIVEN** a class whose `classDeviationPctClass` is within ±0.01 of 0
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-class"` renders "—"
- **AND** the cell does NOT render "0%"
- **AND** the cell carries the `metric-neutral` class

#### Scenario: Positive deviation renders green value in Classe / Desvio

- **GIVEN** a class whose `classDeviationPctClass` is `+3.5`
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-class"` renders "+4%"
  (rounded via `formatDeviationPp`)
- **AND** the cell carries the `metric-positive` class

#### Scenario: Negative deviation renders red value in Classe / Desvio

- **GIVEN** a class whose `classDeviationPctClass` is `-2.1`
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-class"` renders "-2%"
- **AND** the cell carries the `metric-negative` class

#### Scenario: Zero deviation renders em-dash in Carteira / Desvio

- **GIVEN** a class whose `classPortfolioDeviationPct` is within ±0.01 of 0
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-portfolio"` renders "—"
- **AND** the cell does NOT render "0%"
- **AND** the cell carries the `metric-neutral` class

#### Scenario: Positive deviation renders green value in Carteira / Desvio

- **GIVEN** a class whose `classPortfolioDeviationPct` is `+1.2`
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-portfolio"` renders "+1%"
- **AND** the cell carries the `metric-positive` class

#### Scenario: Negative deviation renders red value in Carteira / Desvio

- **GIVEN** a class whose `classPortfolioDeviationPct` is `-0.8`
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-portfolio"` renders "-1%"
- **AND** the cell carries the `metric-negative` class

#### Scenario: Sobra/Falta pill still overrides deviation display when present

- **GIVEN** a class whose per-asset `target_pct_class` sum exceeds 100
  (so `classDeltaMessage` is non-empty)
- **WHEN** the dashboard renders the class totals row
- **THEN** the Sobra/Falta pill (`data-testid="class-delta-badge"`) is visible
- **AND** the em-dash fallback is NOT rendered (the pill takes precedence)
