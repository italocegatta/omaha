## Context

**The rebalance page table (`_rebalance_plan.html`) is the canonical reference for functionality and visual style.** The portfolio page asset table (`_patrimonio_class_section.html`) is broken and MUST NOT be used as reference — it has inconsistent class naming, duplicated rules, and misaligned visual patterns.

Portfolio asset tables and rebalance tables evolved independently. Rebalance tables received polished visual treatment in F18/F22 (gradient shell, uppercase headers, alternating rows, buy/sell color-coding). Portfolio tables got structural upgrades in F27/F28 (sorting, filtering, rounding) but retained their original visual language and accumulated inconsistencies.

After R30 extracts shared `.data-table-*` base CSS classes and R31 unifies filter panels, both table families will have a common structural foundation. This slice applies the rebalance visual design on top of that foundation so portfolio tables match rebalance tables exactly in look and feel.

### Current state (pre-F32)

**Rebalance table CSS** (canonical reference):
- Shell: `border-radius: 14px`, gradient bg, heavy shadow
- Headers: uppercase, `font-weight: 700`, `letter-spacing: 0.06em`, tinted bg, hover accent lift
- Rows: alternating odd/even backgrounds, hover accent tint, buy/sell/hold row-level color classes
- Cells: `padding: 0.82rem 0.75rem`, `font-variant-numeric: tabular-nums`, hairline bottom borders

**Portfolio table CSS** (broken — must be refactored):
- Shell: similar border-radius and shadow (already close via R30 base)
- Headers: uppercase, similar weight — but no hover effect, different bg mix
- Rows: alternating backgrounds — but no buy/sell color-coding, no hover
- Cells: `padding: 0.72rem 0.75rem` — slightly tighter than rebalance
- **Do NOT copy patterns from portfolio table — it is the target of refactoring, not the source**

### Constraints

- R30 (shared CSS base) and R31 (unified filter panels) MUST be applied first.
- Visual-only change: no route, model, seed, or behavior modification.
- Portfolio-specific structures (2-level header, class-totals-row, inline
  editing, delete confirmations) are documented exceptions — adapt styling,
  don't remove.

## Goals / Non-Goals

**Goals:**
- Portfolio asset tables SHALL be visually indistinguishable from rebalance
  tables in shell, header, row, and cell styling.
- Buy/sell/hold row color-coding SHALL work on portfolio rows.
- Trade toggle buttons SHALL adopt rebalance action-badge visual language.
- All changes SHALL use shared base classes from R30 (no duplicate rules).

**Non-Goals:**
- No behavior change: inline editing, delete confirm, trade toggles keep
  existing functionality.
- No template restructuring: 2-level header and class-totals-row stay.
- No new filter behavior (R31 handles that).
- No dark mode changes (covered by separate slices).

## Decisions

### D1: Inherit from R30 base classes, override only portfolio specifics

R30 creates `.data-table-shell`, `.data-table`, `.data-table-th`,
`.data-table-row`, `.data-table-cell` base classes. Portfolio's
`.portfolio-table-shell` and `.asset-table` SHALL inherit from these bases.
Only portfolio-specific overrides (grouped header, summary row, inline edit
cells) remain as explicit CSS rules.

**Why**: Avoids duplicating ~100 lines of shared styling. Future palette
changes in R30 variables propagate automatically.

**Alternative considered**: Copy-paste rebalance CSS into portfolio section.
Rejected: violates DRY, creates maintenance burden.

### D2: Add row-level buy/sell/hold classes to portfolio template

Rebalance uses `.rebalance-asset-row--buy`, `--sell`, `--neutral` classes
applied via Alpine `:class` binding. Portfolio SHALL emit equivalent classes
on each `<tr>` based on `buy_enabled` / `sell_enabled` flags.

**Mapping**:
- `buy_enabled && !sell_enabled` → `asset-row--buy`
- `!buy_enabled && sell_enabled` → `asset-row--sell`
- Both enabled or both disabled → `asset-row--neutral` (hold)

**Why**: Matches rebalance visual language. Uses existing Alpine data — no
server-side change needed.

### D3: Trade toggles get rebalance action-badge styling

The `.trade-toggle` buttons currently use their own color scheme. After this
slice, they SHALL inherit the `.rebalance-action-badge` visual language
(rounded pill shape, color-coded background at 12-18% opacity).

**Why**: Visual consistency. Buy = green pill, Sell = red pill, Hold = neutral.

### D4: class-totals-row palette harmonization

The summary row keeps its structure but its background, font-weight, and
border values SHALL come from the same CSS variables as the rebalance total
row. No structural change.

## Risks / Trade-offs

- **[Risk] R30/R31 not yet applied** → This slice depends on them. If F32
  starts before R30/R31 land, the CSS changes will need manual alignment
  later. Mitigation: roadmap enforces execution order.
- **[Risk] Regressions in inline editing** → Changing cell padding/styling
  could affect edit input sizing. Mitigation: keep `.asset-pct-cell--editing`
  rules explicit; test inline edit flow after CSS changes.
- **[Risk] Visual regression in existing tests** → E2E and visual regression
  baselines may break. Mitigation: regenerate visual baselines after apply.
- **[Trade-off] Row color-coding via template class vs CSS-only** → Template
  approach requires Alpine data binding change; CSS-only approach can't
  distinguish buy/sell from data attributes alone. Chose template approach
  for precision.
