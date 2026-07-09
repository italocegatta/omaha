## 1. Wire format and calculation

- [x] 1.1 Locate current rebalance row assembly path and identify reliable price/currency inputs for trade quantity.
- [x] 1.2 Add `trade_quantity` to rebalance schema/wire mapping for asset rows.
- [x] 1.3 Implement BRL quantity calculation from non-zero buy/sell amount and current ticker price.
- [x] 1.4 Implement USD conversion before division and return `null` for non-tradeable or non-finite-price rows.

## 2. Rebalance page rendering

- [x] 2.1 Add `Qtd` header after `Venda` in `_rebalance_plan.html`.
- [x] 2.2 Render calculated quantity for eligible rows and blank cell for ineligible rows without breaking sort/filter behavior.

## 3. Verification

- [x] 3.1 Add or update tests for BRL quantity, USD quantity conversion, and null quantity cases.
- [x] 3.2 Update page/render assertions for 11-column table and `Qtd` placement.
- [x] 3.3 Run targeted rebalance tests, lint, and OpenSpec spec verification.
