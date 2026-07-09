## MODIFIED Requirements

### Requirement: Wire format exposes a v1 subset of the solver's native output

The system SHALL expose `RebalanceAssetPlanRow` with exactly these
twelve fields:

* `asset_key` (string, `Asset.name.casefold()`)
* `asset_name` (string, `Asset.name`)
* `category_name` (string, `AssetClass.name`)
* `current_value` (float, R$)
* `target_value` (float, R$)
* `buy_amount` (float, R$; `0.0` when no buy is recommended)
* `sell_amount` (float, R$; `0.0` when no sell is recommended)
* `trade_quantity` (float or null; quantity implied by buy/sell amount and
  current ticker price when the asset is tradeable)
* `projected_value` (float, R$)
* `action` (enum string: `"buy"`, `"sell"`, or `"hold"`)
* `deviation_value` (float, R$; `current_value - target_value`)
* `deviation_pct` (float, percentage 0-100; `0.0` when `target_value == 0`)

`trade_quantity` SHALL be derived from the non-zero movement side of the row:
`buy_amount / current_price` for buys or `sell_amount / current_price` for
sells when the asset price is denominated in BRL.

For assets with `currency_code = "USD"`, the system SHALL first convert the
BRL movement amount into USD using the same FX basis implied by the resolved
current ticker price before dividing by the USD ticker price.

For non-tradeable assets, hold rows, or rows without finite price, the system
SHALL expose `trade_quantity = null`.

#### Scenario: BRL buy row carries trade quantity

- **WHEN** a `RebalanceAssetPlanRow` is serialized for a BRL asset with
  `buy_amount = 1000` and current ticker price `20`
- **THEN** `trade_quantity` equals `50`

#### Scenario: BRL sell row carries trade quantity

- **WHEN** a `RebalanceAssetPlanRow` is serialized for a BRL asset with
  `sell_amount = 450` and current ticker price `15`
- **THEN** `trade_quantity` equals `30`

#### Scenario: USD row converts BRL amount before division

- **WHEN** a USD asset has current ticker price `10 USD`
- **AND** FX basis is `5.40 BRL/USD`
- **AND** `buy_amount = 540 BRL`
- **THEN** the system converts movement amount to `100 USD`
- **AND** `trade_quantity` equals `10`

#### Scenario: Non-tradeable row exposes null quantity

- **WHEN** an asset row represents a non-tradeable position or lacks finite
  current price
- **THEN** `trade_quantity` equals `null`
