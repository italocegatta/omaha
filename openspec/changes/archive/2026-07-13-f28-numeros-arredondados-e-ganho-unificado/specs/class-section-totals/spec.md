## MODIFIED Requirements

### Requirement: Asset table column widths are driven by CSS variables

The class totals row and asset table column proportions MUST be defined as CSS custom properties at `:root` so the grouped header, class totals row, and asset rows all consume the same width source. The contract covers the compact `/patrimonio` order:

1. `Ativo`
2. `Qtd`
3. `Preço médio`
4. `Ganho`
5. `Posição`
6. `Desvio da posição`
7. `Classe / Atual`
8. `Classe / Alvo`
9. `Classe / Desvio`
10. `Carteira / Atual`
11. `Carteira / Alvo`
12. `Carteira / Desvio`
13. `Compra`
14. `Venda`
15. `Moeda`

The implementation SHALL render `Ganho` as one visible column that contains absolute BRL value and percentage together. The asset table MUST use `table-layout: fixed` and `width: 100%` so the width variables remain authoritative.

#### Scenario: Grouped header, totals row, and asset rows share one width template

- **WHEN** the dashboard renders a class section with the compact asset table
- **THEN** the grouped `<thead>`, the class totals row, and the asset rows resolve their columns from the same `--col-*` CSS variables
- **AND** the visible `Ganho` column contains absolute value plus percentage in one cell
- **AND** mutating one `--col-*` value in DevTools re-aligns all three layers on the next layout

## ADDED Requirements

### Requirement: Gain cell renders absolute value and percentage together

The system SHALL render the asset-table `Ganho` field as one visible cell that shows the absolute gain and percentual gain together. The absolute value SHALL keep the existing BRL display contract, and the percentual value SHALL keep the existing percentage display contract and sign styling.

#### Scenario: Asset row gain shows one compact cell

- **WHEN** the dashboard renders an asset row with non-zero `gain_value` and `gain_pct`
- **THEN** the `Ganho` cell shows absolute BRL value plus percentual value together
- **AND** the cell keeps positive/negative/neutral sign styling

### Requirement: Asset table numeric values use compact precision

The system SHALL render monetary cells in the asset table with 0 decimal places. The `Qtd` column SHALL render with 0 decimal places for all assets except BTC, which SHALL render with 3 decimal places. Its range-filter labels SHALL retain that BTC precision when their value belongs to BTC. Percentage values in `Ganho`, `Classe / Atual`, `Classe / Alvo`, `Carteira / Atual`, `Carteira / Alvo`, and `Carteira / Desvio` SHALL render with 0 decimal places; percentage values in other columns SHALL keep their established formatter. A rounded value whose magnitude is below one whole percentage point SHALL render as `0%`, never `-0%`. Exact numeric zero SHALL also render as `0%`; `—` is reserved for absent or invalid values.

#### Scenario: BTC quantity keeps 3 decimal places

- **WHEN** an asset row has `asset_name = BTC` and `qty = 1.23456`
- **THEN** the `Qtd` cell renders with 3 decimal places
- **AND** the other monetary cells on the row remain compact with 0 decimal places

#### Scenario: Non-BTC quantity rounds to 0 decimals

- **WHEN** an asset row has `asset_name = PETR4` and `qty = 12.7`
- **THEN** the `Qtd` cell renders with 0 decimal places

#### Scenario: BTC quantity range label keeps precision

- **WHEN** a `Qtd` range-filter boundary belongs to `asset_name = BTC` with `qty = 1.23`
- **THEN** its range label renders as `1,230`

#### Scenario: Rounded negative percentage near zero is normalized

- **WHEN** a requested whole-percentage cell has a value of `-0.4`
- **THEN** it renders as `0%`

#### Scenario: Exact zero target remains a percentage

- **WHEN** `Classe / Alvo` or `Carteira / Alvo` has exact numeric value `0`
- **THEN** it renders as `0%`
- **AND** it does not render as `—`

#### Scenario: Only requested percentage columns use whole percentages

- **WHEN** an asset row includes percentage values with fractional precision
- **THEN** `Ganho`, `Classe / Atual`, `Classe / Alvo`, `Carteira / Atual`, `Carteira / Alvo`, and `Carteira / Desvio` render whole percentages
- **AND** `Classe / Desvio` keeps its established percentage precision

### Requirement: Asset table exposes range filters for quantity and average price

The asset table SHALL expose range-filter panels for `Qtd` and `Preço médio` using the same column filter model as its other numeric columns. Each range filter SHALL constrain displayed asset rows and compose with active filters using AND semantics.

#### Scenario: Quantity and average-price ranges compose

- **WHEN** the user sets a minimum `Qtd` and a minimum `Preço médio`
- **THEN** only rows satisfying both numeric ranges remain visible

### Requirement: Asset table filters use canonical fields and safe viewport behavior

The asset-table enum filters SHALL read `buy_enabled`, `sell_enabled`, and
`currency_code` from their asset rows while retaining the visible `Compra`,
`Venda`, and `Moeda` column keys. Quantity range boundaries SHALL retain the
asset identity that supplied each boundary so BTC labels keep three decimal
places even when another asset has the same quantity. An empty class SHALL
expose safe `0..0` numeric range bounds. Open fixed filter panels SHALL
reposition when page or table-shell scrolling, or viewport resizing, could
detach them from their trigger.

#### Scenario: Enum filter constrains canonical trade field

- **WHEN** the user selects `Liberado` in `Compra`
- **THEN** only assets with `buy_enabled = true` remain visible

#### Scenario: Tied BTC range boundary retains BTC precision

- **WHEN** BTC and a non-BTC asset share a quantity range boundary
- **THEN** the BTC boundary label renders with three decimal places

#### Scenario: Empty class opens numeric filter

- **WHEN** a class without assets opens a numeric range filter
- **THEN** its controls use finite `0..0` bounds

### Requirement: Gain column sorts by absolute gain magnitude

The system SHALL sort `Ganho` rows by `abs(gain_value)` instead of the signed raw value. When two rows have the same absolute gain, the existing secondary stable order by asset name or asset key MUST remain intact.

#### Scenario: Clicking gain header orders by magnitude

- **WHEN** the user clicks the `Ganho` header
- **THEN** rows reorder by absolute gain magnitude
- **AND** rows with equal absolute gain keep stable secondary ordering
