## MODIFIED Requirements

### Requirement: POST /api/rebalance returns a RebalancePlanResponse

The wire format extends with 5 new computed fields. Existing fields
are unchanged. New fields are additive — no breaking change.

#### Scenario: Category plan row carries percentage and deviation fields

- **WHEN** a `RebalanceCategoryPlanRow` is serialized
- **THEN** the JSON object has the keys
  `category_name, current_value, projected_value, delta,
  target_pct, current_pct, deviation_pct`
- **AND** `target_pct` equals the class's target weight as a
  percentage of total portfolio value (0–100)
- **AND** `current_pct` equals the class's current weight as a
  percentage of total portfolio value (0–100)
- **AND** `deviation_pct` equals `current_pct - target_pct`

#### Scenario: Asset plan row carries deviation fields

- **WHEN** a `RebalanceAssetPlanRow` is serialized
- **THEN** the JSON object has the keys
  `asset_key, asset_name, category_name, current_value, target_value,
  buy_amount, sell_amount, projected_value, action,
  deviation_value, deviation_pct`
- **AND** `deviation_value` equals `current_value - target_value`
- **AND** `deviation_pct` equals
  `(current_value - target_value) / target_value * 100` when
  `target_value != 0`, else `0.0`

#### Scenario: Deviation fields are zero when target is zero

- **WHEN** an asset has `target_value = 0` and `current_value = 100`
- **THEN** `deviation_pct` equals `0.0` (avoids division by zero)
- **AND** `deviation_value` equals `100.0`

#### Scenario: Category percentage fields sum correctly

- **WHEN** the portfolio has 3 categories with current values
  4200, 2800, 3000 (total 10000)
- **THEN** `current_pct` values are 42.0, 28.0, 30.0
- **AND** `target_pct` values sum to 100.0
