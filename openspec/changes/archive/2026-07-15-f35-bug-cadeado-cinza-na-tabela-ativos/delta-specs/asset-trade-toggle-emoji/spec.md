# asset-trade-toggle-emoji (delta — F35 correction)

## Purpose

Corrigir o bug do cadeado cinza nos toggles de compra/venda. O estado `--off`
usava cinza neutro em vez de cores semânticas (vermelho para compra bloqueada,
verde para venda bloqueada).

## Changes to asset-trade-toggle-emoji

### Modified: Buy toggle off-state color

The buy toggle off-state SHALL render the `lock` icon with red (negative)
styling, not grey/neutral.

#### Scenario: Buy disabled shows red lock

- **WHEN** an asset has `buy_enabled=false`
- **THEN** the buy toggle cell renders a `lock` Material Symbols Outlined
  icon with `.trade-toggle--off` styling using `--negative` color tokens
  (background, border, text)

### Modified: Sell toggle off-state color

The sell toggle off-state SHALL render the `lock` icon with green (positive)
styling, not grey/neutral. This represents "venda bloqueada" (position
protected).

#### Scenario: Sell disabled shows green lock

- **WHEN** an asset has `sell_enabled=false`
- **THEN** the sell toggle cell renders a `lock` Material Symbols Outlined
  icon with `.trade-toggle--sell.trade-toggle--off` styling using
  `--positive` color tokens (background, border, text)

### Unchanged: Buy toggle on-state

#### Scenario: Buy enabled shows green check_circle (unchanged)

- **WHEN** an asset has `buy_enabled=true`
- **THEN** the buy toggle renders `check_circle` with green (positive) styling
  — no change from base spec

### Unchanged: Sell toggle on-state

#### Scenario: Sell enabled shows red check_circle (unchanged)

- **WHEN** an asset has `sell_enabled=true`
- **THEN** the sell toggle renders `check_circle` with red (negative) styling
  — no change from base spec
