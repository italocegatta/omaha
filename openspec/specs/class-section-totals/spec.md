## Purpose

Surface the class-level consolidated values (`Valor`,
`Alvo % total`, `Atual % total`) directly in the class section
header so the operator can read header → column → rows without
re-anchoring, and keep that alignment robust against future
changes to the asset table column layout.
## Requirements
### Requirement: Consolidated Valor in the class section header

The class section header MUST render the consolidated
`current_value` (sum of `current_value` across the class's
assets) as a plain-text BRL value with no decimal fraction
digits (e.g. `R$ 9.389` — never `R$ 9.389,96`). The value MUST
be rendered at `data-testid="class-total-value"`. When the
class has no assets (`current_value == 0`), the element MUST
render the em-dash `—` instead of `R$ 0`.

#### Scenario: Consolidated Valor renders the BRL sum with no decimals

- **WHEN** the dashboard renders a class whose assets sum to
  `current_value = 9389.45`
- **THEN** the header element `data-testid="class-total-value"`
  contains the text `R$ 9.389` (BRL with `minimumFractionDigits: 0`,
  `maximumFractionDigits: 0`)
- **AND** the element does NOT carry any pill CSS class
  (`.pct-target-pill`, `.pct-current-pill`,
  `.pct-delta-pill`) — it is plain text

#### Scenario: Empty class renders an em-dash for Valor

- **WHEN** the dashboard renders a class whose
  `current_value` is `0` (no assets, or all assets have
  zero `qty * current_price`)
- **THEN** the header element `data-testid="class-total-value"`
  contains the text `—`
- **AND** the element does NOT contain `R$ 0`

### Requirement: Consolidated Alvo % total aligns with the Alvo % total table column

The class section header MUST render the class's
`target_pct` as the consolidated `Alvo % total` value (e.g.
`Alvo 25.00%`), reusing the existing
`pct-target-pill` styling (dashed border, click-to-edit) so
the inline edit flow continues to work. The pill MUST be
placed at the horizontal position aligned with the
`<th data-testid="asset-table-th-target-pct-total">` column
header in the asset table below. The pill's `data-testid`
stays `class-target-pct-view` (no rename — keeps the inline
edit selector stable).

#### Scenario: Consolidated Alvo % total renders the class target

- **WHEN** the dashboard renders a class with `target_pct = 25`
- **THEN** the header element
  `data-testid="class-target-pct-view"` shows `Alvo 25%`
  (matching the existing `commitEditClassPct` contract)
- **AND** the element's `getBoundingClientRect().left` is
  within ±1px of the `Alvo % total`
  `<th data-testid="asset-table-th-target-pct-total">`'s
  `getBoundingClientRect().left`

#### Scenario: Consolidated Alvo % total is still inline-editable

- **WHEN** the user clicks the consolidated `Alvo 25%` pill
  (`data-testid="class-target-pct-view"`)
- **THEN** the inline editor
  (`data-testid="class-inline-edit-input`) opens with
  `classTargetPct` pre-filled
- **AND** Enter / blur still PATCH `/api/classes/{id}` (the
  existing `dashboard-inline-editing` spec contract is
  unchanged)

### Requirement: Consolidated Atual % total aligns with the Atual % total table column

The class section header MUST render the class's `current_pct`
(the class's share of the portfolio's `current_value`) as the
consolidated `Atual % total` value (e.g. `Atual 23.45%`),
reusing the existing `pct-current-pill` styling with the
`ok` / `off` status modifier. The pill MUST be placed at the
horizontal position aligned with the
`<th data-testid="asset-table-th-current-pct-total">` column
header in the asset table below. The pill's `data-testid`
stays `class-current-pct`.

#### Scenario: Consolidated Atual % total renders the class current

- **WHEN** the dashboard renders a class with
  `current_pct = 23.45`
- **THEN** the header element
  `data-testid="class-current-pct"` shows `Atual 23.45%`
  (two-decimal format)
- **AND** the element's `getBoundingClientRect().left` is
  within ±1px of the `Atual % total`
  `<th data-testid="asset-table-th-current-pct-total">`'s
  `getBoundingClientRect().left`

#### Scenario: Consolidated Atual % total inherits ok/off status color

