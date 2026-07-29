## Context

Current F49 runtime uses Alpine-generated SVG and failed visual approval: bars do not paint and labels collapse. Owner directs corrective reimplementation inside F49. Runtime must use approved mock's fixed HTML/CSS plot geometry inside exact existing production-card shell/grid.

Confirmed BRL sources:

| Display datum | Runtime source/calculation | Unit/sign | Notes |
|---|---|---|---|
| Atual / C1 | `RebalanceCategoryPlanRow.current_value`; constructed in `glue.py:194-214` from native category aggregate | BRL, non-negative | First total column. |
| Compra/Venda líquida / C2 | `delta = projected_value - current_value` | BRL; positive purchase/net increase, negative sale/net decrease | `C2 = C1 + delta`; compensated aggregate only. Asset table remains executable detail. |
| Alvo / C3 | Sum `asset_plan.target_value` where `category_name` matches card | BRL, non-negative | `C3 = target`; category wire row has no target BRL. |
| Residual | `target - projected_value` | BRL; positive remaining increase, negative remaining decrease | `C3 = C2 + residual`; zero within tolerance. |

Define future `total_final = sum(asset_plan.target_value)` across complete plan. Existing `target_pct` is derived in `glue.py:187-204` with `total_portfolio`, while target BRL comes from asset-plan `target_value`; its denominator is not `total_final` when portfolio final value differs from current total. Therefore neither `target_pct × total_final` nor percentage labels supplied in owner fixtures can derive stage BRL. Runtime target remains asset-plan aggregation unless approved wire change adds an explicit field.

Owner-approved runtime percentage rule:

```text
total_final_planned = sum(asset_plan.target_value)
operation_pct = round(abs(delta) / total_final_planned * 100, 1)
residual_pct  = round(abs(residual) / total_final_planned * 100, 1)
```

The sum uses finite, unrounded BRL `asset_plan.target_value` inputs. Do not pre-round, coerce, omit, or substitute a non-finite input. The rule is defined only when every required card source and `total_final_planned` are finite and `total_final_planned > 0`; otherwise card uses unavailable state.

## Goals / Non-Goals

**Goals:**
- Implement owner-approved monetary sequence after isolated static browser mock evidence.
- Render chart through fixed HTML/CSS stages with local BRL y-axis, grid, floating deltas, totals, dashed cumulative connectors, solid zero lines, and approved visible labels.
- Preserve accessibility, dark-token theming, 320px fit, asset-plan table, server contracts, solver, and unrelated page behavior.

**Non-Goals:**
- Alpine `x-for` inside SVG; runtime SVG bars/labels/grid/connectors; generic percentage chart; current/projected overlay; target marker/dot; delta zero-anchored as total; old four boxed mini-bars; shared scale; tooltip; zoom; pan; animation; chart dependency.
- Class-level trade instruction, schema/solver/postprocessing rewrite, and changes to asset-plan table.
- Page notice `Sugestões abaixo dos mínimos viram Manter.`, any visible net-status row/text/value `Compra/Venda líquida`, or chart footer/status/prose.
- Changes outside production class-card internals, page notice removal, focused tests, visual baseline, and delivery verification.

## Requirements-Fidelity Ledger

| Literal requirement | Perceived semantic | Required rendering | Source/calculation | Forbidden reinterpretation | Evidence |
|---|---|---|---|---|---|
| `Atual → Compra/Venda líquida → Desvio residual → Alvo` | Monetary reconciliation | Four ordered chart stages; net stage semantics exposed only in chart aria-label | Table above | Current/projected overlay or target marker | Rendered Ações/FII card |
| Geometry driven by BRL, locally referenced to current | Length means money inside this card only | HTML/CSS bars/connectors use local BRL-derived CSS percentages; labels use same scale | Table above | Percentage-position geometry or cross-card comparison | Same fixture cards show independent local scaling |
| Percent values paired labels | Percent informs, not encodes shape | Every stage shows approved `%` textual companion | Current/target sources plus approved operation/residual formula | Percent-only chart | Fixture text and owner approval |
| Net operation compensated | Summary cannot be executed | Signed floating bar; stage name/data only in chart aria-label; asset table retained | `delta` | Visible `Compra/Venda líquida` status or `Comprar/Vender classe` order | aria-label and asset table |
| Inclusive visual access | Meaning survives color/SVG failure | HTML/CSS plot, labels, token contrast, aria-label | DOM/CSS tokens | Color-only state, SVG-only facts, or visible status prose | Browser 320px/dark checks |

