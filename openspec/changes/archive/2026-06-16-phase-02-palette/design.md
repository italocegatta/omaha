## Context

Phase 1 audit tooling (`src/omaha/audit/`) discovered multiple WCAG 2.1 AA contrast failures in the current color palette. Current `app.css` `:root` block uses a mix of hex and OKLCH values, lacks foreground token pairs for status colors, and has two class swatches (`--class-4` at 3.84:1, `--class-6` at 4.02:1) below the 4.5:1 body text threshold. `--accent` on `--ink` fails at 2.23:1. Error feedback tokens (`--error-bg`, `--error-fg`) use raw hex instead of OKLCH. Delete-confirm buttons hardcode `color: #fff`.

DESIGN.md color sections need full refresh to reflect corrected values with documented contrast ratios.

## Goals / Non-Goals

**Goals:**
- Correct `--class-4` and `--class-6` to meet ≥4.5:1 contrast vs `--bg`
- Add `--negative-ink` and `--positive-ink` tokens for text on status fills
- Convert `--error-bg` and `--error-fg` to OKLCH with verified contrast
- Replace hardcoded `color: #fff` with `var(--negative-ink)` in `.class-delete-confirm-yes` and `.dashboard-asset-delete-confirm-yes`
- Rewrite DESIGN.md color token table with Contrast column (D-02)
- Annotate DESIGN.md component inventory with token names (D-04)
- Create `tests/test_phase02_tokens.py` with automated PALT-01/PALT-02 verification
- Legacy aliases (`--fg` → `var(--ink)`, `--muted` → `var(--ink-muted)`) remain intact (D-05)

**Non-Goals:**
- Component state fixes (COMP-01 through COMP-06) — Phase 3
- Contrast validation across full app (CONV-01, CONV-02) — Phase 4
- Regression protection (REGR-01, REGR-02) — Phase 5
- Dark mode or accent theming (THEM-01, THEM-02) — v2

## Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| D-01: Full color section refresh in DESIGN.md | Token table + rationale + component annotations — not piecemeal edits | Refresh, not patch |
| D-02: Add Contrast column to token table | Every token pair documents its WCAG AA status inline | Yes, body ≥4.5:1, UI/large ≥3:1 |
| D-03: No changelog in DESIGN.md | Git is the audit trail; duplication drifts | Skip changelog |
| D-04: Annotate component inventory with token names | Makes it explicit which tokens each component uses | Add `Tokens:` column |
| D-05: Legacy aliases preserved | `--fg` and `--muted` referenced elsewhere; rename breaks consumers | Alias map in CSS comment |

### Token Corrections

| Token | Current | Target (OKLCH) | Contrast vs `--bg` | WCAG |
|-------|---------|-----------------|-------------------|------|
| `--class-4` | `oklch(0.62 0.15 50)` | `oklch(0.53 0.13 50)` | 4.5:1 | AA ✓ |
| `--class-6` | `oklch(0.52 0.10 200)` | `oklch(0.52 0.10 200)` (no change needed, verify actual) | 4.5:1 | AA ✓ |
| `--negative-ink` | (does not exist) | `oklch(0.98 0.005 25)` | 4.5:1 on `--negative` | AA ✓ |
| `--positive-ink` | (does not exist) | `oklch(0.98 0.005 145)` | 4.5:1 on `--positive` | AA ✓ |
| `--error-bg` | hex `#fdd` | `oklch(0.95 0.03 25)` | — | — |
| `--error-fg` | hex `#a00` | `oklch(0.45 0.15 25)` | 4.5:1 on `--error-bg` | AA ✓ |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| T-02-01: Token change breaks component that references old hex value inline | Audit all `var()` references in app.css before change; run `color_token_inventory()` after |
| T-02-02: Hardcoded `#fff` replacement missed in some delete-confirm rule | grep for `color:\s*#fff` in app.css; verify only intended rules match |
| T-02-03: CONV-01 test in Phase 4 reveals additional failures not caught by PALT-01/02 | Phase 2 only claims PALT coverage; Phase 4 handles full validation sweep |

## Migration Plan

1. Correct `:root` block tokens in app.css (class-4, class-6, new status-ink, error OKLCH)
2. Replace hardcoded `#fff` in delete-confirm rules
3. Run `color_token_inventory()` — verify zero Falha rows
4. Rewrite DESIGN.md color sections
5. Create `tests/test_phase02_tokens.py`
6. Run `uv run pytest tests/test_phase02_tokens.py tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`

Rollback: `git checkout HEAD -- src/omaha/static/app.css` reverts token changes. DESIGN.md and test reverted separately.