- **GIVEN** a class with `current_pct - target_pct` within
  ±0.01
- **WHEN** the dashboard renders the class section header
- **THEN** the `Atual` pill carries the
  `pct-current-pill--ok` modifier class (the existing
  status colour contract from `dashboard-inline-editing`
  holds)

#### Scenario: Empty class still shows 0.00% for Atual % total

- **WHEN** the dashboard renders a class with no assets
  (`current_value == 0`)
- **THEN** the header `Atual` pill shows `Atual 0.00%` (not
  `—`) — the slot exists with 0% of the portfolio, that is
  itself meaningful

### Requirement: Sobra/Falta pill aligns with the Alvo % classe column

The per-class `Sobra/Falta` pill SHALL
(`data-testid="class-delta-badge"`) MUST be placed at the
horizontal position aligned with the `<th
data-testid="asset-table-th-target-pct-class">` column header
in the asset table below. The pill's text contract
("Sobra X%" / "Falta X%") and visibility contract (hidden
when `|classDelta| <= 0.01`) are unchanged from
`dashboard-inline-editing`.

#### Scenario: Sobra/Falta pill sits over the Alvo % classe column

- **GIVEN** a class whose per-asset `target_pct_class` sum
  exceeds 100 (so `classDelta < -0.01` → pill shows "Sobra X%")
- **WHEN** the dashboard renders the class section header
- **THEN** the pill element
  `data-testid="class-delta-badge"` is visible with the
  Sobra/Falta text
- **AND** the element's `getBoundingClientRect().left` is
  within ±1px of the `Alvo % classe`
  `<th data-testid="asset-table-th-target-pct-class">`'s
  `getBoundingClientRect().left`

#### Scenario: Sobra/Falta pill hidden when on target

- **GIVEN** a class with per-asset `target_pct_class` sum
  within 0.01 of 100
- **WHEN** the dashboard renders the class section header
- **THEN** no element with `data-testid="class-delta-badge"`
  is in the DOM (the existing visibility contract from
  `dashboard-inline-editing` is unchanged)

### Requirement: Consolidated stats remain visible when the section is collapsed

The system SHALL keep the three consolidated stat cells (`Valor`, `Alvo % total`,
`Atual % total`) and the `Sobra/Falta` pill visible when the class section body is collapsed (the
`<table class="asset-table">` is hidden via
`.class-section-body--collapsed`). Only the asset table rows
and the per-asset delete confirm dialog hide when collapsed;
the header row (chevron + swatch + name + × + stats) stays
fully visible.

#### Scenario: All header stats visible with body collapsed

- **WHEN** the user clicks the class section header so
  `isOpen = false`
- **THEN** the `<div class="class-section-body">` gains
  the `class-section-body--collapsed` class (the asset table
  is no longer in the rendered layout)
- **AND** the header still renders all five cells: chevron,
  swatch, class name, × button, `class-total-value`,
  `class-current-pct`, and the `Alvo` pill if not editing
- **AND** the `Sobra/Falta` pill, if rendered, is also
  still visible

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

A column-proportions change MUST be a one-line edit per variable.
Re-aligning grouped headers, class totals, and table rows after a
column-proportions change MUST NOT require a template edit.

#### Scenario: Grouped header, totals row, and asset rows share one width template

- **WHEN** the dashboard renders a class section with the compact asset table
- **THEN** the grouped `<thead>`, the class totals row, and the asset rows resolve their columns from the same `--col-*` CSS variables
- **AND** the visible `Ganho` column contains absolute value plus percentage in one cell
- **AND** mutating one `--col-*` value in DevTools re-aligns all three layers on the next layout

#### Scenario: Table layout remains fixed with merged gain presentation

- **WHEN** the dashboard renders the compact asset table
- **THEN** the computed `table-layout` of `<table class="asset-table">` is `fixed`
- **AND** the `Ganho` cell stays horizontally aligned with the single visible `Ganho` header label

#### Scenario: Long asset names wrap without breaking alignment

- **GIVEN** an asset named `"Tesouro Selic 2029 - LFT Prefixado com Juros Semestrais"`
- **WHEN** the dashboard renders the compact asset table
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
