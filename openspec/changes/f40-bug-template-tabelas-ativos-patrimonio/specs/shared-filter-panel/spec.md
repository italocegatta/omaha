## MODIFIED Requirements

### Requirement: Filter panel positioning modes

The macro SHALL accept a `teleport` boolean parameter (default `false`). When `false`, the filter panel SHALL render inline inside the `<th>` with `position: absolute`. When `true`, the panel SHALL be wrapped in `<template x-teleport="body">` and use `filterPanelStyle()` for dynamic viewport positioning.

#### Scenario: Inline positioning (rebalance)
- **WHEN** `filter_controls('asset_name', 'Ativo', filter_kind='enum', teleport=false)` is called in `_rebalance_plan.html`
- **THEN** the filter panel SHALL render as a direct child of `<th>`, positioned `absolute` relative to the header cell, without `x-teleport`

#### Scenario: Inline positioning (portfolio)
- **WHEN** `filter_controls('name', 'Ativo', filter_kind='enum')` is called in `_patrimonio_class_section.html`
- **THEN** the filter panel SHALL render as a direct child of `<th>`, positioned `absolute` relative to the header cell
- **AND** the panel SHALL NOT be clipped by `overflow: hidden` on the `<th>`

#### Scenario: Filter panel visible after click
- **WHEN** user clicks the filter icon on any column in the asset table
- **THEN** the filter panel SHALL be visible below the header
- **AND** `x-show="openFilter['key']"` SHALL toggle the panel visibility
- **AND** `@click.outside` SHALL close the panel

### Requirement: Preserve existing filter functionality

All existing filter behavior SHALL be preserved after the refactor: enum checkbox filtering, range dual-slider filtering, composite multi-range filtering, "Todos" / "Todas" select-all, clear filter, and active-filter indicator.

#### Scenario: Enum filter still works in rebalance
- **WHEN** user clicks the filter icon on the "Ativo" column in the rebalance table and selects a value
- **THEN** the table SHALL filter to show only rows matching that value

#### Scenario: Range filter still works in portfolio
- **WHEN** user clicks the filter icon on the "Qtd" column in the portfolio table and adjusts the range slider
- **THEN** the table SHALL filter to show only rows within the selected range

#### Scenario: Clear filter still works
- **WHEN** user clicks the clear button on an active filter
- **THEN** the filter SHALL be removed and all rows SHALL be shown again
