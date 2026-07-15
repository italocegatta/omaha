## Why

The current buy/sell columns in the patrimônio asset table render text labels
"Liberado" / "Bloqueado" inside styled toggle buttons. The text occupies
significant horizontal space (each button is `min-width: 5.5rem`) and requires
the user to read rather than scan. Replacing the text with compact emoji
indicators (checkmark for allowed, lock for blocked) preserves the same
information density while recovering column width and improving scannability.

The toggle behavior (click → PATCH → visual flip) is already correct and
battle-tested across F15/F27/F28 cycles. This change is purely visual:
same backend contract, same Alpine binding, different inner content.

## What Changes

- **Asset table buy/sell cells**: Replace `<span x-text="Liberado/Bloqueado">`
  with emoji icons (✅ / 🔒 or similar Material Symbols glyphs). The button,
  its classes, data-testid, and `@click` handler stay identical.
- **Column header copy**: Keep "Compra" / "Venda" headers unchanged.
- **CSS `.trade-toggle`**: Adjust `min-width` and padding to suit emoji content
  instead of text. The color logic (`--on` / `--off`) stays.
- **Import modal**: No change — it uses a different toggle pattern
  (checkbox + "Sim"/"Não") that is out of scope.
- **Rebalance page**: No change — buy_amount/sell_amount are numeric columns,
  not trade flags.

## Capabilities

### New Capabilities

- `asset-trade-toggle-emoji`: Visual representation of per-asset buy/sell
  trade flags in the patrimônio asset table using emoji icons instead of
  text labels, while preserving the same click-to-toggle behavior and
  backend contract.

### Modified Capabilities

- `asset-trade-flags`: The "Dashboard renders inline per-asset
  trade-control toggles" requirement's visual representation changes
  from text labels to emoji icons. The behavioral contract (PATCH on
  click, disabled during flight, independent toggles) is unchanged.

## Impact

- **Templates**: `src/omaha/templates/_patrimonio_class_section.html`
  (buy/sell cell markup)
- **CSS**: `src/omaha/static/app.css` (`.trade-toggle` sizing)
- **Tests**: Existing `data-testid` selectors (`asset-buy-toggle`,
  `asset-sell-toggle`, `asset-buy-cell`, `asset-sell-cell`) are preserved;
  browser tests that assert on inner text "Liberado"/"Bloqueado" will
  need updated assertions.
- **No backend changes**: The PATCH contract, model, and API are unaffected.
