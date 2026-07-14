## 1. CSS — Portfolio table inherits rebalance visual design

- [ ] 1.1 Refactor `.portfolio-table-shell` to inherit from R30 `.data-table-shell` base class (or replicate exact rebalance values if R30 not yet applied: `border-radius: 14px`, gradient bg, shadow)
- [ ] 1.2 Refactor `.asset-table` to inherit from R30 `.data-table` base class (font-size, width, bg, border)
- [ ] 1.3 Align `.asset-table th` with `.rebalance-table-th` visual values (padding, bg, hover accent lift, font-weight, letter-spacing)
- [ ] 1.4 Align `.asset-table td` with `.rebalance-asset-cell` (padding `0.82rem 0.75rem`, borders, `font-variant-numeric: tabular-nums`)
- [ ] 1.5 Align `.asset-table tbody tr:nth-child(odd/even) td` alternating backgrounds with rebalance palette
- [ ] 1.6 Add `.asset-table tbody tr:hover td` hover effect matching rebalance: `color-mix(in srgb, var(--accent) 10%, var(--surface))`

## 2. CSS — Portfolio row color-coding (buy/sell/hold)

- [ ] 2.1 Add `.asset-row--buy td` rule: `background: color-mix(in srgb, var(--positive) 7%, var(--surface)) !important`
- [ ] 2.2 Add `.asset-row--sell td` rule: `background: color-mix(in srgb, var(--negative) 10%, var(--surface)) !important`
- [ ] 2.3 Add `.asset-row--neutral td` rule: `background: color-mix(in srgb, var(--surface) 82%, var(--surface-sunk) 18%) !important`

## 3. CSS — Trade toggle and class-totals-row harmonization

- [ ] 3.1 Restyle `.trade-toggle` to match rebalance `.rebalance-action-badge` visual (rounded pill, color-coded bg 12-18% opacity)
- [ ] 3.2 Harmonize `.class-totals-row td` background/border values with rebalance total row palette

## 4. Template — Add buy/sell/hold row classes

- [ ] 4.1 In `_patrimonio_class_section.html`, add `:class` binding on asset `<tr>` to emit `asset-row--buy`, `asset-row--sell`, or `asset-row--neutral` based on `a.buy_enabled` / `a.sell_enabled`
- [ ] 4.2 Verify the class-totals-row `<tr>` does not receive buy/sell classes (it has no trade flags)

## 5. Verification

- [ ] 5.1 Run `task test-unit` — confirm no regressions
- [ ] 5.2 Run `task lint` — confirm no lint errors
- [ ] 5.3 Visual inspection: portfolio tables match rebalance tables in browser (shell, headers, rows, cells, hover, color-coding)
- [ ] 5.4 Verify inline editing still works (click target %, edit, Enter, blur)
- [ ] 5.5 Verify delete confirm still works (class delete, asset delete)
- [ ] 5.6 Verify trade toggle buttons still function (click toggles state, persists)
- [ ] 5.7 Regenerate visual regression baselines if applicable
- [ ] 5.8 Run `refresh-for-test` and confirm portfolio page renders correctly
