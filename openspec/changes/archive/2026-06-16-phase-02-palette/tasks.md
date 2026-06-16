## 1. Correct CSS Token Values

- [x] 1.1 Fix `--class-4` from `oklch(0.62 0.15 50)` to `oklch(0.53 0.13 50)` for ≥4.5:1 contrast
- [x] 1.2 Fix `--class-6` from `oklch(0.52 0.10 200)` (verify actual value, ensure ≥4.5:1 vs `--bg`)
- [x] 1.3 Add `--negative-ink: oklch(0.98 0.005 25)` token for text on danger fills
- [x] 1.4 Add `--positive-ink: oklch(0.98 0.005 145)` token for text on success fills
- [x] 1.5 Convert `--error-bg` and `--error-fg` from hex to OKLCH values
- [x] 1.6 Replace hardcoded `color: #fff` with `var(--negative-ink)` in `.class-delete-confirm-yes` and `.dashboard-asset-delete-confirm-yes`
- [x] 1.7 Verify legacy aliases `--fg` and `--muted` remain intact

## 2. Update DESIGN.md Color Documentation

- [x] 2.1 Rewrite color token table with corrected values and Contrast column (D-02)
- [x] 2.2 Update class swatch table with corrected slot values
- [x] 2.3 Annotate component inventory table with token references (D-04)
- [x] 2.4 Document migration path for token changes

## 3. Create Automated Token Verification

- [x] 3.1 Create `tests/test_phase02_tokens.py` with contrast verification tests for all `:root` tokens
- [x] 3.2 Run full verification: `uv run pytest tests/test_phase02_tokens.py tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`
