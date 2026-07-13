## ADDED Requirements

### Requirement: Asset table headers SHALL expose supported rebalance-style per-column filters and deterministic ordering

The dashboard SHALL render each class section's asset table with a filter affordance on every supported visible header, following rebalance-style interaction: sortable headers keep click-to-toggle ordering, categorical columns use multi-select filters, numeric/currency/percentage columns use bounded range filters, and active filters combine with AND inside the same class section. `Preço médio` and `Qtd` SHALL remain sortable but SHALL NOT expose filter UI or filtering behavior.

Ordering SHALL remain deterministic on ties: when two rows compare equal on the active sort key, the table SHALL fall back to asset name and then a stable row identifier so the visible order does not reshuffle between reactive updates.

#### Scenario: Header filter affordance opens filter panel

- **WHEN** the user clicks the filter control for a visible asset-table column
- **THEN** that column's filter panel opens inside the current class section
- **AND** the filter control remains scoped to that table only

#### Scenario: Multiple filters combine with AND

- **WHEN** the user selects `USD` in `Moeda` and narrows `Posição` to a range
- **THEN** only rows matching both filters remain visible
- **AND** clearing one filter keeps the other active

#### Scenario: Equal values keep stable order

- **WHEN** two rows compare equal on the current sort key
- **THEN** the table falls back to asset name for tie-break
- **AND** equal names keep a stable order from their row id

### Requirement: Asset table shell and header/body treatment SHALL mirror rebalance table chrome

The dashboard SHALL render each class's asset table inside a single elevated shell with a distinct header band, striped body rows, and hover/focus treatment consistent with the rebalance table. The header SHALL read as control surface; the body SHALL read as data surface. Existing row content, inline edit affordances, delete controls, and `data-testid` bindings SHALL remain unchanged.

#### Scenario: Table renders with shared shell treatment

- **WHEN** a class section renders its asset table
- **THEN** the table sits inside one shared shell with a visible header band
- **AND** the body rows use alternating striping consistent with rebalance

#### Scenario: Header and body stay visually separated

- **WHEN** the asset table renders
- **THEN** header chrome remains distinct from body chrome
- **AND** body hover/focus treatment is readable without changing numeric formatting

### Requirement: Monetary filter bounds SHALL respect visible currency context

When a class section's visible rows share one currency code, monetary filter bounds for `Ganho` and `Posição` SHALL format with that currency code instead of defaulting to BRL. The filter panel SHALL therefore show USD bounds when the table is narrowed to USD rows.

#### Scenario: USD monetary filters show USD bounds

- **WHEN** the visible asset rows are all USD
- **THEN** the monetary range filter for `Posição` shows USD-formatted bounds
- **AND** the same panel does not label those bounds as BRL
