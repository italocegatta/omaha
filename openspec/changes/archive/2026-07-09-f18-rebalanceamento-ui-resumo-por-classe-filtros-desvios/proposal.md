## Why

The current rebalance page renders 6 metric cards (Aporte, Comprar, Vender,
Caixa residual, Desvio atual, Desvio projetado) that don't help the operator
make decisions. The aporte input takes full width. The asset table has no
filters and no per-asset deviation columns. The operator cannot quickly see
which classes are off-target, by how much, or which assets need action.

## What Changes

1. **Remove 6 metric cards** — replace with horizontal class deviation summary
   cards (one per AssetClass) showing current%, target%, deviation (pp + R$),
   projected%. Color-coded: green within threshold, red outside.

2. **Compact parameter bar** — aporte input + two new threshold inputs
   (desvio mínimo R$ default 1000, desvio mínimo % default 1%) + Rebalancear
   button. All inline, width auto (not full-width).

3. **Extend wire format** — add `target_pct`, `current_pct`, `deviation_pct`
   to `RebalanceCategoryPlanRow`; add `deviation_value`, `deviation_pct` to
   `RebalanceAssetPlanRow`. These are computed fields (no DB schema change).

4. **Asset table redesign** — add columns Desvio(R$) and Desvio(%), add
   multi-select checkbox filters for Classe and Ação columns, add text search
   for asset name. All columns remain sortable. Rows color-coded by deviation
   vs threshold.

5. **Alpine component refactor** — reactive state for thresholds, filters,
   computed filteredRows, class-card color logic.

6. **CSS** — remove `.rebalance-stat-grid`, add styles for params-bar,
   class-cards, filter-bar, deviation cells, row color-coding.

## Capabilities

### Modified Capabilities

- `rebalance-page`: Requirements change for metric cards (removed), category
  summary (new class cards), asset table (new columns, filters, row coloring),
  parameter bar (new threshold inputs), wire format consumption (new fields).
- `rebalance-route`: Wire format extends with 5 new computed fields
  (target_pct, current_pct, deviation_pct on category rows; deviation_value,
  deviation_pct on asset rows). No endpoint changes.

### New Capabilities

None — this modifies existing capabilities only.

## Impact

- `src/omaha/rebalance/schemas.py` — 5 new optional fields on Pydantic models
- `src/omaha/rebalance/glue.py` — compute % and deviations before response
- `src/omaha/templates/_rebalance_plan.html` — full rewrite
- `src/omaha/templates/rebalance.html` — Alpine refactor
- `src/omaha/static/app.css` — remove stat-grid, add new component styles
- Tests: `tests/test_rebalance_page.py`, `tests/test_rebalance_route.py` will
  need updates for new schema fields and changed template structure
- No DB migration (computed fields only)
- No new dependencies
