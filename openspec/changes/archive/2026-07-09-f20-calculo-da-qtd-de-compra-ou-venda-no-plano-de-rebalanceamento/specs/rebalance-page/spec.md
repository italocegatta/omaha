## MODIFIED Requirements

### Requirement: Asset plan table renders ten visible columns plus a data attribute

The system SHALL render the asset plan table with eleven visible `<th>`
cells: Classe, Ativo, Valor atual, Alvo, Desvio (R$), Desvio (%), Compra,
Venda, Qtd, Projetado, Ação. Each row carries a `data-asset-key`
attribute holding the wire's `asset_key` field (used by tests; not
visible to the operator).

The `Qtd` column SHALL appear immediately after `Venda`. It SHALL show
the calculated trade quantity only for assets with negociação em bolsa
and finite market price. Rows that are not tradeable or lack an apt
price SHALL render the `Qtd` cell empty without shifting the column map.

#### Scenario: Asset plan table has eleven visible columns

- **WHEN** the plan renders
- **THEN** the asset plan `<table>` has exactly eleven `<th>`
  elements in `<thead>`
- **AND** `Qtd` appears after `Venda` and before `Projetado`

#### Scenario: Buy row shows calculated quantity for BRL asset

- **WHEN** an asset plan row has `buy_amount = 1000`, `sell_amount = 0`,
  `trade_quantity = 50`, and BRL market price `20`
- **THEN** the `Compra` cell shows `R$ 1.000,00`
- **AND** the `Qtd` cell shows `50`

#### Scenario: Sell row shows calculated quantity for USD asset

- **WHEN** an asset plan row has `sell_amount = 540`, `trade_quantity = 20`,
  and USD market price `27`
- **THEN** the `Venda` cell shows `R$ 540,00`
- **AND** the `Qtd` cell shows `20`

#### Scenario: Non-tradeable row leaves quantity blank

- **WHEN** an asset row is not eligible for exchange trading quantity
- **THEN** the `Qtd` cell renders empty
- **AND** the remaining columns preserve their positions
