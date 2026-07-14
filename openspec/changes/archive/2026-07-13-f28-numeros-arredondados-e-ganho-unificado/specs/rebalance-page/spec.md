## MODIFIED Requirements

### Requirement: Asset plan table renders eight POC-parity columns plus a data attribute

The system SHALL render the rebalance asset plan with a single declarative Alpine column model. The `<thead>` and `<tbody>` SHALL be generated from that model via `<template x-for>`, with no duplicated header/body markup. The table SHALL expose F27 POC's eight visible columns, in order: `Ação`, `Classe`, `Ativo`, `Atual`, `Alvo`, `Desvio`, `Projetado`, `Operação`. `Desvio` SHALL combine value and percentage; `Operação` SHALL combine action, value, and quantity. The quantity subvalue SHALL render with 0 decimal places for non-BTC assets and 3 decimal places for BTC assets. Null or unavailable quantities SHALL remain blank.

The table container SHALL keep `data-testid="rebalance-asset-table"` so existing tests can target the plan surface. Each rendered row SHALL retain a stable `data-asset-key` attribute equal to `asset_key`.

When `plan.asset_plan` is empty, the page SHALL keep the existing empty-state behavior instead of rendering an empty table.

#### Scenario: Declarative table renders eight POC-parity columns

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-asset-table"` exposes eight visible columns in POC order
- **AND** each rendered row carries `data-asset-key`

#### Scenario: BTC quantity renders with 3 decimal places

- **WHEN** the rendered operation cell belongs to `asset_name = BTC` and `trade_quantity = 1.23456`
- **THEN** the quantity subvalue renders with 3 decimal places
- **AND** the operation cell still combines action, BRL amount, and quantity in one visible column

#### Scenario: Empty plan still renders empty state

- **WHEN** `plan.asset_plan` is empty
- **THEN** the empty-state copy renders instead of an empty grid
