## 1. High priority — duplicate selectors

- [ ] 1.1 Delete duplicate `.btn` block (lines 555-569) — exact copy of lines 525-538
- [ ] 1.2 Delete duplicate `.btn:hover:not(:disabled)` block (lines 570-572) — exact copy of lines 540-542
- [ ] 1.3 Delete duplicate `.btn-primary` block (lines 573-577) — exact copy of lines 543-547
- [ ] 1.4 Delete duplicate `.btn-primary:hover:not(:disabled)` block (lines 578-582) — exact copy of lines 548-552

## 2. High priority — conflicting `:root` and header

- [ ] 2.1 Delete percentage-based `:root` block with `--col-*` variables (lines 89-98) — superseded by pixel block at lines 1792-1807 (F15)
- [ ] 2.2 Delete dead `.class-section-header` grid block (lines 1081-1115) — superseded by `display: block` at line 1842 (F15)
- [ ] 2.3 Delete dead `.hdr-leading` grid-column block (lines 1143-1146) — superseded by line 1849

## 3. High priority — duplicate media query

- [ ] 3.1 Delete duplicate `@media (prefers-reduced-motion)` block (lines 1265-1270) — superseded by F10 block at lines 3522-3527

## 4. Medium priority — dead code

- [ ] 4.1 Delete duplicate `.dashboard-asset-list` and `.dashboard-asset-list li` rules (lines 636-642) — superseded by lines 1228-1241
- [ ] 4.2 Delete duplicate `.dashboard-asset-empty` and `.dashboard-asset-empty a` rules (lines 644-645) — superseded by lines 1257-1258
- [ ] 4.3 Delete duplicate `.muted` rule (line 1260) — identical to line 584
- [ ] 4.4 Delete empty `.rebalance-card` block (lines 2862-2866) — zero declarations, comment-only

## 5. Medium priority — unit consistency

- [ ] 5.1 Change `.section-divider` margin from `24px 0` to `1.5rem 0` (line 3572)

## 6. Verification

- [ ] 6.1 Run `uv run task test-unit` — all tests must pass
- [ ] 6.2 Invoke `refresh-for-test` skill — browser visual inspection confirms no regressions
