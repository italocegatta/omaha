## Why

The current dark palette uses hue 60 (warm-brown) throughout — body, surfaces, borders, and ink all share the same hue family, making components blend together. The owner validated a mockup (/mockup v4) using Catppuccin Frappe (cool blue-gray, hue ~274) which provides better visual hierarchy through surface elevation, class-colored headers, and angular borders. This swap addresses "everything looks the same" while respecting PRD §4.10 ("domestic, no ornament") — palette-only, no gradient/glow/glassmorphism.

## What Changes

- Replace all `:root` color tokens from hue 60 warm-neutral to Catppuccin Frappe OKLCH values (cool blue-gray, hue ~274).
- Add new token `--surface-elevated` for portfolio header (lighter than `--surface`).
- Differentiate class headers via tinted bg (`color-mix 30% class-color`) + 2px solid border-bottom. Remove swatch square — name carries the color.
- Asset table gets `--surface-sunk` background (inset feel).
- Compact rows: padding `0.55rem → 0.28rem` (−50% vertical).
- Angular borders: pills/toggles `999px → 4px` border-radius.
- Trade toggle: Liberado = success green, Bloqueado = danger red.
- Number contrast: all numeric cells use `--ink` at weight 600+.
- Update `DESIGN.md` tokens table + color strategy section.
- Update visual baselines (`task test-visual`).

## Capabilities

### Modified Capabilities
- `color-tokens`: All token values change (hue 60 → hue ~274 Catppuccin Frappe). Contrast ratios re-derived. New `--surface-elevated` token added.
- `component-state-language`: Table pattern gains compact rows, angular borders, class-colored headers (tinted bg + border-bottom). Trade toggle success/danger differentiation.

### New Capabilities
- None. This is a palette + component differentiation pass, not new capability introduction.

## Impact

- **CSS:** `src/omaha/static/app.css` — full `:root` token swap + component rule updates.
- **Design doc:** `DESIGN.md` — tokens table, color strategy section rewrite.
- **Templates:** `_patrimonio_class_section.html`, `_patrimonio_portfolio_header.html` — class header markup changes (remove swatch, add tinted bg).
- **Python:** `_CLASS_COLORS` tuple in `routes/pages.py` + `audit/inventory.py` must mirror new OKLCH values.
- **Tests:** Visual baselines (`task test-visual`) need regeneration. Token contrast tests may need threshold updates.
