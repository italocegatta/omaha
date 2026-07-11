## Context

F21 built an isolated comparison page for baseline custom, DataTables, Tabulator, and AG Grid Community. Owner reviewed result, selected AG Grid Community for F22, and directed removal of F21 page rather than shipping or retaining test surface.

## Final decision

### D1 — Discard F21 runtime PoC

Remove `/rebalanceamento/poc-tabelas`, its renderer and shared PoC payload helpers, Jinja template, PoC JS/CSS, vendored DataTables/Tabulator/AG Grid/jQuery assets, F21 selectors, and F21 tests. Restore pre-F21 rebalance page path unchanged.

Reason: F21 existed only to inform library decision. Its test page is not product capability.

### D2 — F22 implementation handoff only

F22, not F21, owns real rebalance table adoption. Owner selected **AG Grid Community**. Preserve official implementation guidance:

1. Use `defaultColDef` for shared `sortable`, `filter`, and `floatingFilter` settings.
2. Use `agNumberColumnFilter` for numeric range columns.
3. Use `agSetColumnFilter` for categorical columns.
4. Theme with AG Grid theming plus Omaha CSS/tokens.

No F22 runtime code, dependencies, or main-spec edits belong in this change.

## Non-goals

- Do not retain a test route or vendored AG Grid assets from F21.
- Do not sync F21 delta spec into main specs.
- Do not archive F21 in this cleanup; parent archives after validation.

## Rollback

No runtime feature is retained. Recreate implementation only through a new approved F22 apply.
