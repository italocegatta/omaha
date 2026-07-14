## 1. Shared macro creation

- [ ] 1.1 Create `src/omaha/templates/_filter_controls.html` with the `filter_controls(key, label, filter_kind, align, teleport, ranges)` Jinja macro
- [ ] 1.2 Implement enum filter branch: trigger button + clear button + `<template x-if="filterKind('{{ key }}') === 'enum'">` with checkbox list (Todos/Todas + `uniqueHeaderValues`)
- [ ] 1.3 Implement range filter branch: dual slider with track, fill, min/max value labels
- [ ] 1.4 Implement composite filter branch: multiple labeled range sliders separated by section dividers
- [ ] 1.5 Implement conditional teleport: when `teleport=true`, wrap panel in `<template x-teleport="body">` and use `filterPanelStyle('{{ key }}')`; when `false`, render inline with `position: absolute`
- [ ] 1.6 Apply alignment modifier: `rebalance-filter-panel--left` or `rebalance-filter-panel--right` based on `align` parameter

## 2. Portfolio template migration

- [ ] 2.1 In `_patrimonio_class_section.html`: replace `asset_filter_controls` macro with `{% from '_filter_controls.html' import filter_controls %}` import
- [ ] 2.2 Replace all `{{ asset_filter_controls('key', 'Label') }}` calls with `{{ filter_controls('key', 'Label', filter_kind='enum', teleport=true) }}` (or `range` where applicable)
- [ ] 2.3 Replace `expand_more` icon in the macro calls with `filter_alt` (handled by the shared macro)
- [ ] 2.4 Remove the old `asset_filter_controls` macro definition from `_patrimonio_class_section.html`

## 3. Rebalance template migration

- [ ] 3.1 In `_rebalance_plan.html`: add `{% from '_filter_controls.html' import filter_controls %}` import
- [ ] 3.2 Replace the inline filter markup inside `<template x-for="column in columns">` with `{{ filter_controls(column.key, column.label, filter_kind=column.type, align=column.panelAlign, ranges=column.ranges if column.type == 'composite') }}` — note: this needs Jinja/Alpine bridge since `column` is Alpine runtime data, not Jinja server data
- [ ] 3.3 If 3.2 is not feasible (Alpine runtime vs Jinja server-time conflict): keep the rebalance filter markup inline but extract the filter panel HTML into the shared macro and use Alpine `x-html` or `<template x-if>` to conditionally render the macro output. Alternatively, keep rebalance inline and only unify portfolio.
- [ ] 3.4 Verify `data-testid` attributes match existing patterns (`rebalance-header-filter-<key>-trigger`, `rebalance-header-clear-<key>-trigger`, `rebalance-header-filter-<key>-panel`)

## 4. CSS adjustments

- [ ] 4.1 Verify `.rebalance-filter-panel--header`, `.rebalance-header-actions`, `.rebalance-range-slider` CSS classes work for both tables without changes (they should, since both already use these classes)
- [ ] 4.2 If portfolio filter icon changes from `expand_more` to `filter_alt`, verify icon renders correctly at the same size (both are Material Symbols, same font)
- [ ] 4.3 Verify `z-index: 100` on `.asset-table .rebalance-filter-panel--header` still applies correctly with the shared macro

## 5. Verification

- [ ] 5.1 Run `task test-unit` — no regressions
- [ ] 5.2 Run `task test-bdd` — filter-related BDD scenarios pass
- [ ] 5.3 Run `task lint` — no new lint errors
- [ ] 5.4 Manual browser check: open rebalance page, verify filter panels open/close, enum/range/composite filters work, clear works
- [ ] 5.5 Manual browser check: open portfolio page, verify filter panels open/close (teleported), enum/range filters work, clear works, panels don't clip under `.class-section-body` overflow
- [ ] 5.6 Verify `data-testid` attributes resolve in browser DevTools for both tables
