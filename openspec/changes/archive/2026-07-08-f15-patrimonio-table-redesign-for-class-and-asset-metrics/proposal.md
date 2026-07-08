## Why

Current `/patrimonio` table still reflects older dashboard contract: flat columns, class header pills aligned to legacy columns, partial sorting, and gain/deviation rendering that does not match the operator's newer reading model. The owner supplied a new mockup that makes class-vs-portfolio context readable in one scan, so this slice exists to turn that approved table model into the canonical contract before implementation.

## What Changes

- Rebuild the asset table column order and header grouping to match the approved mockup, including nested `Classe` and `Carteira` groups with `Atual`, `Alvo`, and `Desvio` subcolumns.
- Replace the current class header alignment contract with a class totals row that lines up against the new asset-table columns.
- Split `Ganho` into internal absolute and percentage subcells for alignment/formatting while preserving a single visible operator-facing column.
- Expand sorting so every visible data column is sortable, with alphabetical behavior for `Ativo` and ascending/descending numeric behavior for metric columns.
- Formalize per-column formatting rules: currency prefix by asset currency, percentage suffix, thousands separator, rounded absolute values, and one decimal for percentage/decimal metrics.
- Add positive/negative iconography and color signaling to `Desvio` and `Ganho`.
- Remove the legacy asset-row `Classe` column while keeping `Compra`, `Venda`, and `Moeda` behavior unchanged.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `class-section-totals`: replace the old flat alignment contract with grouped `Classe` / `Carteira` subheaders and a class totals row aligned to the new asset-table layout.
- `dashboard-inline-editing`: expand the sortable asset-table contract to the new column set, remove the legacy `Classe` column, and redefine CSS-variable-driven column proportions for the redesigned table.
- `patrimonio-portfolio-header`: preserve the three top-level metrics while updating `Ganho` presentation to use separate absolute/percentage subcells plus sign-state iconography.

## Impact

- `src/omaha/templates/_patrimonio_class_section.html` — new grouped `<thead>`, class totals row, redesigned asset cells, updated testids/selectors.
- `src/omaha/templates/_patrimonio_portfolio_header.html` — `Ganho` split layout and sign-state presentation.
- `src/omaha/templates/_patrimonio_add_asset_modal.html` — Alpine sort state, formatting helpers, and inline-edit interactions must survive the new column contract.
- `src/omaha/routes/pages.py` — aggregate payload extended/re-shaped for gain, deviation, average price, quantity, and currency-aware formatting inputs.
- `src/omaha/static/app.css` — new table/group widths, visually-merged `Ganho` cells, grouped headers, icon/color states, and alignment rules.
- `tests/integration/`, `tests/bdd/`, `tests/e2e/` — update selectors and assertions for grouped headers, sorting, formatting, and sign indicators.
- No schema or seed-path change expected: current models already persist quantity, average price, invested/current totals, targets, trade flags, and currency.
