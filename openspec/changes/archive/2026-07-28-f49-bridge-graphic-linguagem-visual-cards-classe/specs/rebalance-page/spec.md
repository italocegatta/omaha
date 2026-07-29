## MODIFIED Requirements

### Requirement: Category summary renders as horizontal class cards

The system SHALL render category deviation summary as horizontal class cards, not table. Each card SHALL render class name and an approved fixed HTML/CSS per-class BRL waterfall. Its semantic stage order SHALL be `Atual → Compra/Venda líquida/Sem operação líquida → Residual → Alvo`; net-stage name/data SHALL appear only in plot aria-label, never as visible card net-status text/value.

Each card SHALL have local y-axis beginning at `R$0`, four or five visible nice BRL ticks, and horizontal grid lines. With full-precision finite values `C1=current_value`, `C2=C1+delta=projected_value`, `C3=C2+residual=target_value`, it SHALL calculate `M=max(C1,C2,C3)`, choose a nice step from `1, 2, 2.5, 5 × 10^n` plus three or four intervals, and set `ceiling=intervals×step` strictly greater than `M`. The card SHALL select lowest eligible ceiling then smallest step. No percentage SHALL affect geometry and no scale SHALL be shared between cards.

Runtime SHALL use fixed HTML plot elements and CSS percentage custom properties for dynamic bars and visible labels on same local BRL scale. It SHALL NOT use Alpine `x-for` inside SVG, nor runtime SVG primitives for bars, labels, ticks, grid, zero lines, or connectors. Atual and Alvo SHALL be blue total columns zero-anchored to C1 and C3. Compra/Venda líquida SHALL float from `min(C1,C2)` to `max(C1,C2)`; Residual SHALL float from `min(C2,C3)` to `max(C2,C3)`. Purchase delta SHALL be green, sale delta SHALL be red, and Residual SHALL be amber. Decorative connectors SHALL be dashed and show cumulative levels `C1 → C2 → C3`; zero lines SHALL be solid. Visible HTML labels SHALL use same local CSS-percentage scale. No fact SHALL require hover, color, or SVG alone.

Atual SHALL use category current BRL value. Compra/Venda líquida SHALL use signed category `delta = projected_value - current_value`: positive is Compra líquida, negative is Venda líquida, and `abs(delta) <= DISPLAY_TOLERANCE` is explicit Sem operação líquida. It SHALL summarize compensated asset trades and SHALL NOT be presented as executable class trade. Alvo SHALL use sum of matching existing asset-plan `target_value`; it SHALL NOT be calculated by multiplying `target_pct` by another portfolio denominator. Residual SHALL be `target - projected_value`, with `abs(residual) <= DISPLAY_TOLERANCE` rendered as explicit zero residual.

Runtime mapping SHALL define `total_final_planned=sum(asset_plan.target_value)` from finite, unrounded BRL inputs across complete plan. Operation and Residual percentage labels SHALL be, respectively, `round(abs(delta) / total_final_planned * 100, 1)` and `round(abs(residual) / total_final_planned * 100, 1)`. Existing `target_pct` uses a distinct current-portfolio denominator and SHALL NOT reconstruct target BRL or either percentage label. A zero operation/residual stage SHALL render explicit zero/hold copy, `R$ 0`, and `0.0%` when all required inputs and positive denominator are finite. Missing/non-finite required input, any non-finite target-value input, or `total_final_planned <= 0` SHALL render `Dados indisponíveis para esta ponte` and SHALL NOT render percentages or monetary geometry. Mock fixture percentages SHALL remain literal and non-derived.

A configured class with no matching asset-plan rows SHALL render `Dados indisponíveis para esta ponte`; it SHALL NOT infer a target of `R$0`, create a synthetic target row, calculate a residual from zero, or render a waterfall. When mapping is available, each card SHALL preserve exact production-card shell and state language: red when current value is above target, blue when current value is below target, and existing tolerance/neutral state at equality. Unavailable state SHALL not fabricate above/below classification.