## Decisions

### 1. Fixed semantic HTML/CSS monetary waterfall; no dependency

Use fixed semantic HTML elements and CSS plot primitives. Alpine may calculate/card-bind values but SHALL NOT use `x-for` inside SVG; runtime SHALL NOT rely on SVG for bars, labels, ticks, grid, zero lines, or connectors. Fixed four-stage flow needs no external chart lifecycle, legend, interaction, bundle, or theme adapter. ECharts rejected unless owner requests unavailable requirements: interactive inspection, reusable chart infrastructure, or many comparative series.

Runtime emits fixed plot children for axis/ticks, solid zero line, Atual total, net-trade delta, residual delta, Alvo total, and dashed connectors. It writes local-scale results to CSS custom properties such as `--bar-start`, `--bar-end`, `--bar-height`, `--label-position`, and `--connector-level`; CSS percentages position and size bars/labels in the plot. No geometry derives from percentage labels. This is approved mock geometry, not a second SVG interpretation.

### 2. Local BRL waterfall geometry

Each card computes from full-precision finite BRL values:

```text
C1 = current_value
C2 = C1 + delta = projected_value
C3 = C2 + residual = target_value
M  = max(C1, C2, C3)
```

Its y-axis begins at `R$0`. Select a BRL nice step from `1, 2, 2.5, 5 × 10^n` and an interval count `N ∈ {3, 4}` such that `ceiling = N × step > M`; select lowest ceiling, then smallest step. Axis labels are `0, step, … ceiling`: four or five visible nice BRL ticks. This is strict next-tick headroom even when `M` already equals a tick. Grid lines span chart plot horizontally at every tick. Each card calculates independently: no shared scale and no percentage affects geometry.

Stage x-order is Atual, internal net trade, Residual, Alvo. Atual and Alvo are blue total columns extending from zero to C1/C3. Net operation floats from `min(C1, C2)` to `max(C1, C2)`; Residual floats from `min(C2, C3)` to `max(C2, C3)`. Purchase is green, sale is red, and Residual is amber. Dashed decorative connectors trace cumulative levels `C1 → C2 → C3`; zero lines are solid. Atual, Residual, and Alvo labels are visible HTML labels positioned through same local CSS-percentage scale. Net-stage name and data are exposed only through plot aria-label; card SHALL render no visible `Compra líquida`, `Venda líquida`, `Sem operação líquida`, or net value/status line. Plot consumes full available content area within unchanged card shell; no footer, status, equation, explanatory prose, or extra card copy may consume space.

### 3. Numeric rules

- Retain full-precision finite source values for calculation; round only displayed BRL with existing PT-BR currency formatter to zero centavos unless source precision/copy approval changes it.
- Use existing `DISPLAY_TOLERANCE = 0.0001` (`postprocessing.py:39-50`, `glue.py:37`) as epsilon: `abs(delta) <= epsilon` means `Sem operação líquida`; `abs(residual) <= epsilon` means `Sem desvio residual` and display `R$ 0`.
- `delta > epsilon`: Compra líquida; `delta < -epsilon`: Venda líquida. It is aggregate display math, even when underlying asset buys/sells offset.
- `residual > epsilon`: remaining net increase; `residual < -epsilon`: remaining net decrease. Do not expose either as executable instruction.
- Operation and Residual percentage labels SHALL use approved formula `round(abs(stage_brl) / total_final_planned * 100, 1)`, where `stage_brl` is respectively unrounded `delta` or `residual` and `total_final_planned = sum(asset_plan.target_value)` from finite, unrounded BRL inputs across complete plan. Do not use `target_pct`, current portfolio total, fixture percentage, rounded BRL, or a per-card denominator.
- `abs(delta) <= epsilon` and `abs(residual) <= epsilon` are valid zero stages: render their explicit state, `R$ 0`, and `0.0%` under approved formula. They are not unavailable solely because stage amount is zero.
- Missing/non-finite required input, any non-finite target-value input contributing to `total_final_planned`, or `total_final_planned <= 0` is not zero. Runtime card MUST use visible `Dados indisponíveis para esta ponte`, omit amount geometry and percentage labels, retain class name and exact production-card shell, and preserve asset table.
- A configured class without any matching asset-plan rows MUST use `Dados indisponíveis para esta ponte`; it MUST NOT infer target `R$0`, calculate residual from zero, substitute a synthetic plan row, or render waterfall geometry.

