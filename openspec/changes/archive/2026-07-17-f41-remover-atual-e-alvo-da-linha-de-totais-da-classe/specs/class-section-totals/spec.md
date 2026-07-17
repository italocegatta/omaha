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

The `class-total-current-pct-class` and `class-total-target-pct-class`
cells in the class totals row SHALL render the em-dash "—" instead of
the percentage values. These values are always 100% (the sum of
per-asset percentages within a class is always 100% by definition) and
carry no information. The em-dash preserves column alignment while
removing redundant data.

#### Scenario: Class totals row aligns with grouped class and portfolio columns

- **WHEN** the dashboard renders a populated class section
- **THEN** the class totals row fields for `Classe` and `Carteira` are within ±1px
  of their matching grouped table headers
- **AND** the row remains readable as a single pre-asset summary line

#### Scenario: Gain and position totals align with financial columns

- **WHEN** the dashboard renders a populated class section
- **THEN** `data-testid="class-total-gain-value"` aligns with the visible `Ganho` column
- **AND** `data-testid="class-total-current-value"` aligns with `Posição`

#### Scenario: Class totals row remains visible when the section is collapsed

- **WHEN** the user collapses a class section
- **THEN** the asset rows are hidden
- **AND** the class totals row remains visible with the grouped column alignment intact

#### Scenario: Class totals row shows em-dash for Atual and Alvo columns

- **WHEN** the dashboard renders a class totals row
- **THEN** the cell `data-testid="class-total-current-pct-class"` contains the text "—"
- **AND** the cell `data-testid="class-total-target-pct-class"` contains the text "—"
- **AND** neither cell displays "100%" or any percentage value

#### Scenario: Class totals row Desvio column still shows deviation value

- **WHEN** the dashboard renders a class totals row with `classDeviationPctClass != 0`
- **THEN** the cell `data-testid="class-total-deviation-class"` still displays the
  formatted deviation value (not "—")
- **AND** the deviation sign styling (positive/negative) is unchanged
