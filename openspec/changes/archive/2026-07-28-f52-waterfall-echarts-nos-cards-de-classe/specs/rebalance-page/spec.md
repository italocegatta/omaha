## MODIFIED Requirements

### Requirement: Category summary renders as horizontal class cards

The system SHALL render category deviation summary as horizontal class cards, not table. Each card SHALL render class name and an Apache ECharts per-class BRL monetary waterfall that reproduces the owner-approved mock visual contract (`src/omaha/templates/rebalance_bridge_mock.html`) as amended by the owner directives encoded in this requirement (adaptive axis floor, hidden y-axis labels, blank zero-operation x-axis name, Inter weight 300 chart text). Its semantic stage order SHALL be `Atual → Compra/Venda → Desvio → Alvo`; net-stage name/data SHALL appear only in plot aria-label, never as visible card net-status text/value.

Each card SHALL have a card-local y-axis with an adaptive floor and ceiling on nice round numbers; it SHALL NOT be anchored at `R$0`. With full-precision finite levels `C1=current_value`, `C2=projected_value`, `C3=Alvo=Σ matching asset_plan.target_value`, it SHALL calculate `L=min(C1,C2,C3)` and `M=max(C1,C2,C3)`, choose ONE nice step from `1, 2, 2.5, 5 × 10^n` targeting three to five intervals over the span `M−L`, set `floor` to the LARGEST step multiple strictly below `L`, and set `ceiling` to the SMALLEST step multiple strictly above `M`. A level within a relative tolerance of `1e-9` of a step multiple SHALL count as exact, so the strict bound moves one more interval outward. The card SHALL select the tightest eligible range (`ceiling−floor`) then the finer step. When the level span is zero or non-positive, the step SHALL derive from the level magnitude — the smallest family member at least `max(|L|,|M|,1)/4` — bracketed by the same strict bounds. Y-axis tick labels SHALL be hidden; horizontal splitLines SHALL render on every tick. No percentage SHALL affect geometry and no scale SHALL be shared between cards.

Runtime SHALL render the chart as one ECharts instance per available card, driven by ONE shared JavaScript render helper that consumes the existing `window.__rebalancePlan` payload. The waterfall SHALL be built as a stacked bar chart with a transparent base series: `Atual` and `Alvo` SHALL be total bars rebased on the card's adaptive floor and rising to C1 and C3 (geometry only — labels, connectors, and aria-label SHALL keep the true absolute values), colored `--class-1`; `Compra` SHALL float from `min(C1,C2)` to `max(C1,C2)` colored `--positive`; `Venda` SHALL float colored `--negative`; non-zero `Desvio` SHALL float from `min(C2,C3)` to `max(C2,C3)` colored `--alert-warn`. A stage whose absolute value is within `DISPLAY_TOLERANCE` SHALL render its `R$ 0` + `0%` label without bar geometry. Cumulative connectors SHALL be dashed lines showing levels `C1 → C2 → C3` and SHALL have no endpoint dots or markers. Bar width SHALL be 45% of the category column, centered. All chart colors SHALL resolve from CSS design tokens at render time (no hardcoded color values; WCAG AA, DESIGN.md §6). Tooltip SHALL be disabled; no fact SHALL require hover, color, or canvas alone. The render helper SHALL NOT reposition labels manually — the library SHALL handle label layout and collision.

Stage names SHALL appear ONLY on the x-axis, centered below their own bar; the zero-net-operation stage SHALL render a blank x-axis category name (no visible label) while its aria-label keeps the full `Sem operação líquida`. All chart text — x-axis names and bar labels — SHALL use the page UI typeface Inter at true weight 300. Bar labels SHALL contain ONLY the absolute value in short scale plus the percentage. Every numeric bar label SHALL use PT-BR short scale — thousands with suffix `k`, one decimal (`R$ 113.746,00` → `R$ 113,7k`); values below one thousand SHALL render integral. Delta labels SHALL carry explicit sign (`+R$ 25,0k` / `-R$ 20,0k`). Percentage labels SHALL use PT-BR formatting with at most one decimal (`14,6%`, `0,2%`, `15%`, zero as `0%`).

