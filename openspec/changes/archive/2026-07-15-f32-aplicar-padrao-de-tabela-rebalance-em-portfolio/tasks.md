## 1. CSS — Portfolio table inherits rebalance visual design

**R30 status:** Tasks 1.1–1.5 already done by R30. `.portfolio-table-shell` inherits `.data-table-shell`, `.asset-table` inherits `.data-table`, th/td use `--table-*` tokens, alternating rows use variables.

- [x] 1.1 ~~Refactor `.portfolio-table-shell` to inherit from R30 `.data-table-shell` base class~~ — DONE by R30
- [x] 1.2 ~~Refactor `.asset-table` to inherit from R30 `.data-table` base class~~ — DONE by R30
- [x] 1.3 ~~Align `.asset-table th` with `.rebalance-table-th` visual values~~ — DONE by R30 (uses `--table-text-muted`, `--table-header-bg`)
- [x] 1.4 ~~Align `.asset-table td` with `.rebalance-asset-cell`~~ — DONE by R30 (uses `--table-border`)
- [x] 1.5 ~~Align `.asset-table tbody tr:nth-child(odd/even) td` alternating backgrounds~~ — DONE by R30 (uses `--table-row-odd/even`)
- [x] 1.6 ~~Verify `.asset-table tbody tr:hover td` hover effect works via `.data-table-tbody tr:hover` base rule~~ — `.data-table-tbody` selector is dead code (no template uses it). Portfolio hover works via `.asset-table tbody tr:hover td` (still present in CSS). No action needed.

## 2. CSS — Portfolio row color-coding (buy/sell/hold)

- [x] 2.1 Add `.asset-row--buy td` rule: `background: color-mix(in srgb, var(--positive) 7%, var(--surface)) !important`
- [x] 2.2 Add `.asset-row--sell td` rule: `background: color-mix(in srgb, var(--negative) 10%, var(--surface)) !important`
- [x] 2.3 Add `.asset-row--neutral td` rule: `background: color-mix(in srgb, var(--surface) 82%, var(--surface-sunk) 18%) !important`

## 3. CSS — Trade toggle and class-totals-row harmonization

- [x] 3.1 Restyle `.trade-toggle` to match rebalance `.rebalance-action-badge` visual (rounded pill, color-coded bg 12-18% opacity)
- [x] 3.2 Harmonize `.class-totals-row td` background/border values with rebalance total row palette

## 4. Template — Add buy/sell/hold row classes

- [x] 4.1 In `_patrimonio_class_section.html`, add `:class` binding on asset `<tr>` to emit `asset-row--buy`, `asset-row--sell`, or `asset-row--neutral` based on `a.buy_enabled` / `a.sell_enabled`
- [x] 4.2 Verify the class-totals-row `<tr>` does not receive buy/sell classes (it has no trade flags)

## 5. Verification

- [x] 5.1 Run `task test-unit` — confirm no regressions
- [x] 5.2 Run `task lint` — confirm no lint errors
- [x] 5.3 Visual inspection: portfolio tables match rebalance tables in browser (shell, headers, rows, cells, hover, color-coding)
- [x] 5.4 Verify inline editing still works (click target %, edit, Enter, blur)
- [x] 5.5 Verify delete confirm still works (class delete, asset delete)
- [x] 5.6 Verify trade toggle buttons still function (click toggles state, persists)
- [x] 5.7 Regenerate visual regression baselines if applicable
- [x] 5.8 Run `refresh-for-test` and confirm portfolio page renders correctly
