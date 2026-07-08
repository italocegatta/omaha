## MODIFIED Requirements

### Requirement: Asset table with sortable columns

The dashboard MUST render each class section's assets in a single
redesigned `<table>` inside the `Ativos` section. Each row MUST carry
the financial fields needed by the approved mockup: asset name,
quantity, average price, gain value, gain percentage, current
position value, position deviation, class current/target/deviation,
portfolio current/target/deviation, and the unchanged `Compra`,
`Venda`, and `Moeda` controls.

The legacy asset-row `Classe` column is removed. `Ganho` MUST behave as
one operator-facing column even if the implementation uses separate
internal absolute and percentual subcells.

Every visible data column MUST be sortable by clicking its `<th>`:

- text columns (`Ativo`, `Moeda`) sort alphabetically
- numeric/percentage/currency columns sort numerically
- first click sorts ascending, second click descending
- sort state MUST NOT persist across page reloads

Sorting remains local to each class section: rows MUST stay attached to
their owning class section and only reorder within that section.

#### Scenario: Click on asset name sorts alphabetically

- **WHEN** the user clicks the `Ativo` header (`data-testid="asset-table-th-name"`)
- **THEN** asset rows in that class section are sorted alphabetically ascending
- **AND** a second click sorts them descending

#### Scenario: Click on numeric metric sorts numerically

- **WHEN** the user clicks the `Posição` header (`data-testid="asset-table-th-position"`)
- **THEN** asset rows in that class section are sorted by current position value ascending
- **AND** a second click sorts them descending

#### Scenario: Gain remains one visible column while sorting by its numeric components

- **WHEN** the dashboard renders the redesigned table
- **THEN** the operator sees one visible `Ganho` column label
- **AND** the row cells still align absolute and percentual gain values independently
- **AND** sorting by `Ganho` uses the declared numeric key for that column

#### Scenario: Legacy class column is not rendered

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** no asset-row column labeled `Classe` is present
- **AND** each row still remains visually scoped to the class section that owns it

### Requirement: Asset table column proportions live in CSS variables

The redesigned asset table column widths SHALL be defined as CSS custom
properties at `:root`, one variable per rendered column/subcolumn,
including the two internal `Ganho` subcolumns. The table MUST consume
these variables via a `<colgroup>` and MUST use `table-layout: fixed`
and `width: 100%`.

The `.class-section-header` / class totals surface MUST consume the same
variables so grouped labels, totals, and rows re-align automatically
when any `--col-*` value changes.

Long asset names MUST wrap inside their `<td>` via `overflow-wrap:
break-word` rather than overflow horizontally or force the column to grow.

#### Scenario: Column widths are CSS-variable-driven for redesigned table

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the `<table class="asset-table">` contains a `<colgroup>` whose `<col>` widths
  resolve from the corresponding `--col-*` custom properties
- **AND** the table's computed `table-layout` is `fixed`

#### Scenario: Grouped headers and rows share the same column template

- **WHEN** both the grouped header surface and the asset rows are rendered
- **THEN** their computed column widths match the same `--col-*` template
- **AND** mutating any `--col-*` value re-aligns them on the next layout

#### Scenario: Stable header testids exist for redesigned columns

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the sortable headers expose stable `data-testid` values for the new column set,
  including at least `asset-table-th-name`, `asset-table-th-qty`,
  `asset-table-th-avg-price`, `asset-table-th-gain`, `asset-table-th-position`,
  `asset-table-th-position-deviation`, `asset-table-th-class-current`,
  `asset-table-th-class-target`, `asset-table-th-class-deviation`,
  `asset-table-th-portfolio-current`, `asset-table-th-portfolio-target`,
  and `asset-table-th-portfolio-deviation`
