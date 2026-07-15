## Context

Two tables in the app — rebalance plan (`_rebalance_plan.html`) and portfolio assets (`_patrimonio_class_section.html`) — implement column filter panels with divergent strategies:

**Rebalance** (`_rebalance_plan.html` lines 100-168):
- Filter panels rendered inline inside `<th>` via `<template x-if>`
- Panels positioned `absolute` relative to `<th>` (which has `position: relative` via `.rebalance-table-th--has-filter`)
- Column config-driven: `columns` array defines `{key, type, panelAlign, label, format, ranges}` for each column
- Filter types: `enum` (checkboxes), `range` (dual slider), `composite` (multiple ranges)
- Icon: `material-symbols-outlined` → `filter_alt` / `close`
- Alignment: `--left` / `--right` modifier classes

**Portfolio** (`_patrimonio_class_section.html` lines 1-57):
- `asset_filter_controls` Jinja macro generates filter button + clear button + teleported panel
- Uses `x-teleport="body"` to escape `<th>` overflow clipping
- JavaScript `filterPanelStyle()` computes `position: fixed` coordinates dynamically
- Filter types: `enum` (checkboxes), `range` (dual slider)
- Icon: Material Symbols → `expand_more` / `close`
- Alignment: hardcoded `--left`

Both share CSS classes in `app.css` (`.rebalance-filter-panel--header`, `.rebalance-header-actions`, `.rebalance-range-slider`, `.rebalance-filter-option`, etc.) — the visual style is already unified. The divergence is in HTML structure and positioning strategy.

**Why teleport exists in portfolio**: The portfolio table has `overflow: hidden` on the class section body (`.class-section-body` with `max-height` transition). Teleporting the filter panel to `<body>` avoids clipping. Rebalance has no such overflow constraint.

## Goals / Non-Goals

**Goals:**
- Single reusable Jinja macro for filter panels consumed by both tables
- Unified positioning strategy (inline `absolute` when possible, teleport as fallback)
- Unified icon set (one icon for filter trigger, one for clear)
- Preserve all existing filter functionality (enum, range, composite)
- Preserve `data-testid` attributes for existing tests

**Non-Goals:**
- Changing filter logic or Alpine component behavior (sort, filter, range)
- Adding new filter types
- Changing table structure or column layout
- Touching R30's shared CSS base (complementary, not dependent)

## Decisions

### D1: Shared Jinja macro (not Alpine component)

Use a Jinja macro as the shared unit. The macro generates the filter button + clear button + panel HTML with Alpine bindings. Both templates import and call the macro.

**Rationale**: Alpine components require a wrapping `x-data` which conflicts with the existing `x-data` on `<th>`. Jinja macros are zero-runtime-cost and generate the same HTML. The macro approach matches the existing `asset_filter_controls` pattern.

**Alternative considered**: Alpine `x-data` component registered globally. Rejected: adds JS complexity, requires `$dispatch` or store coordination with the parent table component, and doesn't reduce HTML output.

### D2: Inline positioning with conditional teleport

Default: inline `position: absolute` relative to `<th>` (rebalance's current approach). This works when the `<th>` ancestor has no `overflow: hidden`.

For portfolio: the `.class-section-body` has `overflow: hidden` from the collapse animation. Two options:

**Option A (recommended)**: Keep teleport for portfolio only. The macro accepts a `teleport` boolean parameter. When `true`, wraps the panel in `<template x-teleport="body">` and uses `filterPanelStyle()`. When `false` (default), renders inline.

**Option B**: Remove `overflow: hidden` from `.class-section-body` and use CSS `clip-path` or `visibility` instead. Rejected: changes animation behavior, higher regression risk.

Decision: **Option A** — macro parameter `teleport=false` (default) for rebalance, `teleport=true` for portfolio. The `filterPanelStyle()` JS stays for the teleport case only.

### D3: Icon unification to `filter_alt`

Rebalance uses `filter_alt` (clear intent: "filter this column"). Portfolio uses `expand_more` (ambiguous: could mean "expand" or "dropdown"). Unify to `filter_alt` for both.

Both use `material-symbols-outlined`. The `close` icon stays for the clear button.

### D4: Macro signature

```jinja
{% macro filter_controls(key, label, filter_kind='enum', align='left', teleport=false, ranges=none) %}
```

Parameters:
- `key`: column key (string) — matches Alpine state keys
- `label`: human-readable label for tooltips (string)
- `filter_kind`: `'enum'`, `'range'`, or `'composite'` — determines which panel template renders
- `align`: `'left'` or `'right'` — panel alignment modifier class
- `teleport`: boolean — whether to wrap in `x-teleport="body"`
- `ranges`: list of range configs (only for `composite` type) — each `{key, label, format}`

The macro handles all three filter types in a single template with `x-if` branching, matching the current rebalance pattern.

### D5: File placement

The shared macro lives in a new partial: `src/omaha/templates/_filter_controls.html`. Both templates import it:
```jinja
{% from '_filter_controls.html' import filter_controls %}
```

**Alternative**: inline the macro in `_patrimonio_class_section.html` (current location) and import from there. Rejected: couples rebalance to a portfolio partial. A dedicated file is cleaner.

## Risks / Trade-offs

- **[Risk] Portfolio overflow clipping on teleport removal** → Mitigated by D2: keep teleport for portfolio. The macro parameter makes this explicit.
- **[Risk] `filterPanelStyle()` drift** → The JS function stays but is only called when `teleport=true`. If it breaks, only portfolio filters are affected (same as today). Rebalance filters are pure CSS-positioned.
- **[Risk] Macro parameter mismatch** → Each table has different filter types per column. The macro signature with `filter_kind` and `ranges` handles this; callers pass the right config.
- **[Trade-off] Extra file** → One new template partial. Acceptable for the DRY benefit across two tables + any future table.
- **[Trade-off] Conditional teleport in same macro** → Slightly more complex macro with `x-if`/`x-teleport` branching. But the alternative (two macros) defeats the purpose of unification.
