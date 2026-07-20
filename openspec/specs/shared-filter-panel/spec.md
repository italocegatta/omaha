# shared-filter-panel Specification

## Purpose
Reusable Jinja macro `filter_controls` in `_filter_controls.html` that generates the complete filter panel UI for sortable table columns. Supports enum, range, and composite filter kinds with inline (rebalance) or teleported (portfolio) positioning.

## Requirements
### Requirement: Shared filter panel macro

The system SHALL provide a single reusable Jinja macro `filter_controls` in `src/omaha/templates/_filter_controls.html` that generates the complete filter panel UI for a sortable table column: trigger button, clear button, and filter panel (enum, range, or composite).

#### Scenario: Macro generates enum filter panel
- **WHEN** a template calls `filter_controls('name', 'Ativo', filter_kind='enum')`
- **THEN** the macro SHALL render a trigger button with `data-testid="asset-header-filter-name-trigger"` (or equivalent pattern), a clear button with `data-testid="asset-header-clear-name-trigger"`, and an enum filter panel with checkboxes for each unique value

#### Scenario: Macro generates range filter panel
- **WHEN** a template calls `filter_controls('qty', 'Qtd', filter_kind='range')`
- **THEN** the macro SHALL render a range filter panel with dual slider inputs, a track, a fill bar, and min/max value labels

#### Scenario: Macro generates composite filter panel
- **WHEN** a template calls `filter_controls('gain', 'Ganho', filter_kind='composite', ranges=[...])`
- **THEN** the macro SHALL render a composite filter panel containing multiple labeled range sliders, each with its own track, fill, and value labels

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

### Requirement: Filter panel alignment

The macro SHALL accept an `align` parameter (`'left'` or `'right'`, default `'left'`) that controls the horizontal position of the filter panel relative to its trigger.

#### Scenario: Left-aligned panel
- **WHEN** `align='left'` is passed
- **THEN** the panel SHALL have class `rebalance-filter-panel--left`

#### Scenario: Right-aligned panel
- **WHEN** `align='right'` is passed
- **THEN** the panel SHALL have class `rebalance-filter-panel--right`

### Requirement: Unified filter icon

Both tables SHALL use the same icon for the filter trigger button: `filter_alt` from `material-symbols-outlined`.

#### Scenario: Rebalance filter icon
- **WHEN** the rebalance table renders a filter trigger button
- **THEN** the button SHALL contain `<span class="material-symbols-outlined">filter_alt</span>`

#### Scenario: Portfolio filter icon
- **WHEN** the portfolio table renders a filter trigger button
- **THEN** the button SHALL contain `<span class="material-symbols-outlined">filter_alt</span>` (replacing the current `expand_more` icon)

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

### Requirement: Preserve data-testid attributes

All existing `data-testid` attributes on filter trigger buttons, clear buttons, and filter panels SHALL be preserved unchanged to avoid breaking existing e2e and BDD tests.

#### Scenario: Existing test selectors resolve
- **WHEN** the shared macro renders filter controls for column `'name'`
- **THEN** the trigger button SHALL have `data-testid="asset-header-filter-name-trigger"` (portfolio) or `data-testid="rebalance-header-filter-name-trigger"` (rebalance), matching the existing pattern