Cards SHALL retain exact production-card shell/grid and `data-testid="rebalance-class-summary"`, wrapping small-viewport layout, CSS tokens, WCAG AA normal-text contrast, and 320px no-horizontal-overflow behavior. Plot SHALL fill all available content area in unchanged shell and SHALL NOT render a footer, status row, reconciliation equation, explanatory prose, or supplementary card copy. Plot aria-label SHALL identify class, red-above/blue-below state, and all four stage values including net trade. No visible card status text/value may duplicate above/below or net-trade semantics. Decorative connector/grid/zero-line marks SHALL be `aria-hidden="true"`; labels and values SHALL remain meaningful without color or SVG. Missing/non-finite required runtime input SHALL render explicit unavailable-data text and SHALL NOT be converted to zero or misleading hold geometry.

The following SHALL NOT render as substitute: generic percentage chart, current/projected overlay, target marker/dot, delta zero-anchored as total, old four boxed mini-bars, shared class scale, Alpine SVG template loop, runtime SVG chart primitive, visible `Compra/Venda líquida` net-status line/text/value, page notice `Sugestões abaixo dos mínimos viram Manter.`, or class-level executable trade control. Asset-plan table remains execution source and SHALL remain unchanged.

#### Scenario: Normative Ações monetary waterfall
- **WHEN** static approved fixture has Atual `R$100k / 14.6%`, Compra líquida `R$25k / 0.2%`, Residual `R$25k / 0.2%`, and Alvo `R$150k / 15%`
- **THEN** card visibly renders approved HTML/CSS plot geometry for Atual, residual, and Alvo, while net-stage name/data is present in plot aria-label only
- **AND** blue Atual/Alvo totals, two green floating deltas, and connectors reconcile `100 + 25 + 25 = 150` on card-local scale
- **AND** percentage text is paired information, not width/position

#### Scenario: Normative FII sale reaches target
- **WHEN** static approved fixture has Atual `R$120k / 15.2%`, Venda líquida `R$20k / 0.2%`, Residual `R$0 / 0%`, and Alvo `R$100k / 15%`
- **THEN** card visibly renders approved HTML/CSS plot geometry for Atual, residual, and Alvo, while net-stage name/data is present in plot aria-label only
- **AND** blue Atual/Alvo totals, red floating sale, and connectors reconcile `120 - 20 + 0 = 100` on card-local scale
- **AND** zero residual is named and does not become missing, target marker, tiny-dot indicator, or zero-anchored total

#### Scenario: Compensated operation is display-only
- **WHEN** category delta is positive, negative, or within display tolerance
- **THEN** plot aria-label names corresponding `Compra líquida`, `Venda líquida`, or no-net-operation state
- **AND** card renders no visible net-status line, text, or value
- **AND** card does not expose class-level buy or sell instruction
- **AND** asset-plan table remains available for executable per-asset suggestions

#### Scenario: Missing or boundary data remains truthful
- **WHEN** required monetary input is non-finite or unavailable
- **THEN** card shows explicit unavailable-data text and no fabricated monetary geometry
- **WHEN** configured class has no matching asset-plan rows
- **THEN** card shows `Dados indisponíveis para esta ponte`, not target `R$0` or a waterfall
- **WHEN** total final planned is non-finite or not positive
- **THEN** card shows `Dados indisponíveis para esta ponte`, not a rounded, omitted, or substituted denominator
- **WHEN** delta or residual absolute amount is within `DISPLAY_TOLERANCE`
- **THEN** card renders explicit zero/hold wording, BRL zero display, and `0.0%`

#### Scenario: Approved percentage labels use planned final total
- **WHEN** complete asset plan has finite unrounded `target_value` inputs and positive `total_final_planned`
- **THEN** operation label equals `round(abs(delta) / total_final_planned * 100, 1)` and residual label equals `round(abs(residual) / total_final_planned * 100, 1)`
- **AND** neither label derives from `target_pct`, rounded BRL, current portfolio total, or fixture percentages

#### Scenario: Corrective owner-approved runtime integration
- **WHEN** F49 runtime implementation begins
- **THEN** approved static Ações/FII fixture semantics, HTML/CSS plot geometry, percentage formula, and no-matching-asset-plan unavailable behavior are binding
- **AND** corrective runtime implementation MUST replace failed SVG loop geometry, remove rejected visible notice/status copy, and re-run targeted tests, visual baselines, full suite, and refresh receipt
