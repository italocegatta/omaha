## Context

Filter logic for table columns is duplicated across 3 JS locations and 2 HTML locations:

**JS duplication:**
- `rebalance.html` lines 366-486 (~120 lines) — filterActive, toggleFilterPanel, clearFilter, rangeBounds, rangeStep, ensureRangeBounds, clampRangeMin, clampRangeMax, rangeFillStyle, formatRangeValue, filteredRows getter
- `test/rebalance_table_poc.html` lines 346-494 (~150 lines) — near-identical copy
- `_patrimonio_add_asset_modal.html` lines 893-970 (~80 lines) — same methods with slight variation (uses `_mapField` for column→field mapping, `filterActiveStr` wrapper)

**HTML duplication:**
- `_rebalance_plan.html` lines 100-166 — inline enum/range/composite filter panels using Alpine x-if
- `rebalance.html` — same panels (the PoC duplicates them too)

**Existing shared infrastructure:**
- `_filter_controls.html` — Jinja2 macro used by portfolio (`_patrimonio_class_section.html`), supports teleport. Already calls the same Alpine method names (filterActive, toggleFilterPanel, etc.)
- `table-formatters.js` (R33) — ES module pattern for shared formatters. This slice follows the same pattern.

**Key difference between consumers:**
- Portfolio uses `_filter_controls.html` Jinja2 macro (compile-time rendering, teleport to body)
- Rebalance uses Alpine `x-if` runtime templates (no teleport, inline in `<th>`)
- Both call identical Alpine methods on their respective `x-data` components

## Goals / Non-Goals

**Goals:**
- Extract filter JS logic into `table-filters.js` ES module (same pattern as `table-formatters.js`)
- Extract filter HTML panels into `_table_filter_panels.html` Jinja2 partial
- Eliminate duplication across rebalance.html, _rebalance_plan.html, _patrimonio_add_asset_modal.html, and test/rebalance_table_poc.html
- Keep Alpine method signatures identical (zero breaking change to existing templates)
- Follow R33's module export pattern exactly

**Non-Goals:**
- Changing filter behavior or UI
- Modifying `_filter_controls.html` macro (it already works; it just calls Alpine methods)
- CSS changes (R30 already handled shared CSS)
- Touching portfolio's `_patrimonio_class_section.html` (it uses the macro, which stays)
- Unifying the Jinja2 macro vs Alpine x-if rendering strategies (both work; different contexts need different approaches)

## Decisions

### D1: ES module for JS, Jinja2 partial for HTML

**Choice:** `table-filters.js` as ES module (like `table-formatters.js`), `_table_filter_panels.html` as Jinja2 include.

**Rationale:** JS logic is pure computation — fits ES module export pattern. HTML panels are Jinja2/Alpine hybrid — fits partial include pattern. Both are already proven patterns in this codebase.

**Alternative considered:** Single Alpine plugin that registers all filter methods. Rejected — adds complexity, changes initialization pattern, and Alpine `x-data` function returns are the established pattern here.

### D2: Functions accept generic row source, not hardcoded `this.plan.asset_plan`

**Choice:** Filter functions take `(rows, columns, headerFilters, headerRangeFilters, options)` as parameters instead of reading from `this`.

**Rationale:** Rebalance reads from `plan.asset_plan`, portfolio reads from `assets` (with field mapping). Generic parameterization lets both consumers pass their own data source. The Alpine methods in each `x-data` become thin wrappers that call the shared functions with their specific data.

**Alternative considered:** Keep functions as Alpine method mixins. Rejected — harder to test, harder to share between components with different data shapes.

### D3: Keep `_filter_controls.html` macro unchanged

**Choice:** The portfolio macro stays as-is. It already calls the correct Alpine method names. After this slice, those methods will internally delegate to `table-filters.js`, but the macro doesn't need to know.

**Rationale:** Zero-change path for portfolio. The macro is already well-structured with teleport support and testid conventions.

### D4: HTML partial uses Alpine x-if templates (rebalance pattern)

**Choice:** `_table_filter_panels.html` contains the enum/range/composite panel markup using Alpine `x-if` templates. Portfolio's `_filter_controls.html` macro keeps its own markup (already different — uses teleport).

**Rationale:** The rebalance and PoC pages use `x-if` inline panels. Extracting those to a partial eliminates HTML duplication between rebalance.html and _rebalance_plan.html. The portfolio macro has different rendering needs (teleport) and stays separate.

## Risks / Trade-offs

**[Risk] Alpine method signature drift between consumers** → Mitigation: Shared functions define the canonical signatures. Each `x-data` wrapper passes its own data source. Integration tests (existing BDD/e2e) catch regressions.

**[Risk] `rangeBounds` data source varies** → Mitigation: `rangeBounds` accepts a `rows` array parameter. Rebalance passes `plan.asset_plan`, portfolio passes `assets`. Function stays pure.

**[Risk] `_patrimonio_add_asset_modal.html` has `filterActiveStr` wrapper and `_mapField` indirection** → Mitigation: Keep `filterActiveStr` and `_mapField` as local wrappers. The shared module provides the core logic; page-specific adapters stay local.

**[Risk] PoC file divergence** → Mitigation: PoC imports from `table-filters.js` just like production pages. Future PoC changes benefit from shared module automatically.
