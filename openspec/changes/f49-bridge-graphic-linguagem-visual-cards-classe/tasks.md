## 1. Replacement static BRL-waterfall mock — only permitted initial Apply work

- [x] 1.1 Replace rejected fixture mock only. Render actual per-class BRL waterfall chart with local y-axis at `R$0`, four or five nice BRL ticks, horizontal grid, ceiling at next nice tick above max(Atual, Projetado, Alvo), and no shared scale.
- [x] 1.2 Render exact literal Ações and FII fixtures without deriving paired percentages. Show stage names and BRL/% labels visibly, total blue Atual/Alvo columns zero-anchored, floating signed operation/residual columns, cumulative connectors C1→C2→C3, and visible equations `100 + 25 + 25 = 150` and `120 - 20 + 0 = 100`.
- [x] 1.3 Owner visual inspection target for replacement mock at desktop, 320px, and dark token theme: no horizontal overflow; 4–5 legible axis ticks/grid; non-color semantic text; decorative chart marks; WCAG AA normal-text token pairs; zero FII residual; and no generic percentage chart, overlay, target dot, zero-anchored delta total, four mini-bars, shared scale, tooltip-only fact, or executable class trade. No automated test or validator is required for this POC.
- [x] 1.4 Keep mock fixture-only and explicitly non-integrated. Existing preview route may serve updated mock; do not add/change production route, runtime card, runtime data, template/CSS, tests, validators, evidence automation, visual baselines, schema, solver, seed, or asset-plan table.

## 2. Owner-approval checkpoint — completed

- [x] 2.1 Orchestrator presented fixture browser evidence, exact Ações/FII literals, visual grammar, and runtime decisions to owner.
- [x] 2.2 Owner explicitly approved waterfall grammar, fixtures, corrected HTML/CSS runtime geometry, operation/residual labels `round(abs(stage_brl) / total_final_planned * 100, 1)` with finite unrounded `total_final_planned=sum(asset_plan.target_value)`, and `Dados indisponíveis para esta ponte` for configured class with no matching asset-plan rows.
- [x] 2.3 Approval is recorded. Sections 3–4 are unblocked; no later task may replace approved formula or no-row behavior.

## 3. Corrective runtime mapping and HTML/CSS waterfall reimplementation

- [x] 3.1 Reimplement approved BRL mapping: `C1=current_value`; `delta=projected_value-current_value`; `C2=C1+delta`; `target=sum(matching asset_plan.target_value)`; `residual=target-C2`; `C3=C2+residual`. Retain finite unrounded inputs until display. Define `total_final_planned=sum(asset_plan.target_value)` over finite unrounded BRL inputs; label operation/residual `round(abs(stage_brl) / total_final_planned * 100, 1)` only when denominator is finite and positive. Never derive target BRL or labels from `target_pct`.
- [x] 3.2 Replace failed runtime SVG with approved fixed HTML/CSS plot geometry. Dynamic bars and visible labels SHALL use CSS percentages on same local BRL scale. Do not use Alpine `x-for` inside SVG or runtime SVG bar/label/grid/connector primitives. Preserve exact production-card shell/grid, plan form, category sorting, `rebalance-asset-section`, asset table, and solver output.
- [x] 3.3 Implement plot grammar: local 0-origin axis, 4–5 ticks/grid, next-nice-tick ceiling, solid zero lines, blue zero-anchored totals, green purchase/red sale floating net delta, amber residual, and dashed cumulative connectors. Plot fills all available card content area; no footer, status, equations, or prose.
- [x] 3.4 Remove `Sugestões abaixo dos mínimos viram Manter.`. Remove visible card net-status line/text/value, including `Compra/Venda líquida`; retain net trade only as chart-stage data/name in aria-label. Preserve red-above/blue-below state via chart/card treatment and aria-label, without visible status text/value.
- [x] 3.5 Reimplement unavailable and boundary states: configured class with no matching asset-plan rows always renders `Dados indisponíveis para esta ponte`, no target `R$0`, no synthetic row, and no waterfall; missing/non-finite required value or non-finite/non-positive denominator does same. Valid zero operation/residual remains truthful in chart aria-label; apply `DISPLAY_TOLERANCE` only to display state.

## 4. Corrective regression and visual evidence

- [x] 4.1 Add/replace focused rendered-page tests proving painted real HTML/CSS bars, CSS-percentage local geometry, visible labels, four-stage aria semantics, local BRL scaling, 4–5 ticks/grid, solid zero lines, dashed connectors, red-above/blue-below aria state, preserved formulas/colors/missing behavior, asset-table preservation, and Ações/FII semantics.
- [x] 4.2 Add assertions that page notice is absent; visible card net-status row/text/value `Compra/Venda líquida` is absent; no runtime SVG template loop exists; no card footer/status/prose exists; and plot consumes full available unchanged-card content area.
- [x] 4.3 Update visual baselines; capture approved desktop, 320px, and dark-mode evidence. Verify labels do not collapse and bars paint. Run targeted taskipy test lanes, then `task test` full suite.
- [x] 4.4 Invoke `refresh-for-test` after corrective runtime template/CSS work and emit required delivery receipt.
