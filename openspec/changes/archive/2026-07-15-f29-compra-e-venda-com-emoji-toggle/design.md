## Context

The patrimônio asset table has two columns — "Compra" and "Venda" — that show
per-asset trade-flag state. Currently each cell renders a `<button>` with text
"Liberado" (green) or "Bloqueado" (red) via `.trade-toggle--on` /
`.trade-toggle--off` CSS classes. The button is `min-width: 5.5rem` to fit the
text, consuming significant horizontal space in an already dense table (14
columns post-F28).

The toggle behavior (click → `toggleTradeFlag` → PATCH → visual flip) is
stable and tested. The change is scoped to the inner content of the button
and its sizing.

## Goals / Non-Goals

**Goals:**
- Replace text labels with compact emoji/icon representation
- Recover column width (shrink buy/sell columns)
- Preserve all existing `data-testid` attributes and click handlers
- Keep the color semantics (green = on, red = off)

**Non-Goals:**
- Changing the import modal's checkbox-based buy/sell toggles (different pattern)
- Changing the rebalance page's buy_amount/sell_amount columns (numeric, not flags)
- Modifying the PATCH API contract or model
- Adding bulk toggle capability

## Decisions

### D1 — Use Material Symbols Outlined icons, not Unicode emoji

The app already loads `Material+Symbols+Outlined` (base.html:24) and uses
`.icon--sm` / `.icon--md` classes. Using `check_circle` (on) and `lock` (off)
is consistent with the existing icon language. Unicode emoji (✅/🔒) would work
but render inconsistently across OS/browsers and don't inherit the app's icon
sizing system.

**Alternatives considered:**
- Unicode emoji: lighter, but inconsistent rendering and no CSS control
- Custom SVG: more work, no benefit over Material Symbols
- Keep text: defeats the purpose of the slice

### D2 — Keep the `<button>` wrapper, only change inner `<span>` content

The button carries the click handler, disabled state, focus-visible outline,
and data-testid attributes. Replacing only the inner `<span>` content
(minimal DOM change) reduces regression risk. The button shrinks naturally
because the icon is narrower than "Liberado"/"Bloqueado" text.

### D3 — Reduce `.trade-toggle` min-width from 5.5rem to fit icon

With icon-only content, `min-width: 5.5rem` is wasted. Reduce to
`min-width: 2rem` (enough for the icon + padding). This recovers ~70px
across both columns in the asset table.

### D4 — Add `aria-label` for accessibility

Since the visual content changes from readable text to an icon, add
`aria-label="Compra: Liberado"` / `aria-label="Compra: Bloqueado"` to
each button so screen readers announce the state. The `title` attribute
already provides tooltip text.

## Risks / Trade-offs

- **[Risk] Test assertions on "Liberado"/"Bloqueado" text break** → Update
  browser tests that assert inner text; testids are preserved so selector
  paths don't change.
- **[Risk] Icon font fails to load** → Fallback: the button still shows
  empty clickable area with correct color; title tooltip provides info.
  Low probability since Material Symbols is already loaded for other icons.
- **[Trade-off] Icon-only may be less discoverable than text** → Mitigated
  by color coding (green/red) and tooltip on hover. The column headers
  "Compra"/"Venda" provide context.
