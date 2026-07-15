## Why

Rebalance and portfolio tables duplicate the same visual patterns (shell, header, rows, cells, alternating backgrounds, hover) under different class names. Changing the palette means editing two separate rule blocks with identical color-mix formulas. Extracting shared `.data-table-*` base classes with `--table-*` CSS custom properties makes future palette swaps a single-variable change and eliminates ~120 lines of duplicated table CSS.

## What Changes

- Create `.data-table-shell`, `.data-table`, `.data-table-thead`, `.data-table-th`, `.data-table-tbody`, `.data-table-tr`, `.data-table-td` base classes in `app.css`
- Create `--table-*` CSS custom properties (`--table-shell-bg`, `--table-header-bg`, `--table-row-odd`, `--table-row-even`, `--table-row-hover`, `--table-border`, `--table-border-strong`, `--table-text`, `--table-text-muted`) on `:root`
- Rebalance table classes (`.rebalance-table-shell`, `.rebalance-table`, `.rebalance-table-th`, `.rebalance-asset-row`, `.rebalance-asset-cell`) inherit from `.data-table-*` bases and add rebalance-specific overrides only
- Portfolio table classes (`.portfolio-table-shell`, `.asset-table`, `.asset-table-header-filter`, `.class-totals-row`) inherit from `.data-table-*` bases and add portfolio-specific overrides only
- All hardcoded color-mix formulas for table surfaces reference `--table-*` variables instead of raw token combinations
- Changing `--table-*` variables restyle ALL tables at once

## Capabilities

### New Capabilities

- `shared-table-pattern`: Base CSS classes and `--table-*` custom properties for table shell, header, rows, and cells. Both rebalance and portfolio tables inherit from these bases. Covers the structural and palette layer only; filter panels, inline editors, and trade toggles are out of scope.

### Modified Capabilities

_(none — no spec-level behavior changes; this is a CSS-only refactor)_

## Impact

- **CSS only** (`src/omaha/static/app.css`): ~200 lines touched (deduplicate, extract base, add variables)
- **Templates**: class attribute changes in `_rebalance_plan.html` (add base classes alongside existing) and `_patrimonio_class_section.html` (same)
- **No behavior change**: no Python, no routes, no JS, no DB
- **No breaking change**: existing class names preserved as thin wrappers over bases
