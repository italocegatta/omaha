## Why

F21 compared table-library approaches against rebalance plan data before changing product UI. Owner selected AG Grid Community for follow-up F22 and explicitly rejected shipping F21 test page.

## Outcome

- F21 runtime PoC is discarded: no protected `/rebalanceamento/poc-tabelas` route, Jinja page, PoC JS/CSS, sole-use vendored libraries, selectors, or PoC tests remain.
- F21 is retained only as decision/discovery record. It does not add shipped capability and its delta spec must not sync into main specs.
- F22 owns real-table implementation. This change does not implement F22.

## Decision record for F22

Owner selected **AG Grid Community**. Preserve these official guidance findings for F22 implementation planning:

- Configure common `sortable`, `filter`, and `floatingFilter` behavior through `defaultColDef`.
- Use `agNumberColumnFilter` for numeric range filtering.
- Use `agSetColumnFilter` for categorical values.
- Apply product theme through AG Grid theming and application CSS/tokens.

## Capabilities

### New Capabilities
- None shipped. `rebalance-table-library-poc` is a discarded discovery artifact.

### Modified Capabilities
- None.

## Impact

- Removed F21-only route, template, assets, vendored libraries, tests, and selector inventory.
- Main OpenSpec capability specs remain unchanged; F21 delta spec is intentionally unsynced.
