## ADDED Requirements

### Requirement: Rebalance plan SHALL expose visual table cues without changing its interaction contract

When `plan.asset_plan` is non-empty, the page SHALL render exactly one `data-testid="rebalance-asset-table"` with existing eight-column Alpine generation, filters, sorting, row keys, action badges, and data. That table SHALL additionally expose the existing sticky-header hook and row-wide hover feedback. When the plan is empty, existing empty-state behavior SHALL remain unchanged.

#### Scenario: Populated plan keeps one table and existing columns

- **WHEN** a valid rebalance plan with assets renders
- **THEN** exactly one `data-testid="rebalance-asset-table"` is present
- **AND** it retains `data-table rebalance-table` plus existing `table-sticky-header`
- **AND** the existing declarative model still supplies `Ação`, `Classe`, `Ativo`, `Atual`, `Alvo`, `Desvio`, `Projetado`, and `Operação` in that order
- **AND** existing filter triggers, sort handlers, row `data-asset-key` values, and action content remain present

#### Scenario: Rebalance row hover is temporary and row-wide

- **WHEN** the pointer enters any rendered rebalance asset row
- **THEN** all cells in that row use the existing hover background for the duration of hover
- **AND** moving the pointer away restores the row’s pre-hover zebra or action-state background
- **AND** no row selection, tooltip, navigation, mutation, or data transformation occurs

#### Scenario: Rebalance header sticks without internal scroll

- **WHEN** the user scrolls the page containing a populated rebalance plan
- **THEN** the table header remains visible at the viewport top with existing header/filter styling
- **AND** the page does not gain a new nested scroll region or alter table columns/layout

#### Scenario: Empty asset plan remains empty state

- **WHEN** `plan.asset_plan` is empty
- **THEN** `data-testid="rebalance-asset-table-empty"` renders as before
- **AND** no sticky or hover table is created
