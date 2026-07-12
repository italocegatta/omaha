## ADDED Requirements

### Requirement: Table-heavy visual states are covered by committed baselines

The visual regression suite SHALL include table-heavy states for dashboard surfaces that users inspect for allocations and plans: Patrimônio asset tables, Rebalance plan tables, and import review tables. Each covered state SHALL assert structural markers before screenshot capture and SHALL maintain committed desktop and mobile baselines.

#### Scenario: Patrimônio table state is baseline-covered

- **WHEN** `tests/visual/test_snapshots.py::test_assets_table_snapshot` or `test_patrimonio_snapshot` runs
- **THEN** it waits for table markers and BRL text before capture
- **AND** it writes or compares committed baselines for both desktop and mobile viewports

#### Scenario: Rebalance and import tables are baseline-covered

- **WHEN** `tests/visual/test_snapshots.py` captures the rebalance plan or import review states
- **THEN** the same committed-baseline workflow applies
- **AND** intentional changes to table spacing, wrapping, or header composition require baseline updates in the same change

### Requirement: Table baselines must expose wrap, overflow, and typography drift

The baseline states for table-heavy pages SHALL be dense enough to make header crowding, cell overflow, and font-rhythm changes visible during review. Visual diffs SHALL remain the contract for issues like cramped headers or cells that render with a different typographic weight than neighboring rows.

#### Scenario: Header crowding is visible in review

- **WHEN** a table header changes padding, line-height, or font inheritance such that labels crowd or wrap differently
- **THEN** the next visual run fails against the committed baseline until the new appearance is intentionally reviewed
- **AND** the review surface makes the drift visible without relying on computed-style assertions alone
