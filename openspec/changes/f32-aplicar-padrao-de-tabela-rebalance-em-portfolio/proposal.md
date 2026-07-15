## Why

**The rebalance page table is the canonical reference for functionality and visual style.** The portfolio page asset table is broken and must not be used as reference.

After R30 (shared CSS base classes) and R31 (unified filter panels) establish the foundation, portfolio asset tables still use their own visual styling while rebalance tables have a polished design with gradient shell, uppercase headers, alternating row colors, and buy/sell color-coding. Users switching between Patrimônio and Rebalanceamento tabs see two different table "languages" for the same data density. This slice ports the rebalance visual design to portfolio tables so both pages feel like one coherent system.

## What Changes

- **Shell**: `.portfolio-table-shell` inherits the same border-radius, shadow,
  gradient background as `.rebalance-table-shell` (already similar; confirm
  exact match after R30 base classes land).
- **Headers**: `.asset-table th` gets the same uppercase treatment, font-weight,
  letter-spacing, hover effect, and sort indicator styling as
  `.rebalance-table-th`.
- **Rows**: Asset rows get alternating background colors matching rebalance
  palette, hover highlight, and buy/sell color-coding via row-level classes
  (`.asset-row--buy`, `.asset-row--sell`, `.asset-row--hold`).
- **Cells**: `td` padding, borders, `font-variant-numeric: tabular-nums`
  aligned with `.rebalance-asset-cell`.
- **Trade toggles**: Buy/sell buttons keep their functionality but adopt the
  rebalance action-badge visual language (rounded pill, color-coded background).

**Documented exceptions** (portfolio keeps unique aspects):
1. **2-level header** (`asset-table-group-row` + `asset-table-subhead-row`):
   portfolio has grouped columns (Classe 3-colspan, Carteira 3-colspan) that
   rebalance doesn't. The group row and subhead row remain as-is, but inherit
   the shared header base styling.
2. **`class-totals-row`** summary row: portfolio-specific aggregate row per
   class section. Visual treatment stays (sunk background, bold text) but
   palette values harmonize with the new row system.
3. **Inline editing** (target % fields): portfolio has editable percentage
   cells that rebalance doesn't. These keep their click-to-edit UX; only the
   surrounding cell styling changes.
4. **Delete confirmations**: portfolio has inline delete confirm for classes
   and assets. These are behavior-only; no visual change needed beyond what
   the row system provides.

## Capabilities

### New Capabilities

None. This is a visual alignment change, not a new feature.

### Modified Capabilities

- `component-state-language`: Table visual patterns gain a unified "data table"
  vocabulary. The spec's existing component-state descriptions for tables expand
  to cover the portfolio use case (grouped headers, summary rows, inline editing
  cells) as documented exceptions.

## Impact

- **CSS**: `src/omaha/static/app.css` — portfolio table section (~lines 1773–2018)
  gets refactored to inherit from shared base classes (R30) and match rebalance
  visual tokens.
- **Templates**: `src/omaha/templates/_patrimonio_class_section.html` — row
  classes change to emit buy/sell/hold modifiers for color-coding. No behavior
  change.
- **No route/model/seed changes**: Visual-only. No DB mutation, no API change.
- **Dependencies**: R30 (shared CSS base) and R31 (unified filter panels) must
  be applied first. This slice applies on top of their output.