`Atual` SHALL use category current BRL value. `Compra`/`Venda` SHALL use signed `delta = projected_value - current_value`: `delta > ε` is Compra, `delta < −ε` is Venda, `abs(delta) <= ε` is an explicit no-net-operation stage, with `ε = DISPLAY_TOLERANCE = 0.0001`. It SHALL summarize compensated asset trades and SHALL NOT be presented as executable class trade. `Alvo` SHALL use sum of matching existing asset-plan `target_value`; it SHALL NOT be calculated by multiplying `target_pct` by another portfolio denominator. `Desvio` SHALL be `target - projected_value`, with `abs(desvio) <= ε` rendered as explicit zero residual.

Runtime mapping SHALL define `total_final_planned=sum(asset_plan.target_value)` from finite, unrounded BRL inputs across complete plan. `Atual`/`Alvo` percentage labels SHALL use allocation over `total_final_planned`. Operation and Desvio percentage labels SHALL be, respectively, `round(abs(delta) / total_final_planned * 100, 1)` and `round(abs(desvio) / total_final_planned * 100, 1)`. Existing `target_pct` uses a distinct current-portfolio denominator and SHALL NOT reconstruct target BRL or any percentage label.

Missing/non-finite required input, any non-finite target-value input, or `total_final_planned <= 0` SHALL render `Dados indisponíveis para esta ponte` and SHALL NOT instantiate an ECharts instance, render percentages or monetary geometry, or infer `R$0`. A configured class with no matching asset-plan rows SHALL render the same unavailable state; it SHALL NOT infer a target of `R$0`, create a synthetic target row, calculate a residual from zero, or render a waterfall. Unavailable state SHALL not fabricate above/below classification.

When mapping is available, each card SHALL preserve exact production-card shell and state language: red accent when current value is above target, blue when below, existing tolerance/neutral state at equality — communicated only via card border treatment and `aria-label`, never via chart background or visible status text. Cards SHALL retain exact production-card shell/grid and `data-testid="rebalance-class-summary"`, wrapping small-viewport layout, CSS tokens, WCAG AA normal-text contrast, and 320px no-horizontal-overflow behavior. The chart SHALL fill all available content area in unchanged shell and SHALL NOT render a footer, status row, reconciliation equation, explanatory prose, or supplementary card copy. The chart container SHALL carry `role="img"` and an aria-label identifying class, red-above/blue-below state, and all four stage values including net trade. The chart SHALL resize with its container (ResizeObserver or equivalent) without horizontal overflow. Manual waterfall DOM/CSS (`.rebalance-waterfall-*`, `.rebalance-bridge-svg/-track/-residual/-marker/-legend`) SHALL be removed; dead selectors SHALL NOT remain in `app.css`.

The following SHALL NOT render as substitute: generic percentage chart, current/projected overlay, target marker/dot, delta zero-anchored as total, old four boxed mini-bars, shared class scale, SVG/Alpine template loop, manual HTML/CSS waterfall geometry with hand-positioned labels, tooltip-only information, stage names repeated on bars, visible `Compra/Venda líquida` net-status line/text/value, page notice `Sugestões abaixo dos mínimos viram Manter.`, class-level executable trade control, hardcoded chart colors, and CDN-loaded chart runtime. Asset-plan table remains execution source and SHALL remain unchanged. The mock route `/rebalanceamento/bridge-mock` and `rebalance_bridge_mock.html` SHALL remain untouched during implementation and SHALL be retired only after owner approval of the ECharts version side-by-side.

#### Scenario: Normative Ações monetary waterfall

- **WHEN** static approved fixture has Atual `R$100k / 14,6%`, Compra líquida `+R$25k / 0,2%`, Desvio `+R$25k / 0,2%`, and Alvo `R$150k / 15%`
- **THEN** card renders an ECharts canvas with blue Atual/Alvo totals, two green floating deltas, and dashed connectors reconciling `100 + 25 + 25 = 150` on card-local scale
- **AND** y-axis spans an adaptive nice floor strictly below `R$100k` and a nice ceiling strictly above `R$150k`, with tick labels hidden and a horizontal splitLine on every tick
- **AND** stage names appear only on the x-axis and bar labels carry only short-scale value + percentage
- **AND** net-stage name/data is present in chart aria-label only

#### Scenario: Normative FII sale reaches target

- **WHEN** static approved fixture has Atual `R$120k / 15,2%`, Venda líquida `-R$20k / 0,2%`, Desvio `R$ 0 / 0%`, and Alvo `R$100k / 15%`
- **THEN** card renders an ECharts canvas with blue Atual/Alvo totals and a red floating sale, reconciling `120 - 20 + 0 = 100` on card-local scale
- **AND** y-axis spans an adaptive nice floor strictly below `R$100k` and a nice ceiling strictly above `R$120k`, with tick labels hidden and splitLines on every tick
- **AND** zero desvio renders its `R$ 0` + `0%` label without bar geometry, and does not become missing, target marker, tiny-dot indicator, or zero-anchored total

