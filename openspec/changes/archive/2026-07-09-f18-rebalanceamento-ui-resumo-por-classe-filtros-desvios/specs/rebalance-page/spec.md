## MODIFIED Requirements

### Requirement: Six metric cards in a 3×2 grid

**Reason**: Replaced by class deviation summary cards and compact parameter bar.
**Migration**: The 6 `data-testid="rebalance-stat-*"` elements are removed.
Tests referencing them must be updated to use the new class-card and
params-bar testids.

### Requirement: Category summary table renders four columns

The system SHALL render the category deviation summary as horizontal
cards (not a table). Each card displays: class name, current weight
(%), target weight (%), deviation in percentage points, deviation in
R$, projected weight (%), and projected deviation (pp). Each card
carries `data-testid="rebalance-class-card-{category_name}"`.

The card container SHALL use `data-testid="rebalance-class-summary"`
and be a horizontal flex container with `overflow-x: auto`.

Color coding: the card SHALL apply
`rebalance-class-card--ok` when `|deviation_pct| < threshold_pct`,
`rebalance-class-card--over` when `|deviation_pct| >= threshold_pct`.
Threshold defaults: `thresholdPct = 1.0` (editable via params bar).

#### Scenario: Class cards render one per AssetClass

- **WHEN** the plan renders with 3 categories
- **THEN** three elements with `data-testid="rebalance-class-card-*"`
  are visible inside `data-testid="rebalance-class-summary"`

#### Scenario: Class card shows current, target, deviation, projected

- **WHEN** a category has `current_pct = 42.0`, `target_pct = 40.0`,
  `deviation_pct = 2.0`, `projected_pct = 40.1`
- **THEN** the card displays "Atual 42.0%", "Alvo 40.0%", "+2.0 pp",
  and "Projetado 40.1%"

#### Scenario: Class card color codes by threshold

- **WHEN** a category has `|deviation_pct| >= threshold_pct`
- **THEN** the card has class `rebalance-class-card--over`
- **WHEN** a category has `|deviation_pct| < threshold_pct`
- **THEN** the card has class `rebalance-class-card--ok`

### Requirement: Asset plan table renders eight visible columns plus a data attribute

The system SHALL render the asset plan table with ten visible `<th>`
cells: Ativo, Classe, Valor atual, Alvo, Desvio (R$), Desvio (%),
Compra, Venda, Projetado, Ação. Each row carries a `data-asset-key`
attribute holding the wire's `asset_key` field.

All ten columns SHALL be sortable. Default sort: by `category_name`
asc, then `asset_name` asc.

#### Scenario: Asset plan table has ten visible columns

- **WHEN** the plan renders
- **THEN** the asset plan `<table>` has exactly ten `<th>`
  elements in `<thead>`
- **AND** each `<tbody> <tr>` has the
  `data-asset-key="..."` attribute matching the row's
  `asset_key`

#### Scenario: Desvio columns show deviation values

- **WHEN** an asset has `current_value = 5000`, `target_value = 5500`
- **THEN** the Desvio (R$) cell shows `-R$ 500,00`
- **AND** the Desvio (%) cell shows `-9.1%`

### Requirement: Asset table column filters

The system SHALL render a filter bar above the asset table with:
- A multi-select checkbox dropdown for `Classe` (lists all unique
  `category_name` values from the asset plan). Default: all selected.
  Carries `data-testid="rebalance-filter-class"`.
- A multi-select checkbox dropdown for `Ação` (Comprar, Vender, Manter).
  Default: all selected. Carries `data-testid="rebalance-filter-action"`.
- A text search input for asset name. Carries
  `data-testid="rebalance-filter-search"`.

When a filter is active, only matching rows are visible. The filter
operates client-side (Alpine computed, no server round-trip).

#### Scenario: Filtering by class shows only matching assets

- **WHEN** the operator deselects all classes except "Ações BR"
- **THEN** only assets with `category_name = "Ações BR"` are visible
  in the table

#### Scenario: Filtering by action shows only matching assets

- **WHEN** the operator selects only "Comprar"
- **THEN** only assets with `action = "buy"` are visible

#### Scenario: Text search filters by asset name

- **WHEN** the operator types "PETR" in the search input
- **THEN** only assets whose `asset_name` contains "PETR"
  (case-insensitive) are visible

#### Scenario: Filters compose (AND logic)

- **WHEN** class filter is "Ações BR" AND action filter is "Comprar"
- **THEN** only assets matching BOTH criteria are visible

### Requirement: Compact parameter bar

The system SHALL render a parameter bar above the class summary with
four inline elements (not full-width):
1. Aporte (R$) input — `data-testid="rebalance-contribution-input"`
   (preserves existing testid)
2. Desvio mínimo (R$) input — `data-testid="rebalance-threshold-abs"`,
   default value `1000`
3. Desvio mínimo (%) input — `data-testid="rebalance-threshold-pct"`,
   default value `1`
4. Rebalancear button — `data-testid="rebalance-submit-btn"`
   (preserves existing testid)

The bar uses `data-testid="rebalance-params-bar"`.

Threshold inputs are Alpine reactive state (`thresholdAbs`, `thresholdPct`),
not form fields. They affect visual color-coding only. The Rebalancear
button submits the form (POST) as before.

#### Scenario: Parameter bar renders all four elements inline

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-params-bar"` contains the aporte
  input, two threshold inputs, and the submit button

#### Scenario: Threshold defaults are 1000 and 1

- **WHEN** the page loads
- **THEN** `data-testid="rebalance-threshold-abs"` has value `1000`
- **AND** `data-testid="rebalance-threshold-pct"` has value `1`

#### Scenario: Changing threshold updates class card colors

- **WHEN** the operator changes desvio mínimo (%) to `5`
- **THEN** class cards with `|deviation_pct| < 5` switch to `--ok`
- **AND** class cards with `|deviation_pct| >= 5` switch to `--over`

### Requirement: Row color-coding by deviation

The system SHALL color asset table rows based on deviation vs threshold:
- `rebalance-asset-row--over`: `|deviation_pct| >= threshold_pct` OR
  `|deviation_value| >= thresholdAbs`
- `rebalance-asset-row--ok`: deviation within threshold
- `rebalance-asset-row--neutral`: action is `hold` (no deviation color)

#### Scenario: Over-threshold row gets red tint

- **WHEN** an asset has `deviation_pct = -9.1` and `threshold_pct = 1`
- **THEN** the row has class `rebalance-asset-row--over`

#### Scenario: Within-threshold row gets green tint

- **WHEN** an asset has `deviation_pct = 0.5` and `threshold_pct = 1`
- **THEN** the row has class `rebalance-asset-row--ok`

#### Scenario: Hold row gets neutral treatment

- **WHEN** an asset has `action = "hold"`
- **THEN** the row has class `rebalance-asset-row--neutral`

## REMOVED Requirements

### Requirement: Six metric cards in a 3×2 grid

**Reason**: Replaced by class deviation summary cards (more actionable
information per card) and compact parameter bar (aporte + thresholds).
**Migration**: Remove references to `data-testid="rebalance-stat-*"`.
New testids: `rebalance-class-card-*`, `rebalance-params-bar`.
