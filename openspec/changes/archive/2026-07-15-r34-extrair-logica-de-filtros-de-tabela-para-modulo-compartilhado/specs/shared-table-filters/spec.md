## ADDED Requirements

### Requirement: Shared filter JS module
The system SHALL provide `table-filters.js` as an ES module exporting pure functions for table column filter logic. Functions SHALL accept generic parameters (rows array, column definitions, filter state) rather than reading from component `this` context.

#### Scenario: Module exports range computation functions
- **WHEN** a consumer imports from `table-filters.js`
- **THEN** the module exports `rangeBounds`, `rangeStep`, `ensureRangeBounds`, `clampRangeMin`, `clampRangeMax`, `rangeFillStyle`, `formatRangeValue` functions

#### Scenario: Module exports filter state functions
- **WHEN** a consumer imports from `table-filters.js`
- **THEN** the module exports `filterActive`, `toggleFilterPanel`, `clearFilter`, `computeFilteredRows` functions

#### Scenario: Functions are pure (no side effects on inputs)
- **WHEN** `rangeBounds` is called with a rows array and column key
- **THEN** it returns `{min, max}` without modifying the input array

#### Scenario: Module uses ES module syntax
- **WHEN** the file is loaded
- **THEN** it uses `export function` syntax (same pattern as `table-formatters.js`)

### Requirement: Shared filter HTML partial
The system SHALL provide `_table_filter_panels.html` as a Jinja2 partial containing enum, range, and composite filter panel markup using Alpine.js `x-if` templates.

#### Scenario: Partial renders enum filter panel
- **WHEN** `_table_filter_panels.html` is included in a template with a column of type `enum`
- **THEN** the partial renders checkboxes for unique values with select-all option

#### Scenario: Partial renders range filter panel
- **WHEN** `_table_filter_panels.html` is included in a template with a column of type `range`
- **THEN** the partial renders dual range sliders with min/max inputs and fill visualization

#### Scenario: Partial renders composite filter panel
- **WHEN** `_table_filter_panels.html` is included in a template with a column of type `composite`
- **THEN** the partial renders multiple range slider sections (one per range key)

### Requirement: Rebalance page consumes shared module
The system SHALL replace inline filter JS in `rebalance.html` with imports from `table-filters.js`. Alpine method signatures in `window.rebalancePage` SHALL remain identical.

#### Scenario: Rebalance filter methods delegate to shared module
- **WHEN** `filterActive(column)` is called on the rebalance Alpine component
- **THEN** it delegates to the shared `filterActive` function with `this.plan.asset_plan` as rows source

#### Scenario: Rebalance filteredRows getter uses shared module
- **WHEN** `filteredRows` is accessed on the rebalance Alpine component
- **THEN** it delegates to `computeFilteredRows` with current filter state and returns the same filtered row set

### Requirement: Rebalance plan template uses shared HTML partial
The system SHALL replace inline filter panel HTML in `_rebalance_plan.html` (lines 100-166) with an include of `_table_filter_panels.html`.

#### Scenario: Filter panels render identically after refactor
- **WHEN** the rebalance page loads with filter panels
- **THEN** enum/range/composite panels render with same markup, classes, and Alpine bindings as before

### Requirement: PoC page consumes shared module
The system SHALL replace inline filter JS in `test/rebalance_table_poc.html` with imports from `table-filters.js`.

#### Scenario: PoC filter behavior unchanged
- **WHEN** filter operations are performed on the PoC page
- **THEN** results match the pre-refactor behavior exactly

### Requirement: Asset modal consumes shared module
The system SHALL replace inline filter JS in `_patrimonio_add_asset_modal.html` with imports from `table-filters.js`. Page-specific wrappers (`filterActiveStr`, `_mapField`) SHALL remain as local thin adapters.

#### Scenario: Asset modal filter behavior unchanged
- **WHEN** filter operations are performed on the asset modal import table
- **THEN** results match the pre-refactor behavior exactly

### Requirement: No behavioral change
The refactoring SHALL produce zero user-visible behavior changes. All existing tests SHALL continue to pass.

#### Scenario: Existing BDD scenarios pass
- **WHEN** `task test-bdd` is run
- **THEN** all scenarios pass without modification

#### Scenario: Existing e2e tests pass
- **WHEN** `task test-e2e` is run
- **THEN** all tests pass without modification
