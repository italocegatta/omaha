## MODIFIED Requirements

### Requirement: Portfolio class section Alpine component
The `classSection()` Alpine component SHALL consume formatters from the shared `table-formatters.js` module instead of defining them inline. The component's method signatures and return values SHALL remain identical to the pre-refactor implementation.

#### Scenario: Formatter output unchanged after refactor
- **WHEN** the portfolio page renders with the same asset/class data
- **THEN** all formatted values (money with currency, percentages, quantities, sign classes, sign icons) produce identical output to the pre-refactor version

#### Scenario: Multi-currency preserved
- **WHEN** `formatMoney` is called with a USD asset
- **THEN** the output uses USD currency symbol, not BRL

#### Scenario: Import modal formatters also shared
- **WHEN** the import modal (`$store.importModal`) formats values
- **THEN** it uses the same shared formatters as the class section component
