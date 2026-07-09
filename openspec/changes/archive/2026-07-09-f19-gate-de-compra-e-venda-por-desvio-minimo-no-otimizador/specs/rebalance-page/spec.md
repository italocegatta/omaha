## MODIFIED Requirements

### Requirement: Compact parameter bar

The system SHALL render a parameter bar above the class summary with
four inline elements (not full-width):
1. Aporte (R$) input — `data-testid="rebalance-contribution-input"`
2. Desvio mínimo (R$) input — `data-testid="rebalance-threshold-abs"`
3. Desvio mínimo (%) input — `data-testid="rebalance-threshold-pct"`
4. Rebalancear button — `data-testid="rebalance-submit-btn"`

The bar uses `data-testid="rebalance-params-bar"`.

Threshold inputs SHALL be real form fields submitted with the page request. When
the page first loads or the caller omits the threshold values, the rendered
defaults SHALL be `1000` and `1`. The rendered plan SHALL reflect the submitted
thresholds, not only client-side color-coding.

#### Scenario: Parameter bar renders all four elements inline

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-params-bar"` contains the aporte
  input, two threshold inputs, and the submit button

#### Scenario: Threshold defaults are 1000 and 1

- **WHEN** the page loads without explicit threshold values
- **THEN** `data-testid="rebalance-threshold-abs"` has value `1000`
- **AND** `data-testid="rebalance-threshold-pct"` has value `1`

#### Scenario: Threshold fields submit with the form

- **WHEN** the operator posts aporte `5000`, threshold abs `2500`, and
  threshold pct `2`
- **THEN** the rendered plan reflects those threshold values
- **AND** rows below either threshold render as non-actionable hold rows

## ADDED Requirements

### Requirement: Threshold gate affects rendered execution suggestions

The system SHALL render `Compra`, `Venda`, `Projetado`, and `Ação` from the
server-gated plan. An asset row that fails either minimum threshold SHALL render
as a hold row with zero buy/sell suggestion even if the ungated optimizer would
have moved capital through that asset.

#### Scenario: Small buy recommendation is hidden by threshold gate

- **WHEN** the plan contains an asset with ungated `buy_amount = 600`,
  `deviation_value = 600`, `deviation_pct = 2.0`, and the active thresholds are
  `1000` and `1`
- **THEN** the rendered row shows `Compra = R$ 0,00`
- **AND** the action badge is `Manter`

#### Scenario: Material recommendation stays visible

- **WHEN** the plan contains an asset with `sell_amount = 3500`,
  `deviation_value = 3500`, `deviation_pct = 2.4`, and the active thresholds are
  `1000` and `1`
- **THEN** the rendered row still shows the sell recommendation
- **AND** the action badge is `Vender`
