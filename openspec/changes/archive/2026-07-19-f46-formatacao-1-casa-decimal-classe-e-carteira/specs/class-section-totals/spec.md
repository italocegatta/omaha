## MODIFIED Requirements

### Requirement: Asset table numeric values use compact precision

The system SHALL render monetary cells in the asset table with 0 decimal places. The `Qtd` column SHALL render with 0 decimal places for all assets except BTC, which SHALL render with 3 decimal places. Its range-filter labels SHALL retain that BTC precision when their value belongs to BTC. Percentage values in `Ganho` SHALL render with 0 decimal places. Percentage values in `Classe / Atual`, `Classe / Alvo`, `Classe / Desvio`, `Carteira / Atual`, `Carteira / Alvo`, and `Carteira / Desvio` SHALL render with 1 decimal place. A rounded value whose magnitude is below one whole percentage point SHALL render as `0%`, never `-0%`. Exact numeric zero SHALL also render as `0%`; `—` is reserved for absent or invalid values.

#### Scenario: BTC quantity keeps 3 decimal places

- **WHEN** an asset row has `asset_name = BTC` and `qty = 1.23456`
- **THEN** the `Qtd` cell renders with 3 decimal places
- **AND** the other monetary cells on the row remain compact with 0 decimal places

#### Scenario: Non-BTC quantity rounds to 0 decimals

- **WHEN** an asset row has `asset_name = PETR4` and `qty = 12.7`
- **THEN** the `Qtd` cell renders with 0 decimal places

#### Scenario: BTC quantity range label keeps precision

- **WHEN** a `Qtd` range-filter boundary belongs to `asset_name = BTC` with `qty = 1.23`
- **THEN** its range label renders as `1,230`

#### Scenario: Rounded negative percentage near zero is normalized

- **WHEN** a requested percentage cell has a value of `-0.4`
- **THEN** it renders as `0%`

#### Scenario: Exact zero target remains a percentage

- **WHEN** `Classe / Alvo` or `Carteira / Alvo` has exact numeric value `0`
- **THEN** it renders as `0%`
- **AND** it does not render as `—`

#### Scenario: Classe and Carteira columns use 1 decimal place

- **WHEN** an asset row includes percentage values with fractional precision
- **THEN** `Classe / Atual`, `Classe / Alvo`, `Classe / Desvio`, `Carteira / Atual`, `Carteira / Alvo`, and `Carteira / Desvio` render with 1 decimal place
- **AND** `Ganho` renders with 0 decimal places

#### Scenario: Class totals row Carteira columns use 1 decimal place

- **WHEN** the dashboard renders a class totals row
- **THEN** `data-testid="class-total-current-pct-portfolio"` renders with 1 decimal place (e.g. `23.5%`)
- **AND** `data-testid="class-total-deviation-portfolio"` renders with 1 decimal place (e.g. `+1.2%`)

#### Scenario: Class totals row Classe Desvio uses 1 decimal place

- **GIVEN** a class whose `classDeviationPctClass` is `+3.56`
- **WHEN** the dashboard renders the class totals row
- **THEN** the cell `data-testid="class-total-deviation-class"` renders `+3.6%` (1 decimal place)
- **AND** the cell carries the `metric-positive` class
