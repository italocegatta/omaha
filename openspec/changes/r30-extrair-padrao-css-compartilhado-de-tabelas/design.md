## Context

Two tables in the app — rebalance plan (`_rebalance_plan.html`) and portfolio assets (`_patrimonio_class_section.html`) — share identical visual patterns for shell, header, rows, cells, alternating backgrounds, and hover states. They implement these patterns under different class names with duplicated `color-mix()` formulas. The rebalance table is the design reference (F18 polish); the portfolio table was aligned visually in F27/F28 but kept its own class names.

Current state of duplication in `app.css`:
- `.rebalance-table-shell` (line ~2980) and `.portfolio-table-shell` (line ~1773): same border-radius, border, background gradient, box-shadow
- `.rebalance-table-th` (line ~2998) and `.asset-table th` (line ~1815): same font-size, letter-spacing, text-transform, font-weight, color formula
- `.rebalance-asset-row:nth-child(odd/even)` (line ~3260) and `.asset-table tbody tr:nth-child(odd/even)` (line ~1940): same alternating row formulas
- `.rebalance-asset-cell` (line ~3243) and `.asset-table td` (line ~1808): same padding, border-bottom, vertical-align

Hardcoded color-mix formulas mean a palette change requires editing 6+ rule blocks.

## Goals / Non-Goals

**Goals:**
- Extract `.data-table-*` base classes for shell, table, thead, th, tbody, tr, td
- Create `--table-*` CSS custom properties so palette swap = variable change
- Rebalance and portfolio inherit from bases; keep their specific overrides
- Zero visual change (pixel-perfect parity before/after)

**Non-Goals:**
- Unifying filter panel behavior (R31 scope)
- Changing table structure or HTML (no new `<table>` elements, no column changes)
- Touching inline editors, trade toggles, or action badges
- Dark mode toggle (existing dark-only palette stays)

## Decisions

### D1: Base classes as shared selectors, not @extend

Use `.data-table-shell` etc. as standalone class selectors applied in templates alongside existing classes. Both `.rebalance-table-shell` and `.portfolio-table-shell` become thin wrappers that `@apply` or simply co-apply the base. CSS has no `@extend`; using shared selectors avoids preprocessor dependency.

**Alternative considered**: CSS `@layer` with cascade layers. Rejected: adds complexity for a single-file CSS bundle; not needed when specificity is already manageable.

### D2: `--table-*` variables on `:root`, not scoped to table

Variables go in `:root` alongside existing `--surface`, `--border`, etc. This keeps them accessible from any context (future tables, print styles) and matches the existing token pattern.

Variables to create:
```
--table-shell-bg: linear gradient formula (currently hardcoded)
--table-header-bg: color-mix(in srgb, var(--surface-sunk) 70%, var(--surface))
--table-row-odd: color-mix(in srgb, var(--surface) 84%, var(--surface-sunk))
--table-row-even: color-mix(in srgb, var(--surface-sunk) 88%, transparent)
--table-row-hover: color-mix(in srgb, var(--accent) 10%, var(--surface))
--table-border: color-mix(in srgb, var(--border) 72%, transparent)
--table-border-strong: color-mix(in srgb, var(--border-strong) 72%, transparent)
--table-text: var(--ink)
--table-text-muted: color-mix(in srgb, var(--ink) 94%, white)
```

### D3: Template classes = base + specific

Templates get both base and specific classes:
```html
<div class="data-table-shell rebalance-table-shell">
<table class="data-table rebalance-table">
```

Specific classes only override what differs from the base. Base handles all shared properties.

### D4: Rebalance as reference design source

Rebalance table CSS (F18 polish) is the canonical visual. Portfolio inherits the same base and adds its exceptions (2-level header, summary row, inline editors). This matches the existing F27 intent.

## Risks / Trade-offs

- **[Risk] Specificity conflicts** → Base classes use single-class specificity (`.data-table-shell`). Existing specific classes (`.rebalance-table-shell`) have same specificity but come later in cascade, so overrides work naturally.
- **[Risk] Visual regression during refactor** → Mitigate by running visual regression tests before/after. Apply base + verify pixel match, then remove duplicates.
- **[Risk] Variable inheritance in nested contexts** → CSS custom properties inherit naturally; no issue since tables are always in main content.
- **[Trade-off] More classes in HTML** → Each table element gains one extra class. Acceptable for the DRY benefit.
