## MODIFIED Requirements

### Requirement: Asset table column widths are driven by CSS variables

The class totals row and asset table column proportions MUST be
defined as CSS custom properties at `:root` so the grouped header,
class totals row, and asset rows all consume the same width source.
The contract is no longer limited to the legacy eight-column layout;
it SHALL cover the redesign order approved for `/patrimonio`:

1. `Ativo`
2. `Qtd`
3. `Preço médio`
4. `Ganho` absolute subcell
5. `Ganho` percentual subcell
6. `Posição`
7. `Desvio` da posição
8. `Classe / Atual`
9. `Classe / Alvo`
10. `Classe / Desvio`
11. `Carteira / Atual`
12. `Carteira / Alvo`
13. `Carteira / Desvio`
14. `Compra`
15. `Venda`
16. `Moeda`

The implementation MAY render `Ganho` as two internal subcolumns for
alignment and formatting, but the operator-facing grouped header MUST
present `Ganho` as a single visible column. The asset table MUST use
`table-layout: fixed` and `width: 100%` so the width variables remain
authoritative.

A column-proportions change MUST be a one-line edit per variable.
Re-aligning grouped headers, class totals, and table rows after a
column-proportions change MUST NOT require a template edit.

#### Scenario: Grouped header, totals row, and asset rows share one width template

- **WHEN** the dashboard renders a class section with the redesigned table
- **THEN** the grouped `<thead>`, the class totals row, and the asset rows
  resolve their columns from the same `--col-*` CSS variables
- **AND** mutating one `--col-*` value in DevTools re-aligns all three layers
  on the next layout

#### Scenario: Table layout remains fixed with merged gain presentation

- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the computed `table-layout` of `<table class="asset-table">` is `fixed`
- **AND** the two internal `Ganho` subcells stay horizontally aligned with the
  single visible `Ganho` header label

#### Scenario: Long asset names wrap without breaking alignment

- **GIVEN** an asset named `"Tesouro Selic 2029 - LFT Prefixado com Juros Semestrais"`
- **WHEN** the dashboard renders the redesigned asset table
- **THEN** the `Ativo` cell wraps the name with `overflow-wrap: break-word`
- **AND** the grouped header and class totals row do NOT shift horizontally

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
- **AND** the row remains readable as a single pre-asset summary line

#### Scenario: Gain and position totals align with financial columns

- **WHEN** the dashboard renders a populated class section
- **THEN** `data-testid="class-total-gain-value"` aligns with the visible `Ganho` column
- **AND** `data-testid="class-total-current-value"` aligns with `Posição`

#### Scenario: Class totals row remains visible when the section is collapsed

- **WHEN** the user collapses a class section
- **THEN** the asset rows are hidden
- **AND** the class totals row remains visible with the grouped column alignment intact
