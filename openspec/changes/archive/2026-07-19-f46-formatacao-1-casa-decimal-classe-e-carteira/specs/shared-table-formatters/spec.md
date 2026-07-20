## MODIFIED Requirements

### Requirement: Numeric formatting functions
The module SHALL export pure functions for formatting numeric values as localized strings:
- `formatMoney(value, currency)` — formats as currency with `pt-BR` locale. `currency` defaults to `'BRL'`. Uses `narrowSymbol` currency display. Returns `'—'` for null/undefined/NaN. Minimum 0, maximum 0 fraction digits.
- `formatPct(value)` — formats as `X.XX%`. Returns `'—'` for null/undefined/NaN.
- `formatPctRounded(value, decimals)` — formats as percentage rounded to `decimals` decimal places (default 0). Returns `'—'` for null/undefined/NaN.
- `formatQty(value, assetName)` — formats quantity with `pt-BR` locale. BTC assets get 3 fraction digits; all others get 0. Returns `'—'` for null/undefined/NaN.
- `formatDeviationPp(value, decimals)` — formats as `+X%` or `-X%` with explicit sign, rounded to `decimals` decimal places (default 0). Returns `'0%'` for zero.

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

#### Scenario: formatPctRounded with default decimals
- **WHEN** `formatPctRounded(12.7)` is called
- **THEN** returns `'13%'` (0 decimals by default)

#### Scenario: formatPctRounded with 1 decimal
- **WHEN** `formatPctRounded(12.73, 1)` is called
- **THEN** returns `'12.7%'`

#### Scenario: formatPctRounded with null and decimals
- **WHEN** `formatPctRounded(null, 1)` is called
- **THEN** returns `'—'`

#### Scenario: formatQty for BTC
- **WHEN** `formatQty(0.12345678, 'BTC')` is called
- **THEN** returns `'0,123'` (3 fraction digits)

#### Scenario: formatQty for non-BTC
- **WHEN** `formatQty(100, 'PETR4')` is called
- **THEN** returns `'100'` (0 fraction digits)

#### Scenario: formatDeviationPp positive with default decimals
- **WHEN** `formatDeviationPp(5.3)` is called
- **THEN** returns `'+5%'` (0 decimals by default)

#### Scenario: formatDeviationPp negative with default decimals
- **WHEN** `formatDeviationPp(-3.1)` is called
- **THEN** returns `'-3%'` (0 decimals by default)

#### Scenario: formatDeviationPp with 1 decimal
- **WHEN** `formatDeviationPp(5.37, 1)` is called
- **THEN** returns `'+5.4%'`

#### Scenario: formatDeviationPp negative with 1 decimal
- **WHEN** `formatDeviationPp(-3.12, 1)` is called
- **THEN** returns `'-3.1%'`
