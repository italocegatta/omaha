## ADDED Requirements

### Requirement: Numeric formatting functions
The module SHALL export pure functions for formatting numeric values as localized strings:
- `formatMoney(value, currency)` — formats as currency with `pt-BR` locale. `currency` defaults to `'BRL'`. Uses `narrowSymbol` currency display. Returns `'—'` for null/undefined/NaN. Minimum 0, maximum 0 fraction digits.
- `formatPct(value)` — formats as `X.XX%`. Returns `'—'` for null/undefined/NaN.
- `formatPctRounded(value)` — formats as `X%` (rounded to 0 decimals). Returns `'—'` for null/undefined/NaN.
- `formatQty(value, assetName)` — formats quantity with `pt-BR` locale. BTC assets get 3 fraction digits; all others get 0. Returns `'—'` for null/undefined/NaN.
- `formatDeviationPp(value)` — formats as `+X%` or `-X%` (0 decimals, explicit sign). Returns `'0%'` for zero.

#### Scenario: formatMoney with BRL
- **WHEN** `formatMoney(1234.56)` is called
- **THEN** returns `'R$\u00a01.235'` (pt-BR locale, narrowSymbol, 0 decimals)

#### Scenario: formatMoney with USD
- **WHEN** `formatMoney(1234.56, 'USD')` is called
- **THEN** returns `'US$\u00a01.235'` (pt-BR locale, narrowSymbol, 0 decimals)

#### Scenario: formatMoney with null
- **WHEN** `formatMoney(null)` is called
- **THEN** returns `'—'`

#### Scenario: formatPct with value
- **WHEN** `formatPct(12.345)` is called
- **THEN** returns `'12.35%'`

#### Scenario: formatPctRounded with value
- **WHEN** `formatPctRounded(12.7)` is called
- **THEN** returns `'13%'`

#### Scenario: formatQty for BTC
- **WHEN** `formatQty(0.12345678, 'BTC')` is called
- **THEN** returns `'0,123'` (3 fraction digits)

#### Scenario: formatQty for non-BTC
- **WHEN** `formatQty(100, 'PETR4')` is called
- **THEN** returns `'100'` (0 fraction digits)

#### Scenario: formatDeviationPp positive
- **WHEN** `formatDeviationPp(5.3)` is called
- **THEN** returns `'+5%'`

#### Scenario: formatDeviationPp negative
- **WHEN** `formatDeviationPp(-3.1)` is called
- **THEN** returns `'-3%'`

### Requirement: Sign logic functions
The module SHALL export pure functions for determining visual sign representation:
- `signClass(value)` — returns `'metric-positive'` if value > 0.0001, `'metric-negative'` if value < -0.0001, `'metric-neutral'` otherwise (including null/undefined/NaN/zero).
- `signIcon(value)` — returns `'arrow_upward'` if value > 0.0001, `'arrow_downward'` if value < -0.0001, `'remove'` otherwise.

#### Scenario: signClass positive
- **WHEN** `signClass(5.5)` is called
- **THEN** returns `'metric-positive'`

#### Scenario: signClass negative
- **WHEN** `signClass(-3.2)` is called
- **THEN** returns `'metric-negative'`

#### Scenario: signClass zero
- **WHEN** `signClass(0)` is called
- **THEN** returns `'metric-neutral'`

#### Scenario: signClass null
- **WHEN** `signClass(null)` is called
- **THEN** returns `'metric-neutral'`

#### Scenario: signIcon positive
- **WHEN** `signIcon(1.5)` is called
- **THEN** returns `'arrow_upward'`

#### Scenario: signIcon negative
- **WHEN** `signIcon(-0.5)` is called
- **THEN** returns `'arrow_downward'`

#### Scenario: signIcon null
- **WHEN** `signIcon(null)` is called
- **THEN** returns `'remove'`

### Requirement: Row and cell formatting functions
The module SHALL export functions for table row and cell presentation:
- `actionLabel(action)` — returns `'Comprar'` for `'buy'`, `'Vender'` for `'sell'`, `'Manter'` otherwise.
- `rowClass(row)` — returns `'rebalance-asset-row--neutral'` for hold, `'rebalance-asset-row--buy'` for buy, `'rebalance-asset-row--sell'` for sell.
- `cellClass(row, column)` — returns CSS class string based on column type and row data. Numeric columns get `'rebalance-asset-cell--num'`. Action columns get `'rebalance-asset-cell--action'`. Deviation columns get sign-based class.
- `formatCell(row, column, formatters)` — returns formatted cell value based on column configuration. Delegates to appropriate formatter based on `column.cellFormat`, `column.key`, and `column.type`.

#### Scenario: actionLabel for buy
- **WHEN** `actionLabel('buy')` is called
- **THEN** returns `'Comprar'`

#### Scenario: rowClass for hold
- **WHEN** `rowClass({action: 'hold'})` is called
- **THEN** returns `'rebalance-asset-row--neutral'`

#### Scenario: cellClass for numeric column
- **WHEN** `cellClass(row, {type: 'range', key: 'deviation_value'})` is called
- **THEN** returns string containing `'rebalance-asset-cell--num'`

#### Scenario: formatCell for action column
- **WHEN** `formatCell({action: 'buy'}, {key: 'action', type: 'enum'})` is called
- **THEN** returns `'Comprar'`

### Requirement: Module export format
The module SHALL be a standard ES module at `static/table-formatters.js` exporting all functions as named exports. The module SHALL have zero dependencies (pure functions only).

#### Scenario: Module loads as ES module
- **WHEN** the browser loads `static/table-formatters.js` via `<script type="module">`
- **THEN** all exported functions are available for import

#### Scenario: Module has no side effects
- **WHEN** the module is loaded
- **THEN** no global state is modified and no DOM mutations occur
