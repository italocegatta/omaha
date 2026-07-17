## Why

F39 spacing changes revealed accumulated CSS maintenance debt in `app.css`.
Review found 12 issues: duplicate selectors, dead code, conflicting `:root`
blocks, and mixed units. The file has grown to 3754 lines with duplicate
blocks that silently override each other via cascade order — a source of
subtle bugs and wasted developer time tracing which declaration wins.

## What Changes

**High priority (duplicate selectors / conflicting blocks):**
1. Delete duplicate `.btn` / `.btn-primary` / `.btn:hover:not(:disabled)` block (lines 555-582) — exact copy of lines 525-553.
2. Consolidate triple `.class-section-header` into one declaration — keep F15's `display: block` (line 1842) as final state, remove dead grid at lines 1081-1115.
3. Merge two `:root` blocks with `--col-*` variables — the first (lines 89-98) uses percentages, the second (lines 1792-1807) uses pixels. Keep the pixel version (F15's final state), delete the percentage block.
4. Delete duplicate `@media (prefers-reduced-motion)` at lines 1265-1270 — the second block (lines 3522-3527) is the canonical one from F10.

**Medium priority (dead code):**
5. Remove duplicate `.dashboard-asset-list` rules (lines 636-645 dead, keep 1228-1258).
6. Delete duplicate `.muted` at line 1260 — identical to line 584.
7. Delete empty `.rebalance-card` block at lines 2862-2866.
8. Change `.section-divider` `margin: 24px 0` to `margin: 1.5rem 0` for unit consistency.

**Low priority (optional, not blocking):**
9. Remove dead `.dashboard-asset-list li` at lines 637-642 — superseded by 1229-1241.

## Capabilities

### New Capabilities
None — pure refactoring, no behavior change.

### Modified Capabilities
None — no spec-level behavior changes.

## Impact

- **File:** `src/omaha/static/app.css` — single file, CSS-only.
- **Risk:** Low — removing duplicate/dead rules. The surviving declarations are already the ones the browser applies (later in cascade wins). Removing the earlier duplicates changes nothing visually.
- **Verification:** `uv run task test-unit` must pass. Visual inspection via `refresh-for-test` to confirm no regressions.