### 4. Static fixtures are literal; runtime decisions approved

Mock uses literal owner fixtures. It MUST NOT derive their internally illustrative percentage pairs: Ações `R$100k/14.6%`, `R$25k/0.2%`, `R$25k/0.2%`, `R$150k/15%`; FII `R$120k/15.2%`, `R$20k/0.2%`, `R$0/0%`, `R$100k/15%`. It visibly prints reconciliation `100 + 25 + 25 = 150` and `120 - 20 + 0 = 100`.

Owner approved these runtime decisions:

1. **Operation/residual percentage denominator.** Display `round(abs(stage_brl) / total_final_planned * 100, 1)`, with `total_final_planned = sum(asset_plan.target_value)` using finite unrounded BRL inputs. This does not reconstruct literal fixture percentages.
2. **Configured target class with no matching asset-plan rows.** Render `Dados indisponíveis para esta ponte`; never infer an `R$0` target or render a waterfall.

Owner also approved waterfall grammar, literal fixtures, and corrected HTML/CSS runtime geometry. Runtime corrective integration is unblocked.

### 5. Production-card shell and visual states

Replace only card internals and remove named page notice. Preserve exact production-card shell/grid, class name, sorting, `data-testid`, and asset-plan section. Plot fills card's existing available content area. When target mapping is available, retain red-above/blue-below state treatment with existing tolerance/neutral state; aria-label SHALL identify above/below state without visible card status text/value. Waterfall colors remain independent: blue total bars, green purchase delta, red sale delta, amber residual. Unavailable state does not fabricate above/below classification.

### 6. Accessibility and responsive grammar

Visible plot labels use HTML and CSS percentages, never tooltip-only. Plot aria-label SHALL include class, above/below state, and four-stage semantic values including net trade; it is sole semantic presentation of net-stage name/data. Dashed connectors, grid, and solid zero lines are decorative (`aria-hidden="true"`). Token foreground/background pairs MUST meet WCAG AA 4.5:1 for normal text in dark token theme. Layout stacks or reflows without horizontal overflow at 320px; no fact depends only on geometry, color, hover, or SVG.

## Normative Static Fixtures

| Card | Atual | Compra/Venda líquida | Desvio residual | Alvo |
|---|---|---|---|---|
| Ações | `R$100k / 14.6%` | `Compra líquida R$25k / 0.2%` | `R$25k / 0.2%` | `R$150k / 15%` |
| FII | `R$120k / 15.2%` | `Venda líquida R$20k / 0.2%` | `R$0 / 0%` | `R$100k / 15%` |

Fixture geometry follows BRL reconciliation: Ações `100 + 25 + 25 = 150`; FII `120 - 20 + 0 = 100`. Literal paired percentages are fixture display acceptance, not inferred arithmetic.

## Risks / Trade-offs

- [Runtime mapping violates approved formula] → reject implementation; focused tests cover unrounded finite numerator/denominator, one-decimal rounding, zero stage, and unavailable inputs.
- [Compensated trades look executable] → no visible net status, retain net semantics in aria-label only, and retain asset table.
- [Target BRL mapping accidentally uses percentage] → aggregate matching asset `target_value`; focused integration test verifies source.
- [No matching target rows silently become zero] → render approved unavailable state; focused test proves no target `R$0` or geometry.
- [Zero/missing data misread as hold] → distinct zero and unavailable copy; no fabricated geometry.
- [Narrow/dark rendering loses meaning] → 320px and dark rendered evidence plus WCAG AA token audit before runtime acceptance.

## Migration Plan

Phase 1 static mock/fixtures and browser evidence are complete. Prior runtime attempt is rejected. Corrective Phase 2 reimplements template/CSS/client plot geometry; no data migration. Roll back corrective work by reverting production template/CSS/client changes.

## Open Questions

None. Owner approved mock HTML/CSS geometry, fixture semantics, operation/residual percentage formula and rounding, and no-matching-asset-plan unavailable behavior. Implementation must not reopen these decisions.
