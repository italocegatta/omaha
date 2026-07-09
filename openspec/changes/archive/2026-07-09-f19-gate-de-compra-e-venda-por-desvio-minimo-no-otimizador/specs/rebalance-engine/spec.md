## ADDED Requirements

### Requirement: Operator thresholds suppress sub-material trades in final plan

The system SHALL accept two operator thresholds during rebalance plan assembly:

- `min_deviation_value` (float, R$, default `1000.0`)
- `min_deviation_pct` (float, percentage, default `1.0`)

After the solver produces the native plan, post-processing SHALL evaluate each
tradeable asset row against its absolute deviation (`abs(current_value -
target_value)`) and percentual deviation (`abs((current_value - target_value) /
target_value * 100)` when `target_value > 0`, otherwise `0`).

If either deviation is below its minimum threshold, the system SHALL suppress
the trade by setting `buy_amount = 0`, `sell_amount = 0`, and
`projected_value = current_value` for that asset row. The system SHALL then
recompute category projected totals, portfolio projected totals, aggregate buy /
sell metrics, residual cash, and any downstream action derivation from the gated
rows.

Existing hard locks (`buy_enabled`, `sell_enabled`, non-tradeable sentinels)
SHALL remain in force before threshold gating; the threshold gate SHALL never
re-enable a locked trade.

#### Scenario: Row below absolute threshold is suppressed

- **WHEN** a solved asset row has `deviation_value = 600`, `deviation_pct = 2.5`,
  `buy_amount = 600`, `min_deviation_value = 1000`, and
  `min_deviation_pct = 1`
- **THEN** the final plan sets `buy_amount = 0` for that row
- **AND** the row's `projected_value` equals `current_value`

#### Scenario: Row below percentual threshold is suppressed

- **WHEN** a solved asset row has `deviation_value = 5000`,
  `deviation_pct = 0.4`, `sell_amount = 5000`, `min_deviation_value = 1000`,
  and `min_deviation_pct = 1`
- **THEN** the final plan sets `sell_amount = 0` for that row
- **AND** the row's `projected_value` equals `current_value`

#### Scenario: Row must clear both thresholds to remain actionable

- **WHEN** a solved asset row has `deviation_value = 2500`, `deviation_pct = 1.8`,
  and thresholds `min_deviation_value = 1000`, `min_deviation_pct = 1`
- **THEN** the final plan keeps the solved buy/sell amount for that row

#### Scenario: Suppression recomputes aggregate plan metrics

- **WHEN** two solved buy rows are suppressed by threshold gating after the LP
  finishes
- **THEN** the final plan's `total_buy`, `projected_value` totals, and
  `residual_cash` reflect only non-suppressed rows
