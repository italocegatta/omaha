## 1. CSS custom properties

- [ ] 1.1 Add `--table-*` CSS custom properties to `:root` in `app.css`: `--table-header-bg`, `--table-row-odd`, `--table-row-even`, `--table-row-hover`, `--table-border`, `--table-border-strong`, `--table-text`, `--table-text-muted` (values extracted from current hardcoded color-mix formulas in rebalance table rules)
- [ ] 1.2 Verify all `--table-*` variables resolve correctly in browser DevTools

## 2. Base CSS classes

- [ ] 2.1 Create `.data-table-shell` base class in `app.css` with shared shell properties (border-radius, border, background, box-shadow, overflow) extracted from `.rebalance-table-shell` and `.portfolio-table-shell`
- [ ] 2.2 Create `.data-table` base class with shared table properties (width, border-collapse, font-size, background) extracted from `.rebalance-table` and `.asset-table`
- [ ] 2.3 Create `.data-table-th` base class with shared header cell properties (text-align, padding, background, border-bottom, font-weight, font-size, letter-spacing, text-transform, color) extracted from `.rebalance-table-th` and `.asset-table th`
- [ ] 2.4 Create `.data-table-td` base class with shared body cell properties (padding, border-bottom, vertical-align, white-space) extracted from `.rebalance-asset-cell` and `.asset-table td`
- [ ] 2.5 Create `.data-table-tbody tr:nth-child(odd/even)` rules using `--table-row-odd/even` variables
- [ ] 2.6 Create `.data-table-tbody tr:hover` rule using `--table-row-hover` variable

## 3. Refactor rebalance table to inherit from base

- [ ] 3.1 Update `.rebalance-table-shell` to remove properties now in `.data-table-shell` (keep only rebalance-specific overrides if any)
- [ ] 3.2 Update `.rebalance-table` to remove properties now in `.data-table`
- [ ] 3.3 Update `.rebalance-table-th` to remove properties now in `.data-table-th` (keep rebalance-specific: cursor, user-select, white-space)
- [ ] 3.4 Update `.rebalance-asset-cell` to remove properties now in `.data-table-td`
- [ ] 3.5 Update `.rebalance-asset-row:nth-child(odd/even)` to use `--table-row-odd/even` variables
- [ ] 3.6 Verify rebalance-specific row states (buy/sell/neutral hover) still override correctly

## 4. Refactor portfolio table to inherit from base

- [ ] 4.1 Update `.portfolio-table-shell` to remove properties now in `.data-table-shell` (keep only portfolio-specific overrides)
- [ ] 4.2 Update `.asset-table` to remove properties now in `.data-table` (keep portfolio-specific: min-width, col widths)
- [ ] 4.3 Update `.asset-table th` to remove properties now in `.data-table-th` (keep portfolio-specific: line-height, word-break, overflow-wrap)
- [ ] 4.4 Update `.asset-table td` to remove properties now in `.data-table-td`
- [ ] 4.5 Update `.asset-table tbody tr:nth-child(odd/even)` to use `--table-row-odd/even` variables
- [ ] 4.6 Verify portfolio-specific states (class-totals-row, class-section-body) still override correctly

## 5. Template updates

- [ ] 5.1 Add base classes to `_rebalance_plan.html`: `data-table-shell` on shell div, `data-table` on `<table>`, `data-table-th` on `<th>` elements, `data-table-td` on `<td>` elements
- [ ] 5.2 Add base classes to `_patrimonio_class_section.html`: `data-table-shell` on shell div, `data-table` on `<table>`, `data-table-th` on `<th>` elements, `data-table-td` on `<td>` elements

## 6. Verification

- [ ] 6.1 Run visual regression tests — confirm no pixel-level differences
- [ ] 6.2 Run full test suite (`task test`) — confirm no regressions
- [ ] 6.3 Manual browser check: rebalance table looks identical
- [ ] 6.4 Manual browser check: portfolio table looks identical
- [ ] 6.5 Verify palette swap works: override one `--table-*` variable in DevTools and confirm both tables update
