## 1. Token swap in app.css :root

- [x] 1.1 Replace all `:root` color tokens with Catppuccin Frappe OKLCH values (see design.md D2 token mapping table)
- [x] 1.2 Add new `--surface-elevated` token: `oklch(0.395 0.034 275.9)`
- [x] 1.3 Update `--class-1` through `--class-8` to Catppuccin Frappe-derived values
- [x] 1.4 Update `--class-1-tint` through `--class-8-tint` to use new `--class-N` + `--surface`
- [x] 1.5 Update `--bg-hover` to match new surface hierarchy
- [x] 1.6 Update `--color-focus` to match new `--class-1` (blue)
- [x] 1.7 Update legacy aliases `--fg` and `--muted` (still point to `--ink` / `--ink-muted`)

## 2. Component differentiation in app.css

- [x] 2.1 Asset table: add `background: var(--surface-sunk)` to `.proposto-table` / patrimonio table styles
- [x] 2.2 Row padding: reduce td padding from `0.55rem` to `0.05rem` vertical
- [x] 2.3 Angular borders: change all pills/toggles/badges `border-radius` from `999px` to `4px`
- [x] 2.4 Trade toggle Liberado: `background: color-mix(in srgb, var(--positive) 15%, var(--surface))`, `color: var(--positive)`
- [x] 2.5 Trade toggle Bloqueado: `background: color-mix(in srgb, var(--negative) 12%, var(--surface))`, `color: var(--negative)`
- [x] 2.6 Number contrast: all numeric cells (`.asset-value`, `.asset-pct`, currency) use `color: var(--ink)` at `font-weight: 600+`
- [x] 2.7 Asset table header: tinted background + stronger separator line
- [x] 2.8 Class card surface: match summary cards with `--surface-elevated`

## 3. Class header differentiation

- [x] 3.1 Class header tinted bg: `background: color-mix(in srgb, var(--class-N) 30%, var(--bg))`
- [x] 3.2 Class header color border: `border-bottom: 2px solid var(--class-N)`
- [x] 3.3 Class name text: `color: var(--class-N)`, `font-weight: 700`
- [x] 3.4 Remove swatch square from `_patrimonio_class_section.html` template

## 4. Portfolio header elevation

- [x] 4.1 Portfolio header: `background: var(--surface-elevated)` in `_patrimonio_portfolio_header.html`

## 5. Python class-color sync

- [x] 5.1 Update `_CLASS_COLORS` tuple in `routes/pages.py` to match new `--class-N` OKLCH values
- [x] 5.2 Update `_CLASS_COLORS` in `audit/inventory.py` to match

## 6. DESIGN.md update

- [x] 6.1 Update tokens table with Catppuccin Frappe values and contrast ratios
- [x] 6.2 Rewrite color strategy section: hue shift rationale, surface elevation hierarchy, class header differentiation
- [x] 6.3 Update component inventory with new token dependencies

## 7. Tests and baselines

- [x] 7.1 Update `test_dark_mode_tokens.py` contrast thresholds for new palette
- [ ] 7.2 Regenerate visual baselines (`task test-visual`)
- [x] 7.3 Run full test suite (`task test-unit`, `task test-integration`, `task test-bdd`, `task test-e2e`) and fix failures

## 8. Cleanup

- [x] 8.1 Remove mockup route (`src/omaha/routes/mockup.py` + its registration in app)

**Note:** Visual baselines (task 7.2) require owner to run `task test-visual` and commit updated PNGs.
