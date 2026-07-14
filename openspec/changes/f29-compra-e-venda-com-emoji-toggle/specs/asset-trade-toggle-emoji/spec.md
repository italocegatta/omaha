# asset-trade-toggle-emoji

## Purpose

Define the visual representation of per-asset buy/sell trade-flag toggles
in the patrimônio asset table using Material Symbols Outlined icons instead
of text labels. The toggle behavior (click → PATCH → visual flip) is
inherited from `asset-trade-flags` and is unchanged.

## ADDED Requirements

### Requirement: Buy toggle shows check_circle or lock icon

The system SHALL render the buy-enabled toggle as a `<button>` containing
a Material Symbols Outlined icon: `check_circle` when `buy_enabled` is
true, `lock` when false. The button SHALL use the existing
`.trade-toggle--on` / `.trade-toggle--off` CSS classes for color coding.

#### Scenario: Buy enabled shows check_circle

- **WHEN** an asset has `buy_enabled=true`
- **THEN** the buy toggle cell renders a `check_circle` Material Symbols
  Outlined icon with the `.trade-toggle--on` (green) styling

#### Scenario: Buy disabled shows lock

- **WHEN** an asset has `buy_enabled=false`
- **THEN** the buy toggle cell renders a `lock` Material Symbols Outlined
  icon with the `.trade-toggle--off` (red) styling

### Requirement: Sell toggle shows check_circle or lock icon

The system SHALL render the sell-enabled toggle as a `<button>` containing
a Material Symbols Outlined icon: `check_circle` when `sell_enabled` is
true, `lock` when false. The button SHALL use the existing
`.trade-toggle--on` / `.trade-toggle--off` CSS classes for color coding.

#### Scenario: Sell enabled shows check_circle

- **WHEN** an asset has `sell_enabled=true`
- **THEN** the sell toggle cell renders a `check_circle` Material Symbols
  Outlined icon with the `.trade-toggle--on` (green) styling

#### Scenario: Sell disabled shows lock

- **WHEN** an asset has `sell_enabled=false`
- **THEN** the sell toggle cell renders a `lock` Material Symbols Outlined
  icon with the `.trade-toggle--off` (red) styling

### Requirement: Toggle buttons carry aria-label for accessibility

Each buy/sell toggle button SHALL carry an `aria-label` attribute that
announces the field and state in Portuguese. Format:
`<Campo>: <Estado>` where Campo is "Compra" or "Venda" and Estado is
"Liberado" or "Bloqueado".

#### Scenario: Buy enabled aria-label

- **WHEN** an asset has `buy_enabled=true`
- **THEN** the buy toggle button has `aria-label="Compra: Liberado"`

#### Scenario: Sell disabled aria-label

- **WHEN** an asset has `sell_enabled=false`
- **THEN** the sell toggle button has `aria-label="Venda: Bloqueado"`

### Requirement: Toggle button sizing adapts to icon content

The `.trade-toggle` CSS class SHALL use a reduced `min-width` suitable
for icon content (approximately `2rem`) instead of the text-label width
(`5.5rem`). The button SHALL retain padding, border-radius, and
focus-visible outline from the existing `.trade-toggle` rules.

#### Scenario: Toggle button is compact

- **WHEN** the asset table renders buy/sell columns
- **THEN** each toggle button is narrower than the pre-F29 text-label
  version, recovering horizontal space in the table

### Requirement: Preserved testids and click handlers

The system SHALL preserve all existing `data-testid` attributes
(`asset-buy-toggle`, `asset-buy-cell`, `asset-sell-toggle`,
`asset-sell-cell`) and the `@click` handler (`toggleTradeFlag`)
on the same elements. The change MUST be limited to the inner
`<span>` content and button sizing.

#### Scenario: Buy toggle testid preserved

- **WHEN** a test queries `[data-testid="asset-buy-toggle"]`
- **THEN** exactly one element matches per asset row, same as pre-F29

#### Scenario: Sell toggle testid preserved

- **WHEN** a test queries `[data-testid="asset-sell-toggle"]`
- **THEN** exactly one element matches per asset row, same as pre-F29
