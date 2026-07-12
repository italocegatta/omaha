## Why

The rebalance page still carries handcrafted table markup that diverges from F27 POC handoff. F22 lands the validated declarative Alpine table on `/rebalanceamento`, so sort/filter parity and PT-BR presentation reach the real page without changing rebalance data contract.

## What Changes

- Replace current rebalance asset-plan surface with POC-style declarative Alpine table on `/rebalanceamento`.
- Keep F27's eight visible columns in order: Ação, Classe, Ativo, Atual, Alvo, Desvio, Projetado, Operação. Desvio and Operação remain composite cells.
- Render `<thead>` and `<tbody>` from shared column model via `x-for`, keeping row hooks and PT-BR labels stable.
- Restore POC parity for column sorting and per-column filters on client side.
- Integrate table with official rebalance route/template flow and theme it with app tokens / existing `rebalance-*` CSS.
- Remove legacy hardcoded table/filter markup from official page after parity lands.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `rebalance-page`: rebalance plan table contract changes to declarative Alpine/x-for rendering with client-side sort and filters on the official page.

## Impact

- `src/omaha/templates/rebalance.html`
- `src/omaha/templates/_rebalance_plan.html`
- `src/omaha/static/app.css`
- `src/omaha/routes/rebalance.py`
- Rebalance page tests/selectors that target old table/filter DOM
- No API, solver, or data-model contract changes expected
