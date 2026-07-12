## MODIFIED Requirements

### Requirement: Compact parameter bar

The system SHALL render a parameter bar above the class summary with three inline inputs (not full-width):
1. Aporte (R$) input — `data-testid="rebalance-contribution-input"`
2. Desvio mínimo (R$) input — `data-testid="rebalance-threshold-abs"`
3. Desvio mínimo (%) input — `data-testid="rebalance-threshold-pct"`

The bar uses `data-testid="rebalance-params-bar"`.

Threshold inputs SHALL be real form fields submitted with the page request. When the page first loads or the caller omits the threshold values, the rendered defaults SHALL be `1000` and `1`. The rendered plan SHALL reflect the submitted thresholds, not only client-side color-coding. The bar SHALL NOT render a visible manual submit button.

#### Scenario: Parameter bar renders inline inputs without manual button

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-params-bar"` contains the aporte input and two threshold inputs
- **AND** `data-testid="rebalance-submit-btn"` is not rendered

#### Scenario: Threshold defaults are 1000 and 1

- **WHEN** the page loads without explicit threshold values
- **THEN** `data-testid="rebalance-threshold-abs"` has value `1000`
- **AND** `data-testid="rebalance-threshold-pct"` has value `1`

### Requirement: Client-side validation rejects negative aporte

The system SHALL block form submission when `contribution < 0` on the client side, displaying an inline error before any POST round-trip. Server-side accepts negative (per the `rebalance-route` contract extension), but the page UI is more restrictive for v1.

The error renders inside the in-body form (no sidebar element exists any more; see `dashboard-sidebar` REMOVED delta).

#### Scenario: Negative aporte shows client error before form submit

- **WHEN** the user types `-1000` in the aporte input
- **THEN** the form does NOT trigger a POST round-trip
- **AND** an element with `data-testid="rebalance-form-error"` (in-body, not `sidebar-form-error`) shows the message
  "Saques serão suportados em versão futura. Por enquanto, deixe o aporte em zero ou positivo."

## ADDED Requirements

### Requirement: Rebalance inputs submit plan on Enter

The system SHALL keep rebalance input edits local while operator types. It SHALL refresh plan only when operator presses Enter in aporte or threshold input with valid values. Refresh SHALL reuse existing `POST /rebalanceamento` render path and SHALL not require clicking visible manual submit button.

#### Scenario: Enter submits edited aporte

- **WHEN** page is showing rebalance plan
- **AND** operator changes `contribution` from `5000` to `6000`
- **THEN** page does not issue rebalance request while operator is typing
- **WHEN** operator presses Enter
- **THEN** page issues new rebalance request without button click
- **AND** the rendered plan reflects `metrics.contribution = 6000`
