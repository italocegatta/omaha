# Spec: rebalance-page

## Purpose

Render the rebalance plan on `/rebalanceamento` with declarative Alpine table surface defined by F27 handoff. The page still consumes the existing rebalance wire contract; only the client-side table implementation and visible interaction model change.

## MODIFIED Requirements

### Requirement: Asset plan table renders eight POC-parity columns plus a data attribute

The system SHALL render the rebalance asset plan with a single declarative Alpine column model. The `<thead>` and `<tbody>` SHALL be generated from that model via `<template x-for>`, with no duplicated header/body markup. The table SHALL expose F27 POC's eight visible columns, in order: Ação, Classe, Ativo, Atual, Alvo, Desvio, Projetado, Operação. `Desvio` SHALL combine value and percentage; `Operação` SHALL combine action, value, and quantity.

The table container SHALL keep `data-testid="rebalance-asset-table"` so existing tests can target the plan surface. Each rendered row SHALL retain a stable `data-asset-key` attribute equal to `asset_key`.

When `plan.asset_plan` is empty, the page SHALL keep the existing empty-state behavior instead of rendering an empty table.

#### Scenario: Declarative table renders eight POC-parity columns

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-asset-table"` exposes eight visible columns in POC order
- **AND** each rendered row carries `data-asset-key`

#### Scenario: Empty plan still renders empty state

- **WHEN** `plan.asset_plan` is empty
- **THEN** the empty-state copy renders instead of an empty grid

### Requirement: Sortable asset plan table

The system SHALL sort and filter rebalance asset plan rows client-side in Alpine. Clicking a column header SHALL toggle `asc → desc → asc` on the same column. Categorical columns SHALL use multi-select enum filters. Numeric columns SHALL use range filters with min/max bounds. Composite columns SHALL expose multiple range controls within the same filter panel.

The page SHALL keep PT-BR labels and SHALL NOT render legacy handcrafted table/filter controls that are no longer part of the declarative surface.

#### Scenario: Clicking a numeric column sorts ascending

- **WHEN** the user clicks the `Atual` header
- **THEN** rows are reordered by `current_value` ascending

#### Scenario: Filters compose with AND logic

- **WHEN** class filter selects `Renda Fixa` AND action filter selects `Comprar`
- **THEN** only rows matching all criteria remain visible
