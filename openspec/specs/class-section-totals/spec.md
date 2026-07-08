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

The asset table column proportions MUST be defined as CSS
custom properties at `:root` (one variable per column,
`--col-ativo` through `--col-atual-total`) so the
`.class-section-header` grid template and the table's
`<colgroup>` widths can both consume the same source. The
table MUST use `table-layout: fixed` and `width: 100%` so
the `<colgroup>` widths are authoritative.

A column-proportions change MUST be a one-line edit per
variable. Re-aligning the header with the table after a
column-proportions change MUST NOT require a template edit.

#### Scenario: Header and table share the same column template

- **WHEN** the dashboard renders an asset table and a class
  section header
- **THEN** the computed `grid-template-columns` of
  `.class-section-header` resolves to the same value as the
  computed `width` per column on `.asset-table col`
- **AND** changing `--col-ativo` in `:root` (e.g. via
  DevTools) re-aligns both header and table on the next
  layout

#### Scenario: Table layout is fixed, not auto

- **WHEN** the dashboard renders an asset table
- **THEN** the computed `table-layout` of
  `<table class="asset-table">` is `fixed`
- **AND** the sum of `<col>` widths equals the table's
  `clientWidth` (no browser-driven column growth from long
  content)

#### Scenario: Long asset names wrap inside their column

- **GIVEN** an asset named `"Tesouro Selic 2029 - LFT
  Prefixado com Juros Semestrais"` (or any other long string)
- **WHEN** the dashboard renders the asset table at the
  default desktop viewport
- **THEN** the `<td data-testid="asset-row-name">` wraps
  the name across multiple lines (`overflow-wrap: break-word`)
  rather than overflowing horizontally or forcing the column
  to grow
- **AND** the class section header above does NOT shift
  horizontally as a result of the wrap

### Requirement: Alignment contract between header stats and table columns

Each consolidated stat cell in the class section header SHALL
be horizontally aligned with the corresponding table
column header (`<th>`):

| Header stat (`data-testid`) | Table column header (`data-testid`) |
|-----------------------------|-------------------------------------|
| `class-total-value`         | `asset-table-th-current-value`      |
| `class-delta-badge`         | `asset-table-th-target-pct-class`   |
| `class-target-pct-view`     | `asset-table-th-target-pct-total`   |
| `class-current-pct`         | `asset-table-th-current-pct-total`  |

The horizontal alignment is verified via DOM measurement: the
left-edge `x` coordinate of the header stat MUST be within
±1px of the left-edge `x` coordinate of the matching table
`<th>`. Column 6 (`Atual % classe`) has no consolidated
counterpart and stays empty in the header.

#### Scenario: Valor aligned with Valor column

- **WHEN** the dashboard renders a class section
- **THEN** `getBoundingClientRect().left` of
  `data-testid="class-total-value"` is within ±1px of
  `getBoundingClientRect().left` of
  `data-testid="asset-table-th-current-value"`

#### Scenario: Alvo aligned with Alvo % total column

- **WHEN** the dashboard renders a class section
- **THEN** `getBoundingClientRect().left` of
  `data-testid="class-target-pct-view"` is within ±1px of
  `getBoundingClientRect().left` of
  `data-testid="asset-table-th-target-pct-total"`

#### Scenario: Atual aligned with Atual % total column

- **WHEN** the dashboard renders a class section
- **THEN** `getBoundingClientRect().left` of
  `data-testid="class-current-pct"` is within ±1px of
  `getBoundingClientRect().left` of
  `data-testid="asset-table-th-current-pct-total"`

#### Scenario: Sobra/Falta aligned with Alvo % classe column

- **WHEN** the dashboard renders a class section
- **THEN** `getBoundingClientRect().left` of
  `data-testid="class-delta-badge"` (when rendered) is
  within ±1px of `getBoundingClientRect().left` of
  `data-testid="asset-table-th-target-pct-class"`
