## Why

Phase 1 audit found multiple WCAG 2.1 AA contrast failures in the Omaha color palette. `--accent` vs `--ink` fails at 2.23:1, two class swatches (`--class-4`, `--class-6`) have insufficient contrast, error tokens use raw hex instead of OKLCH, and delete-confirm buttons hardcode `color: #fff` instead of referencing a token. Palette must be corrected before component-level fixes (Phase 3+) can proceed.

## What Changes

- Correct `--class-4` and `--class-6` in `app.css` `:root` block to meet 4.5:1 contrast vs `--bg`
- Add `--negative-ink` and `--positive-ink` tokens for status text on filled backgrounds
- Convert `--error-bg` and `--error-fg` to OKLCH format
- Replace hardcoded `color: #fff` with `var(--negative-ink)` in delete-confirm button rules
- Rewrite DESIGN.md color sections with contrast ratios in token table
- Annotate component inventory in DESIGN.md with token references
- Create `tests/test_phase02_tokens.py` with automated contrast verification
- Legacy aliases (`--fg` → `var(--ink)`, `--muted` → `var(--ink-muted)`) remain intact

## Capabilities

### New Capabilities
- `color-tokens`: Contrast-safe color token system for Omaha with OKLCH values, documented WCAG AA ratios, and automated verification

### Modified Capabilities
<!-- No existing specs in openspec/specs/ -->

## Impact

- `src/omaha/static/app.css`: `:root` block tokens, delete-confirm button rules
- `DESIGN.md`: Color section refresh with contrast column, corrected swatches, annotated component inventory
- `tests/test_phase02_tokens.py`: New file with PALT-01/PALT-02 verification
