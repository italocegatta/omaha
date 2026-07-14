## ADDED Requirements

### Requirement: Shared table base classes

The system SHALL provide `.data-table-shell`, `.data-table`, `.data-table-thead`, `.data-table-th`, `.data-table-tbody`, `.data-table-tr`, `.data-table-td` CSS classes that define shared visual properties for all data tables (shell container, table element, header row, header cell, body container, body row, body cell).

#### Scenario: Base classes applied to rebalance table
- **WHEN** the rebalance plan table is rendered
- **THEN** each structural element (`<div>` shell, `<table>`, `<thead>`, `<th>`, `<tbody>`, `<tr>`, `<td>`) SHALL carry both the base class (e.g. `.data-table-shell`) and the specific class (e.g. `.rebalance-table-shell`)

#### Scenario: Base classes applied to portfolio table
- **WHEN** the portfolio asset table is rendered
- **THEN** each structural element SHALL carry both the base class and the specific class (e.g. `.portfolio-table-shell`)

#### Scenario: Visual parity after base extraction
- **WHEN** base classes are applied alongside existing specific classes
- **THEN** the rendered visual output SHALL be identical to the pre-refactor state (no pixel-level differences in spacing, colors, borders, or typography)

### Requirement: Table CSS custom properties

The system SHALL define `--table-shell-bg`, `--table-header-bg`, `--table-row-odd`, `--table-row-even`, `--table-row-hover`, `--table-border`, `--table-border-strong`, `--table-text`, `--table-text-muted` as CSS custom properties on `:root`.

#### Scenario: Variables resolve to current palette
- **WHEN** the page loads
- **THEN** all `--table-*` variables SHALL resolve to values that produce the same visual result as the current hardcoded color-mix formulas

#### Scenario: Palette swap via variables
- **WHEN** a `--table-*` variable is overridden (e.g. via a class or media query)
- **THEN** ALL tables consuming that variable SHALL reflect the new value without any other CSS changes

### Requirement: Specific classes override base

Specific table classes (`.rebalance-table-shell`, `.portfolio-table-shell`, `.rebalance-table`, `.asset-table`, etc.) SHALL override base class properties only where they differ. Properties that are identical between tables SHALL NOT be duplicated in specific classes.

#### Scenario: Rebalance-specific overrides
- **WHEN** rebalance table has properties that differ from the base (e.g. row color-coding by action: buy/sell/neutral)
- **THEN** `.rebalance-*` classes SHALL provide those overrides and the base SHALL NOT include them

#### Scenario: Portfolio-specific overrides
- **WHEN** portfolio table has properties that differ from the base (e.g. 2-level header, summary row background)
- **THEN** `.portfolio-*` / `.asset-table` classes SHALL provide those overrides and the base SHALL NOT include them

#### Scenario: No duplicated identical rules
- **WHEN** a CSS property has the same value in both rebalance and portfolio tables
- **THEN** that property SHALL exist only in the base class, not in both specific classes
