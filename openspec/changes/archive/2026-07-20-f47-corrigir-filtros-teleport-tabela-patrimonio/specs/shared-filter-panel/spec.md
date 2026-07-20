## MODIFIED Requirements

### Requirement: Filter panel positioning modes

The macro SHALL accept a `teleport` boolean parameter (default `false`). When `false`, the filter panel SHALL render inline inside the `<th>` with `position: absolute`. When `true`, the panel SHALL be wrapped in `<template x-teleport="body">` and use `filterPanelStyle()` for dynamic viewport positioning.

All calls to `filter_controls()` in `_patrimonio_class_section.html` SHALL use the default `teleport=false` (inline positioning). The `teleport=true` parameter SHALL NOT be used in the portfolio asset table.

#### Scenario: Inline positioning (rebalance)
- **WHEN** `filter_controls('asset_name', 'Ativo', filter_kind='enum', teleport=false)` is called in `_rebalance_plan.html`
- **THEN** the filter panel SHALL render as a direct child of `<th>`, positioned `absolute` relative to the header cell, without `x-teleport`

#### Scenario: Inline positioning (portfolio)
- **WHEN** `filter_controls('name', 'Ativo', filter_kind='enum')` is called in `_patrimonio_class_section.html`
- **THEN** the filter panel SHALL render as a direct child of `<th>`, positioned `absolute` relative to the header cell
- **AND** the panel SHALL NOT be clipped by `overflow: hidden` on the `<th>` or any ancestor container

#### Scenario: Portfolio table shell does not clip filter panels
- **WHEN** the portfolio asset table renders with inline filter panels
- **THEN** `.portfolio-table-shell` SHALL have `overflow: visible` to prevent clipping of absolutely-positioned filter panels
- **AND** filter panels SHALL be visible below their respective `<th>` headers when toggled open

#### Scenario: Filter panel visible after click
- **WHEN** user clicks the filter icon on any column in the asset table
- **THEN** the filter panel SHALL be visible below the header
- **AND** `x-show="openFilter['key']"` SHALL toggle the panel visibility
- **AND** `@click.outside` SHALL close the panel