#### Scenario: Short scale is mandatory on all numeric labels

- **WHEN** any bar label formats a BRL value (y-axis tick labels are hidden)
- **THEN** values ≥ 1000 render as `R$ <n>,<d>k` with one PT-BR decimal and values < 1000 render integral
- **AND** deltas carry explicit sign and percentages use PT-BR formatting with at most one decimal

#### Scenario: Compensated operation is display-only

- **WHEN** category delta is positive, negative, or within display tolerance
- **THEN** chart aria-label names corresponding `Compra líquida`, `Venda líquida`, or no-net-operation state
- **AND** card renders no visible net-status line, text, or value
- **AND** card does not expose class-level buy or sell instruction
- **AND** asset-plan table remains available for executable per-asset suggestions

#### Scenario: Missing or boundary data remains truthful

- **WHEN** required monetary input is non-finite or unavailable
- **THEN** card shows explicit unavailable-data text and no ECharts instance is created
- **WHEN** configured class has no matching asset-plan rows
- **THEN** card shows `Dados indisponíveis para esta ponte`, not target `R$0` or a waterfall
- **WHEN** total final planned is non-finite or not positive
- **THEN** card shows `Dados indisponíveis para esta ponte`, not a rounded, omitted, or substituted denominator
- **WHEN** delta or desvio absolute amount is within `DISPLAY_TOLERANCE`
- **THEN** card renders the stage label `R$ 0` and `0%` without bar geometry

#### Scenario: Approved percentage labels use planned final total

- **WHEN** complete asset plan has finite unrounded `target_value` inputs and positive `total_final_planned`
- **THEN** operation label equals `round(abs(delta) / total_final_planned * 100, 1)` and desvio label equals `round(abs(desvio) / total_final_planned * 100, 1)`
- **AND** neither label derives from `target_pct`, rounded BRL, current portfolio total, or fixture percentages

#### Scenario: One shared render helper on vendored runtime

- **WHEN** the rebalance page renders N available class cards
- **THEN** exactly one ECharts instance per available card is created by one shared render helper, with colors resolved from CSS design tokens and tooltip disabled
- **AND** the ECharts runtime is served from the application's own static vendor path, not a CDN
- **AND** charts resize with their containers without horizontal overflow at 320px
- **AND** no manual label repositioning logic exists in the helper

### Requirement: Rebalance class summary cards SHALL share one card family with target-state accents

The system SHALL render rebalance class summary cards as one consistent card family: same shell, same internal hierarchy, same spacing rhythm, and same typography treatment across all classes. Cards SHALL not rely on a repeated kicker label such as `CLASSE`; the class name is the primary header text.

Cards SHALL encode target relationship with color cues on the shared shell: classes above target SHALL use a red accent — a 3px top border in `--negative` (`oklch(0.717 0.124 19.4)`) plus a `6%` `--negative` surface tint (`color-mix(in srgb, var(--negative) 6%, var(--surface))`); classes below target SHALL use a blue accent — a 3px top border in `--class-1` (`oklch(0.742 0.104 265.7)`) plus a `6%` `--class-1` surface tint (`color-mix(in srgb, var(--class-1) 6%, var(--surface))`). A class at target (within tolerance) SHALL keep the neutral shell top border (`var(--border)`). Visual differences between cards SHALL come from state accenting, not from changing the underlying card mold.

#### Scenario: All class cards share the same family structure

- **WHEN** the rebalance page renders class summary cards
- **THEN** each card uses the same shell, header hierarchy, and metric layout
- **AND** no card introduces a different structural mold for a different state

#### Scenario: Above-target class renders with red accent

- **WHEN** a class is above its target allocation
- **THEN** its summary card renders with a red top-border accent (`--negative`) and a 6% red surface tint
- **AND** the card remains part of the shared card family

#### Scenario: Below-target class renders with blue accent

- **WHEN** a class is below its target allocation
- **THEN** its summary card renders with a blue top-border accent (`--class-1`) and a 6% blue surface tint
- **AND** the card remains part of the shared card family

#### Scenario: Card header does not repeat kicker label

- **WHEN** a class summary card renders
- **THEN** the header shows the class name as primary text
- **AND** the label `CLASSE` does not render in the card header
