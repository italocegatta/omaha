# Phase 2: Palette - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 2-palette
**Areas discussed:** DESIGN.md update depth

---

## DESIGN.md Update Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Token table only | Update only the "Tokens (target)" table with corrected values | |
| Color strategy + token table + migration path | Rewrite Color strategy, update token table, refresh Migration path | |
| Full color section refresh | Rewrite Color strategy, Accent rationale, Class swatches, Token table, Component inventory, Migration path | ✓ |

**User's choice:** Full color section refresh — every section referencing color gets updated so DESIGN.md becomes the definitive post-fix reference.
**Notes:** None beyond the selection.

---

### Contrast ratios in token table

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add contrast ratios | Add a "Contrast" column to the token table with WCAG AA ratio and Passa/Falha status | ✓ |
| No — keep table clean | Keep token table with just name, value, role. Contrast validation in Phase 4 | |

**User's choice:** Add contrast ratios — every token pair gets its computed ratio from Phase 1 audit in the table.
**Notes:** This makes DESIGN.md self-validating.

---

### Changelog in DESIGN.md

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add changelog | Add "## History" section noting Phase 2 changes | |
| No changelog needed | DESIGN.md stays living snapshot; changes tracked in git and SUMMARY.md | ✓ |

**User's choice:** No changelog. Git commit history is the audit trail.
**Notes:** DESIGN.md is a living document — version history adds maintenance burden without value.

---

### Component inventory token annotations

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — annotate with tokens | Add "Accent/primary token" column or update Notes with token references | ✓ |
| No — keep component table structural-only | Component inventory is about structure, not styles; token usage visible in app.css | |

**User's choice:** Annotate component inventory with token references.
**Notes:** Each component row gets the token names it uses.

---

## the agent's Discretion

- **Token granularity** — How many new token pairs (minimum fix vs surface-level vs component-scoped)
- **Naming convention** — Semantic (`--text-primary`) vs surface-paired (`--card-fg`, `--card-bg`) vs component-scoped (`--btn-primary-text`, `--btn-primary-bg`)
- **State tokens** — Whether error/success/disabled-state tokens belong in this phase, and whether hex `--error-bg`/`--error-fg` migrate to OKLCH
- **Dark mode forward compatibility** — Whether to design tokens so dark mode can be added by swapping values without renaming

These were offered as gray areas but the user chose to let the agent decide during planning.

## Deferred Ideas

- Dark mode (THEM-01, THEM-02) — v2 themes phase
- Layout or typography redesign — explicitly out of scope per REQUIREMENTS.md
