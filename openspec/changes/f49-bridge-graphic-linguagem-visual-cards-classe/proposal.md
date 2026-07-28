## Why

Runtime F49 failed visual approval: Alpine-generated SVG bars did not paint and labels collapsed. Owner directs corrective amendment inside F49. Runtime chart must reproduce approved mock's HTML/CSS plot geometry while retaining exact real production card shell/grid.

## What Changes

- Replace failed SVG runtime plot with fixed HTML/CSS plot children. Dynamic geometry and visible labels use CSS percentage custom properties on approved per-card local BRL scale; no Alpine `x-for` may render SVG bars, labels, ticks, grid, or connectors.
- Preserve BRL waterfall semantics: local `R$0` axis, nice ticks/grid, zero-anchored blue Atual/Alvo totals, floating green purchase/red sale/amber residual deltas, dashed cumulative connectors, and solid zero lines. No shared scale.
- Preserve exact production card shell/grid and use all available card content area for plot. No chart footer, status line, reconciliation prose, or supplementary card text.
- Remove page notice `Sugestões abaixo dos mínimos viram Manter.`. Remove all visible net-status content, including text/value `Compra/Venda líquida`; net trade remains compensated chart-stage data and aria-label-only semantics. Above/below state remains red/blue through chart/card treatment and aria-label, without visible status copy.
- Preserve approved BRL mapping, operation/residual percentage formula, colors, tolerance, unavailable behavior, asset-plan table, and literal Ações/FII acceptance semantics.
- Record approved runtime BRL mapping. Operation and Residual percentage labels SHALL be `round(abs(stage_brl) / total_final_planned * 100, 1)`, where `total_final_planned = sum(asset_plan.target_value)` over finite, unrounded BRL inputs. A configured class without matching asset-plan rows SHALL render `Dados indisponíveis para esta ponte`, never inferred `R$0` or a false waterfall.
- Owner approved waterfall grammar, corrected HTML/CSS runtime geometry, fixtures, percentage rule, and unavailable no-row behavior. Runtime corrective integration is unblocked; existing preview route may retain static mock evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rebalance-page`: Correct class-card BRL waterfall runtime contract to approved HTML/CSS plot geometry and remove rejected visible copy.

## Impact

- Corrective runtime candidates: `src/omaha/templates/_rebalance_plan.html`, `src/omaha/templates/rebalance.html`, `src/omaha/static/app.css`, focused page/visual tests. No routes, schema, solver, seed, asset-plan-table, config, or unrelated change.
- No dependency: fixed semantic HTML plus CSS plot primitives fit four stages and no chart lifecycle. ECharts and dynamic SVG excluded.
- Runtime contract: calculate operation/residual labels with `round(abs(stage_brl) / total_final_planned * 100, 1)` only when required BRL inputs and positive `total_final_planned` are finite; preserve unrounded values until display rounding. Zero operation/residual displays `0.0%`; missing, non-finite, or non-positive denominator displays `Dados indisponíveis para esta ponte` with no geometry. No matching asset-plan rows always uses same unavailable state.
