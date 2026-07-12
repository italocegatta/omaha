## Context

Rebalance page currently renders asset plan with custom handwritten table markup inside Jinja templates. F27 POC handoff defines target behavior: declarative Alpine column model, `x-for` rendered header/body, client-side sort/filter controls, PT-BR labels, and theme aligned to app tokens. Change is UI-only, but it touches core visible surface on `/rebalanceamento` and must stay aligned with existing rebalance data contract.

## Goals / Non-Goals

**Goals:**
- Ship POC-style declarative Alpine table on real rebalance page.
- Keep F27's eight-column order and its composite Desvio and Operação cells.
- Preserve existing rebalance data and row semantics.
- Replace bespoke table markup with one column model driving header/body/filter UI.
- Theme table with Omaha tokens and existing app CSS.

**Non-Goals:**
- No solver, route, or payload-shape changes.
- No import, seed, or profile behavior changes.
- No new server endpoints.

## Decisions

1. **Use single Alpine column model for header/body**
   - Rationale: handoff defines one eight-entry `columns` array as source of truth for labels, order, sort keys, filter type, and cell formatting.
   - Alternative: keep hardcoded header/body markup. Rejected: duplicates structure and makes parity drift likely.

2. **Keep server data contract intact**
   - Rebalance plan still arrives from existing server render/context; table consumes same row data and keeps stable row identity by `asset_key`.
   - Alternative: add API endpoint for table data. Rejected: unnecessary for current page flow.

3. **Keep sort/filter client-side in Alpine**
   - Shared component state manages `sortKey`, `sortDir`, `headerFilters`, and `headerRangeFilters`.
   - Enum columns use multi-select filters; range columns use min/max sliders; composite columns reuse range slots in same panel.
   - Alternative: server-side filtering/sorting. Rejected: extra round-trips and no POC parity.

4. **Theme through app tokens plus existing rebalance classes**
   - Table wrapper and header panels reuse `.rebalance-*` classes mapped to existing surface, border, ink, and positive/negative tokens.
   - Alternative: introduce new table design system. Rejected: unnecessary churn on already-stable page palette.

5. **Retire legacy hardcoded table markup after parity lands**
   - Old hand-written th/td blocks and stale control hooks are removed from official page once declarative version is in place.
   - Alternative: keep both systems in parallel. Rejected: confusing and redundant.

## Risks / Trade-offs

- **Declarative table logic may drift from POC** → keep column model + helpers aligned with handoff and cover key flows in tests.
- **Header filter panels may overflow small viewports** → use `panelAlign` plus existing left/right anchoring rules.
- **Search/filter composition can regress silently** → add tests for AND logic, empty-state, and representative sort/filter cases.
- **CSS reuse may miss dark-surface details** → validate against app tokens and existing rebalance classes before apply.

## Migration Plan

1. Replace hardcoded rebalance table markup with declarative Alpine column model.
2. Port POC sort/filter helpers into official rebalance component.
3. Align app CSS with token-driven table, header action, panel, and slider styles.
4. Update tests for declarative DOM and interaction parity.
5. Roll back by restoring previous template/CSS surface if parity regressions appear.

## Open Questions

- None.
