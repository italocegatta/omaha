## MODIFIED Requirements

### Requirement: Rebalance page Alpine component
The `rebalancePage()` Alpine component SHALL consume formatters from the shared `table-formatters.js` module instead of defining them inline. The component's method signatures and return values SHALL remain identical to the pre-refactor implementation.

#### Scenario: Formatter output unchanged after refactor
- **WHEN** the rebalance page renders with the same plan data
- **THEN** all formatted values (BRL amounts, percentages, quantities, action labels, row classes, cell classes) produce identical output to the pre-refactor version

#### Scenario: Shared module imported once
- **WHEN** the rebalance page loads
- **THEN** `table-formatters.js` is imported exactly once via `<script type="module">`
