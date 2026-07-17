## Context

`app.css` has 3754 lines accumulated over 14+ feature/refactoring slices (F02-F39, R30-R34). Each slice added CSS but rarely cleaned up predecessors. Result: duplicate selectors, dead code, conflicting `:root` blocks, mixed units (px vs rem vs %).

F39 spacing changes exposed this debt — the review found 12 concrete issues. This slice cleans them up surgically.

## Goals / Non-Goals

**Goals:**
- Remove all duplicate CSS selectors (where later-in-cascade block silently overrides earlier)
- Remove dead CSS rules (superseded by later slices, no longer referenced by templates)
- Consolidate conflicting `:root` blocks into one
- Standardize units on `.section-divider` (px → rem)
- Reduce file size by ~100-150 lines

**Non-Goals:**
- No new CSS variables or design tokens
- No refactoring of live selectors
- No visual changes — output must be pixel-identical
- No template changes
- No extraction of spacing variables (nice-to-have, deferred)

## Decisions

### D1 — Keep later declarations, delete earlier duplicates

**Decision:** When two identical selectors exist, keep the one that appears later in the file (the one the browser actually applies). Delete the earlier one.

**Rationale:** CSS cascade means later declarations win. The later block is what developers have been visually testing against. Removing it would require re-verification; removing the earlier one changes nothing.

### D2 — Keep F15's `:root` pixel block, delete original percentage block

**Decision:** The `:root` block at lines 1792-1807 (F15, pixels) supersedes the one at lines 89-98 (percentages). Keep pixels, delete percentages.

**Rationale:** F15 redesigned the patrimonio table with fixed-width columns in pixels. The percentage-based variables from the original layout are no longer consumed by any template. The pixel version is the active one.

### D3 — Keep F15's `display: block` class-section-header, remove dead grid

**Decision:** The `.class-section-header` at line 1842 (`display: block`) is F15's final state. The grid version at lines 1081-1115 is dead code — F15 replaced the grid layout with a simpler block layout.

**Rationale:** The grid was for the old class-section header with aligned column stats. F15 moved those stats into the table itself. The header is now a simple block with name + chevron + delete button.

### D4 — Keep F10's `@media (prefers-reduced-motion)`, delete S05's

**Decision:** The block at lines 3522-3527 (F10, `transition: none; animation: none`) is more complete than the one at lines 1265-1270 (S05, `animation-duration: 0.01ms; transition-duration: 0.01ms`). Keep F10's.

**Rationale:** `none` is cleaner than `0.01ms`. Both achieve the same user-facing result (no motion), but `none` is the canonical CSS pattern. The F10 block came later and is the one documented in the design system.

### D5 — `.section-divider` margin: 24px → 1.5rem

**Decision:** Change `margin: 24px 0` to `margin: 1.5rem 0` for unit consistency with the rest of the file.

**Rationale:** 24px = 1.5rem at default 16px root font. The file uses rem everywhere else for spacing. This is the only px-based margin on a generic component.

## Risks / Trade-offs

**[Risk] Cascade order matters — removing earlier duplicate could expose a hidden dependency.**
→ Mitigation: Each duplicate was verified by reading the later block and confirming it has identical or superseding properties. No earlier block has properties not present in the later one.

**[Risk] `--col-*` percentage variables might be used somewhere not obvious.**
→ Mitigation: Grep for `var(--col-` confirms only the `:root` blocks and `.class-section-header` grid reference them. The grid is dead code (D3). Safe to remove.

**[Risk] `.dashboard-asset-list` at lines 636-645 might be needed for a page not visible in templates.**
→ Mitigation: The rules at lines 1228-1258 supersede them completely (same selectors, more specific styles). No template references the old styles.
