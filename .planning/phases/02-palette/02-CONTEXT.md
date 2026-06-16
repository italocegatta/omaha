# Phase 2: Palette - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

## Phase Boundary

A contrast-safe color token system replaces the broken palette and is fully documented in DESIGN.md. Define unambiguous foreground/background custom properties for every surface in `app.css`, lock each pair with a documented minimum WCAG 2.1 AA contrast ratio, and rewrite DESIGN.md's color sections to reflect the corrected system with rationale.

## Implementation Decisions

### DESIGN.md Update Depth
- **D-01:** Full color section refresh — rewrite Color strategy, Accent rationale, Class swatches, Token table, and Migration path. Every section that references color gets updated to match the corrected token system.
- **D-02:** Add a "Contrast" column to the token table — each token pair shows its computed WCAG AA ratio and Passa/Falha status from the Phase 1 audit.
- **D-03:** No version history or changelog in DESIGN.md. It stays a living snapshot. Phase 2 changes are tracked in git commits and SUMMARY.md.
- **D-04:** Annotate the Component inventory table with the token names each component uses (e.g., "Uses --btn-primary-bg, --btn-primary-fg").

### the agent's Discretion
Token granularity (surface-level pairs vs component-scoped tokens), naming convention (semantic vs surface-paired), state tokens (error/disabled/success), and dark mode forward compatibility were offered but not discussed — the agent decides these during planning based on Phase 1 audit findings, existing app.css patterns, and WCAG requirements.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design system
- `DESIGN.md` — Current design system with target OKLCH values, accent rationale, class swatches table, component inventory, anti-patterns, and 6-step migration path
- `src/omaha/static/app.css` — Current CSS (1440 lines) with 23 color tokens in `:root`, all component styles, legacy aliases (`--fg`, `--muted`), and `--error-bg`/`--error-fg` hex values

### Requirements
- `.planning/REQUIREMENTS.md` — PALT-01 (fg/bg pairs per surface), PALT-02 (documented contrast ratios), PALT-03 (DESIGN.md reflects corrected tokens)

### Phase 1 audit artifacts
- `reports/contrast_audit.html` — 329 KB self-contained audit report with 300+ state color pairs across 8 templates, per-page collapsible tables, token inventory, failure log, and "Mostrar apenas falhas" toggle
- `src/omaha/audit/css_parser.py` — CSS parsing with recursive var() resolution (depth guard 10), `color_token_inventory()` returning `TokenInventoryRow` dataclass rows
- `src/omaha/audit/color_resolver.py` — `contrast_ratio()`, `aa_status()` (4.5:1 body / 3:1 large), `apply_brightness()`, `composite_over()` using coloraide library
- `.planning/phases/01-audit/01-01-SUMMARY.md` — Interactive element inventory, report generation, CLI entry point
- `.planning/phases/01-audit/01-02-SUMMARY.md` — CSS token inventory (23 tokens), adjacent-background mapping (foreground tokens vs `--bg`, surface tokens vs `--ink`)

### Project context
- `.planning/PROJECT.md` — Tech stack (FastAPI + Jinja2 + Alpine.js + SQLite), WCAG 2.1 AA target, PT-BR UI language, two-profile household
- `.planning/REQUIREMENTS.md` — Full v1/v2 requirement traceability matrix

## Existing Code Insights

### Reusable Assets
- **`src/omaha/audit/css_parser.py`** — `parse_stylesheet()` and `resolve_var()` can validate corrected token values during implementation. `color_token_inventory()` can re-generate contrast data against the updated app.css.
- **`src/omaha/audit/color_resolver.py`** — `contrast_ratio()` and `aa_status()` can verify each new token pair against WCAG AA thresholds before committing.

### Established Patterns
- Legacy alias pattern (`--fg: var(--ink)`, `--muted: var(--ink-muted)`) — transitional aliases let existing rules resolve to new values without renaming every call site. This pattern should be extended for the new token system.
- First-definition-wins for custom properties — `:root` tokens take precedence over component-scoped re-declarations.
- OKLCH color space throughout — all target values from DESIGN.md use OKLCH; hex values exist only as migration sources.

### Integration Points
- `app.css` `:root` block (lines 3-58) — all color tokens live here. New tokens go here.
- Every component rule in app.css references `var(--ink)`, `var(--surface)`, `var(--accent)`, etc. — token renaming or aliasing affects the entire stylesheet.
- `DESIGN.md` token table (lines 30-41) — the migration source for corrected values.

## Specific Ideas

- User chose caveman full mode — communications stay compressed but technically precise
- Phase 1 audit found `--accent` on `--ink` fails at 2.23:1 (needs accent-ink text on accent backgrounds), `--bg` passes at 16.85:1
- The `--error-bg` and `--error-fg` tokens are raw hex (`#fde8e8`, `#8a1f1f`) — candidate for OKLCH migration
- DESIGN.md accent rationale (hue 150 fern green) should be preserved — it's a deliberate design choice, not a defect

## Deferred Ideas

- Dark mode (THEM-01, THEM-02) — v2 themes phase. Token system should be designed so dark mode can be added by swapping values without renaming tokens, but dark mode implementation is explicitly deferred.
- Layout or typography redesign — explicitly out of scope per REQUIREMENTS.md. This milestone only fixes color/state visibility.

---

*Phase: 2-Palette*
*Context gathered: 2026-06-13*
