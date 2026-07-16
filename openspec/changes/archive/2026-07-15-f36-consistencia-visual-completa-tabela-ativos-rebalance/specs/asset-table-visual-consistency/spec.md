# Spec: asset-table-visual-consistency

## Purpose

Align the portfolio asset table (`_patrimonio_class_section.html`) with the rebalance table (`_rebalance_plan.html`) across 5 visual dimensions: filter icons, filter positioning, numeric formatting, totals row styling, and header spacing.

## Requirements

### Requirement: Unified filter icon component

The asset table filter trigger buttons SHALL use `material-symbols-outlined` as the CSS class for the filter icon span, matching the rebalance table pattern.

#### Scenario: Asset table filter icon uses material-symbols-outlined
- **WHEN** the asset table renders a filter trigger button
- **THEN** the icon span SHALL have class `material-symbols-outlined` (not `icon icon--sm`)

#### Scenario: Rebalance table filter icon unchanged
- **WHEN** the rebalance table renders a filter trigger button
- **THEN** the icon span SHALL continue to use `material-symbols-outlined`

### Requirement: Filter panel positioning preserved

The asset table SHALL continue to use `teleport=true` for filter panels. The rebalance table SHALL continue to use inline positioning. Both approaches SHALL produce correctly positioned filter panels within their respective contexts.

#### Scenario: Asset filter panel escapes overflow clipping
- **WHEN** user clicks a filter trigger in the asset table
- **THEN** the filter panel SHALL be teleported to `<body>` and positioned via `filterPanelStyle()`, escaping the `.class-section-body` overflow clipping

#### Scenario: Rebalance filter panel stays inline
- **WHEN** user clicks a filter trigger in the rebalance table
- **THEN** the filter panel SHALL render inline within the `<th>` element

### Requirement: Deviation columns use 0 decimal places with explicit sign

The asset table deviation columns (`class_deviation_pct`, `portfolio_deviation_pct`) SHALL display values using 0 decimal places with explicit sign (`+X%` or `-X%`), matching the rebalance table's `formatDeviationPp` format.

#### Scenario: Class deviation shows 0 decimals with sign
- **WHEN** an asset row has `class_deviation_pct = 3.7`
- **THEN** the class deviation cell SHALL display `+4%` (rounded, with explicit `+` sign)

#### Scenario: Portfolio deviation shows 0 decimals with sign
- **WHEN** an asset row has `portfolio_deviation_pct = -2.3`
- **THEN** the portfolio deviation cell SHALL display `-2%` (rounded, with explicit `-` sign)

#### Scenario: Zero deviation shows 0%
- **WHEN** an asset row has `class_deviation_pct = 0`
- **THEN** the deviation cell SHALL display `0%`

### Requirement: "Total da classe" row styled as highlighted card

The "Total da classe" summary row SHALL be visually distinguished as a card-like element using the class color.

#### Scenario: Totals row has class-colored left border
- **WHEN** a class section renders its totals row
- **THEN** the row SHALL have a `border-left` of 3px using the class color

#### Scenario: Totals row has tinted background
- **WHEN** a class section renders its totals row
- **THEN** the row cells SHALL have a background tinted with the class color at low opacity (8-12% over `--surface`)

#### Scenario: Totals label uses class color
- **WHEN** a class section renders its totals row
- **THEN** the "TOTAL DA CLASSE" label text SHALL use the class color

### Requirement: Header spacing accommodates all column names

The asset table header cells SHALL have sufficient padding and column width to display all column names without truncation.

#### Scenario: ATIVO column fits header text
- **WHEN** the asset table renders on a 1440px+ viewport
- **THEN** the "ATIVO" header text SHALL be fully visible without truncation or overflow

#### Scenario: All sub-headers fit their text
- **WHEN** the asset table renders the sub-header row (Atual, Alvo, Desvio under Classe and Carteira)
- **THEN** all sub-header texts SHALL be fully visible without truncation
