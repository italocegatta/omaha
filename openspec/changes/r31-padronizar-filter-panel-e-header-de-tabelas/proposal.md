## Why

Rebalance and portfolio tables implement filter panels with fundamentally different strategies: rebalance renders filter panels inline inside `<th>` (positioned `absolute` relative to the header cell), while portfolio uses `x-teleport="body"` with a JavaScript `filterPanelStyle()` function for dynamic viewport positioning. Both share the same CSS classes (`.rebalance-filter-panel--header`, `.rebalance-header-actions`, `.rebalance-range-slider`, etc.) but the HTML structure and Alpine binding patterns diverge. This means filter UX bugs must be fixed twice, and adding a new filterable table requires copying ~60 lines of macro/template code with no guaranteed parity.

The `asset_filter_controls` Jinja macro in `_patrimonio_class_section.html` is a reusable extraction candidate — but it's currently locked to the portfolio template and uses the teleport pattern. Unifying both tables to use the same filter component (macro or Alpine component) eliminates duplication and ensures any future table gets filters for free.

## What Changes

- **Extract a reusable filter panel component**: Transform the `asset_filter_controls` macro (and the equivalent inline code in `_rebalance_plan.html`) into a single shared Jinja macro or Alpine component that both tables consume
- **Unify positioning strategy**: Both tables should use the same approach — either both inline (relative to `<th>`) or both teleported. Inline positioning (rebalance's current approach) is simpler and avoids the `filterPanelStyle()` JavaScript; teleport is needed only when the panel would clip. Decision: use inline positioning with `position: absolute` relative to `<th>` (which already has `position: relative`), and only fall back to teleport if overflow clipping occurs
- **Align filter icon**: Rebalance uses `material-symbols-outlined` (`filter_alt`), portfolio uses Material Symbols (`expand_more`). Unify to one icon (likely `filter_alt` for clarity)
- **Align panel alignment classes**: Rebalance uses `--left` / `--right` modifiers; portfolio hardcodes `--left`. The shared component should accept an alignment parameter
- **Share CSS classes from R30's base**: Filter panel styles (`.rebalance-filter-panel--header`, `.rebalance-header-actions`, `.rebalance-range-slider`, etc.) already exist in `app.css` and are shared. This slice ensures the HTML structure is also shared

## Capabilities

### New Capabilities

- `shared-filter-panel`: Reusable Jinja macro (or Alpine component) for column filter panels in sortable tables. Covers enum filters (checkboxes), range filters (dual slider), and composite filters (multiple ranges). Includes trigger button, clear button, panel container, and all Alpine bindings. Both rebalance and portfolio tables consume this single component.

### Modified Capabilities

_(none — no spec-level behavior changes; this is a template/CSS refactor)_

## Impact

- **Templates**: `_patrimonio_class_section.html` (replace `asset_filter_controls` macro with shared component), `_rebalance_plan.html` (replace inline filter markup with shared component)
- **CSS** (`src/omaha/static/app.css`): minor adjustments if icon unification changes class names; filter panel CSS classes stay as-is (already shared via R30)
- **JS/Alpine**: `filterPanelStyle()` may be removed if inline positioning works for both tables; `toggleFilterPanel()`, `clearFilter()`, `filterActive()` etc. stay unchanged
- **No behavior change**: all existing filter functionality preserved (enum, range, composite)
- **No breaking change**: `data-testid` attributes preserved for existing tests
