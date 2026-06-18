## 1. CSS Token Corrections

- [x] 1.1 Fix `--class-4` and `--class-6` in `app.css :root` with OKLCH values meeting WCAG AA
- [x] 1.2 Add `--negative-ink` and `--positive-ink` custom properties
- [x] 1.3 Convert `--error-bg`/`--error-fg` to OKLCH with ≥4.5:1 contrast

## 2. Hardcoded Color Fix

- [x] 2.1 Find and replace `color: #fff` with `var(--negative-ink)` in delete-confirm buttons across all templates

## 3. DESIGN.md Update

- [x] 3.1 Rewrite color sections with contrast table (D-02) and corrected swatches (D-04)

## 4. Automated Contrast Test

- [x] 4.1 Create `tests/test_phase02_tokens.py` using tinycss2 + coloraide to verify all token pairs meet WCAG AA

## 5. Verification

- [x] 5.1 Run `pytest -m unit -q` — all pass
- [ ] 5.2 Visual check: open dashboard, verify colors look correct
