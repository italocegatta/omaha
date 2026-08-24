# Spec: rebalance-page

## Purpose

Render the v1 rebalance plan on a dedicated URL
(`/rebalanceamento`), fed by a form that lives in the body of the
page only (no sidebar, no global slot). Consumes the wire contract
defined in `openspec/specs/rebalance-route/spec.md` (no new server
endpoints are added — the page calls `run_rebalance()` server-side
via the existing glue module).

This spec is the page's contract — Phase 4 (`rebalance-engine`)
swaps the solver stub for the real CVXPY solver, and the page
renders the result automatically because it consumes the wire
format the route already defines.

The legacy URL `/rebalance` is no longer served (404, no alias).

## Requirements

### Requirement: GET /rebalanceamento renders the rebalance plan page

The system SHALL expose `GET /rebalanceamento` (PT-BR slug, `D1`)
that returns HTTP 200 with the rendered `rebalance.html` template.
Auth follows the project standard (`require_user` +
`require_active_profile`).

When the active profile has zero `AssetClass` rows, the main
content area renders an empty-state card; the in-body form is
present but inert (the input + button carry `disabled`).
When the profile has classes, the main area SHALL render the
materialized rebalance plan using the active profile's persisted
aporte value. If no aporte was persisted yet for that profile, the
system SHALL use `0` as the default contribution and render the
resulting plan immediately.

The previous URL `/rebalance` is no longer served — requests to
`/rebalance` return HTTP 404. No alias, no redirect.

#### Scenario: Authenticated user with empty profile sees empty state

- **WHEN** the authenticated user has no active profile OR the
  active profile has zero `AssetClass` rows
- **AND** `GET /rebalanceamento` is called
- **THEN** the response is HTTP 200
- **AND** the main area contains an element with
  `data-testid="rebalance-empty-state"`
- **AND** the in-body form's input has the `disabled` attribute
- **AND** the in-body form's submit button has the `disabled`
  attribute

#### Scenario: Populated profile with no prior aporte renders zero plan

- **WHEN** the active profile has at least one `AssetClass` row
- **AND** no aporte was persisted yet for that profile in the current session
- **AND** `GET /rebalanceamento` is called
- **THEN** the response is HTTP 200
- **AND** the main area contains an element with
  `data-testid="rebalance-plan"`
- **AND** the rendered plan reflects `metrics.contribution = 0`

#### Scenario: Returning to page reuses persisted aporte and fresh data

- **WHEN** the active profile has at least one `AssetClass` row
- **AND** the operator previously submitted aporte `5000`
- **AND** portfolio data changed before the next `GET /rebalanceamento`
- **THEN** the response is HTTP 200
- **AND** the main area contains `data-testid="rebalance-plan"`
- **AND** the rendered plan reflects `metrics.contribution = 5000`
- **AND** the plan is recomputed from current persisted classes/assets/positions,
  not reused from an older serialized snapshot

#### Scenario: Unauthenticated request bounces to /login

- **WHEN** `GET /rebalanceamento` is called without a valid session
- **THEN** the response is HTTP 303 to `/login` (FastAPI default
  for `require_user` failure)

#### Scenario: Legacy /rebalance URL returns 404

- **WHEN** `GET /rebalance` is called
- **THEN** the response is HTTP 404
- **AND** no automatic redirect to `/rebalanceamento` is performed

### Requirement: POST /rebalanceamento renders the plan

The system SHALL expose `POST /rebalanceamento` that reads
`contribution` from the in-body form, resolves it as the active
profile's current aporte, and calls `run_rebalance()`. The success
path SHALL follow POST/Redirect/GET (PRG): the handler SHALL persist
the submitted finite contribution for the active profile in the
current session, then respond with HTTP 303 See Other to
`/rebalanceamento` (no query string — the active profile is
session-bound). The POST response SHALL NOT render the plan; the
browser follows with `GET /rebalanceamento`, which renders
`rebalance.html` with a fresh `RebalancePlanResponse` recomputed from
the persisted aporte and the default thresholds.

When the field is blank or missing, the handler SHALL normalize it to
`0` instead of rendering an error, and the success path SHALL still
redirect (303). On a non-finite (`NaN` / `inf`) or non-numeric
contribution, on a malformed threshold field, or when
`run_rebalance()` raises `RebalanceValidationError`, the handler SHALL
render the page directly with HTTP 200 and an inline `form_error` —
no redirect, no 4xx — so the message survives the round-trip.

Submitted thresholds are ephemeral: they are consumed by the POST-time
computation but SHALL NOT be persisted; after the redirect the GET
recomputes with the defaults (`1000.0` / `1.0`) and the threshold
inputs re-render at defaults. Only the aporte survives the PRG
(per-profile, in session; see F52 design D13).

#### Scenario: Valid finite contribution redirects and persists the aporte

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = 5000.00`
- **THEN** the response is HTTP 303 See Other with
  `Location: /rebalanceamento`
- **AND** the POST response does NOT render the plan
- **AND** the follow-up `GET /rebalanceamento` for the same active
  profile is HTTP 200 and the main area contains an element with
  `data-testid="rebalance-plan"` rendering the compact parameter bar,
  horizontal class summary cards, and the asset plan table
- **AND** the rendered plan reflects `metrics.contribution = 5000.00`
- **AND** the rendered plan is computed with the default thresholds
  (abs `1000`, pct `1`)

#### Scenario: Blank contribution is normalized to zero and redirects

- **WHEN** `POST /rebalanceamento` is called with an empty
  `contribution` field
- **THEN** the response is HTTP 303 See Other to `/rebalanceamento`
- **AND** the follow-up `GET /rebalanceamento` renders the plan
  section reflecting `metrics.contribution = 0`

#### Scenario: Zero contribution is a valid rebalance plan

- **WHEN** `POST /rebalanceamento` is called with `contribution = 0`
- **THEN** the response is HTTP 303 See Other to `/rebalanceamento`
  (zero is the rebalance-only case — no new money, just
  reallocation)
- **AND** the follow-up GET renders the zero-contribution plan

#### Scenario: Negative contribution is accepted server-side

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = -1000.00`
- **THEN** the response is HTTP 303 See Other to `/rebalanceamento`
  (server is permissive per the contract extension; the page
  client-side gates this for v1 with explanatory copy)

#### Scenario: NaN contribution re-renders with form error

- **WHEN** `POST /rebalanceamento` is called with `contribution = NaN`
- **THEN** the response is HTTP 200 with the page rendered (no
  redirect)
- **AND** the main area shows an element with
  `data-testid="rebalance-form-error"` containing
  "Use um número finito"
- **AND** the plan section is NOT rendered

#### Scenario: Solver validation failure renders inline error

- **WHEN** `run_rebalance()` raises `RebalanceValidationError`
  with message "Classes devem somar 100%"
- **THEN** the response is HTTP 200 with the page rendered (no
  redirect)
- **AND** the form error element contains the validation
  message

### Requirement: Client-side validation rejects negative aporte

The system SHALL block form submission when `contribution < 0`
on the client side, displaying an inline error before the
POST round-trip. Server-side accepts negative (per the
`rebalance-route` contract extension), but the page UI is
more restrictive for v1.

The error renders inside the in-body form (no sidebar element
exists any more; see `dashboard-sidebar` REMOVED delta).

#### Scenario: Negative aporte shows client error before submit

- **WHEN** the user types `-1000` in the aporte input
- **AND** presses Enter
- **THEN** the form does NOT submit (no POST round-trip)
- **AND** an element with `data-testid="rebalance-form-error"`
  (in-body, not `sidebar-form-error`) shows the message
  "Saques serão suportados em versão futura. Por enquanto,
  deixe o aporte em zero ou positivo."

### Requirement: Asset plan table renders eight POC-parity columns plus a data attribute

The system SHALL render the rebalance asset plan with a single declarative Alpine column model. The `<thead>` and `<tbody>` SHALL be generated from that model via `<template x-for>`, with no duplicated header/body markup. The table SHALL expose F27 POC's eight visible columns, in order: `Ação`, `Classe`, `Ativo`, `Atual`, `Alvo`, `Desvio`, `Projetado`, `Operação`. `Desvio` SHALL combine value and percentage; `Operação` SHALL combine action, value, and quantity. The quantity subvalue SHALL render with 0 decimal places for non-BTC assets and 3 decimal places for BTC assets. Null or unavailable quantities SHALL remain blank.

The table container SHALL keep `data-testid="rebalance-asset-table"` so existing tests can target the plan surface. Each rendered row SHALL retain a stable `data-asset-key` attribute equal to `asset_key`.

When `plan.asset_plan` is empty, the page SHALL keep the existing empty-state behavior instead of rendering an empty table.

#### Scenario: Declarative table renders eight POC-parity columns

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-asset-table"` exposes eight visible columns in POC order
- **AND** each rendered row carries `data-asset-key`

#### Scenario: BTC quantity renders with 3 decimal places

- **WHEN** the rendered operation cell belongs to `asset_name = BTC` and `trade_quantity = 1.23456`
- **THEN** the quantity subvalue renders with 3 decimal places
- **AND** the operation cell still combines action, BRL amount, and quantity in one visible column

#### Scenario: Empty plan still renders empty state

- **WHEN** `plan.asset_plan` is empty
- **THEN** the empty-state copy renders instead of an empty grid

### Requirement: Rebalance plan SHALL expose visual table cues without changing its interaction contract

When `plan.asset_plan` is non-empty, the page SHALL render exactly one `data-testid="rebalance-asset-table"` with existing eight-column Alpine generation, filters, sorting, row keys, action badges, and data. That table SHALL additionally expose the existing sticky-header hook and row-wide hover feedback. When the plan is empty, existing empty-state behavior SHALL remain unchanged.

#### Scenario: Populated plan keeps one table and existing columns
- **WHEN** a valid rebalance plan with assets renders
- **THEN** exactly one `data-testid="rebalance-asset-table"` is present
- **AND** it retains `data-table rebalance-table` plus existing `table-sticky-header`
- **AND** existing filter triggers, sort handlers, row `data-asset-key` values, and action content remain present

#### Scenario: Rebalance row hover is temporary and row-wide
- **WHEN** the pointer enters any rendered rebalance asset row
- **THEN** all cells in that row use the existing hover background for the duration of hover
- **AND** moving the pointer away restores the row’s pre-hover zebra or action-state background
- **AND** no row selection, tooltip, navigation, mutation, or data transformation occurs

#### Scenario: Rebalance header sticks without internal scroll
- **WHEN** the user scrolls the page containing a populated rebalance plan
- **THEN** the table header remains visible at the viewport top with existing header/filter styling
- **AND** the page does not gain a new nested scroll region or alter table columns/layout

#### Scenario: Empty asset plan remains empty state
- **WHEN** `plan.asset_plan` is empty
- **THEN** `data-testid="rebalance-asset-table-empty"` renders as before
- **AND** no sticky or hover table is created

### Requirement: Rebalance page Alpine component
The `rebalancePage()` Alpine component SHALL consume formatters from the shared `table-formatters.js` module instead of defining them inline. The component's method signatures and return values SHALL remain identical to the pre-refactor implementation.

#### Scenario: Formatter output unchanged after refactor
- **WHEN** the rebalance page renders with the same plan data
- **THEN** all formatted values (BRL amounts, percentages, quantities, action labels, row classes, cell classes) produce identical output to the pre-refactor version

#### Scenario: Shared module imported once
- **WHEN** the rebalance page loads
- **THEN** `table-formatters.js` is imported exactly once via `<script type="module">`

### Requirement: Sortable asset plan table

The system SHALL sort and filter rebalance asset plan rows client-side in Alpine. Clicking a column header SHALL toggle `asc → desc → asc` on the same column. Categorical columns SHALL use multi-select enum filters. Numeric columns SHALL use range filters with min/max bounds. Composite columns SHALL expose multiple range controls within the same filter panel.

The page SHALL keep PT-BR labels and SHALL NOT render legacy handcrafted table/filter controls that are no longer part of the declarative surface.

#### Scenario: Clicking a numeric column sorts ascending

- **WHEN** the user clicks the `Atual` header
- **THEN** rows are reordered by `current_value` ascending

#### Scenario: Filters compose with AND logic

- **WHEN** class filter selects `Renda Fixa` AND action filter selects `Comprar`
- **THEN** only rows matching all criteria remain visible

### Requirement: Action column renders translated badges

The system SHALL render the `action` field as a square badge
(border-radius 4px, bg-color sutil, ink forte) with PT-BR
labels: `Comprar` (green), `Vender` (red), `Manter` (neutral).

#### Scenario: Buy action renders green badge

- **WHEN** an asset plan row has `action = "buy"`
- **THEN** the cell renders a badge with the `Comprar` label
  and the `.rebalance-action-badge--buy` class

#### Scenario: Sell action renders red badge

- **WHEN** an asset plan row has `action = "sell"`
- **THEN** the cell renders a badge with the `Vender` label
  and the `.rebalance-action-badge--sell` class

#### Scenario: Hold action renders neutral badge

- **WHEN** an asset plan row has `action = "hold"`
- **THEN** the cell renders a badge with the `Manter` label
  and the `.rebalance-action-badge--hold` class

### Requirement: Compact parameter bar

The system SHALL render a parameter bar above the class summary with
three inline inputs (not full-width):
1. Aporte (R$) input — `data-testid="rebalance-contribution-input"`
2. Desvio mínimo (R$) input — `data-testid="rebalance-threshold-abs"`
3. Desvio mínimo (%) input — `data-testid="rebalance-threshold-pct"`

The bar uses `data-testid="rebalance-params-bar"`.

Threshold inputs SHALL be real form fields submitted with the page
request. When the page first loads, when the caller omits the
threshold values, or after a successful POST redirect (PRG), the
rendered defaults SHALL be `1000` and `1`. Thresholds are ephemeral
display state: they are submitted with the POST and consumed by the
POST-time computation, but they SHALL NOT round-trip into the rendered
plan — after the 303 redirect the follow-up GET recomputes the plan
with the defaults and the threshold inputs re-render at `1000` and `1`.
Only the aporte survives the redirect (see
`POST /rebalanceamento renders the plan` and F52 design D13).

#### Scenario: Parameter bar renders inline inputs without manual button

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-params-bar"` contains the aporte input and two threshold inputs
- **AND** `data-testid="rebalance-submit-btn"` is not rendered

#### Scenario: Threshold defaults are 1000 and 1

- **WHEN** the page loads without explicit threshold values
- **THEN** `data-testid="rebalance-threshold-abs"` has value `1000`
- **AND** `data-testid="rebalance-threshold-pct"` has value `1`

#### Scenario: Submitted thresholds are ephemeral across the POST redirect

- **WHEN** the operator posts aporte `5000`, threshold abs `2500`, and
  threshold pct `2`
- **THEN** the response is HTTP 303 See Other to `/rebalanceamento`
- **AND** the follow-up GET renders a plan computed with the default
  thresholds (`1000` and `1`), not `2500` / `2`
- **AND** `data-testid="rebalance-threshold-abs"` re-renders with value
  `1000` and `data-testid="rebalance-threshold-pct"` with value `1`
- **AND** the rendered plan reflects `metrics.contribution = 5000`

### Requirement: Rebalance inputs submit plan on Enter

The system SHALL keep rebalance input edits local while operator types. It SHALL refresh plan only when operator presses Enter in aporte or threshold input with valid values. Refresh SHALL reuse existing `POST /rebalanceamento` render path and SHALL not require clicking visible manual submit button.

#### Scenario: Enter submits edited aporte

- **WHEN** page is showing rebalance plan
- **AND** operator changes `contribution` from `5000` to `6000`
- **THEN** page does not issue rebalance request while operator is typing
- **WHEN** operator presses Enter
- **THEN** page issues new rebalance request without button click
- **AND** the rendered plan reflects `metrics.contribution = 6000`

### Requirement: Threshold gate affects rendered execution suggestions

The system SHALL render `Compra`, `Venda`, `Qtd`, `Projetado`, and `Ação` from
the server-gated plan. An asset row that fails either minimum threshold SHALL
render as a hold row with zero buy/sell suggestion even if the ungated optimizer
would have moved capital through that asset.

#### Scenario: Small buy recommendation is hidden by threshold gate

- **WHEN** the plan contains an asset with ungated `buy_amount = 600`,
  `deviation_value = 600`, `deviation_pct = 2.0`, and the active thresholds are
  `1000` and `1`
- **THEN** the rendered row shows `Compra = R$ 0,00`
- **AND** the action badge is `Manter`

#### Scenario: Material recommendation stays visible

- **WHEN** the plan contains an asset with `sell_amount = 3500`,
  `deviation_value = 3500`, `deviation_pct = 2.4`, and the active thresholds are
  `1000` and `1`
- **THEN** the rendered row still shows the sell recommendation
- **AND** the action badge is `Vender`

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

### Requirement: Class summary cards render in normative order

The rebalance page SHALL render the class summary cards in the fixed normative order `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`, regardless of the order in which `category_plan` rows arrive from the server. Order SHALL be resolved client-side from `category_name` using a fixed name→position map; no order field SHALL be added to `RebalanceCategoryPlanRow`.

A class name absent from the normative map SHALL render after all mapped classes, with unknown classes ordered alphabetically by `category_name`. The normative order SHALL NOT alter card content, card shell, waterfall chart, CSS, asset plan table, global metrics, or the rebalance solver.

#### Scenario: Known classes render in normative sequence

- **WHEN** the rebalance plan contains category rows for `Ações`, `RF Pós`, `Internacional`, `FII`, `Cripto`, and `RF Dinâmica` in any server order
- **THEN** the rendered class summary cards appear in the sequence `RF Pós`, `RF Dinâmica`, `FII`, `Ações`, `Internacional`, `Cripto`

#### Scenario: Unknown classes render after normative classes

- **WHEN** the rebalance plan contains mapped classes plus unknown classes `Zebra` and `Alpha`
- **THEN** all mapped classes render first in normative order
- **AND** `Alpha` renders before `Zebra` after the mapped classes

#### Scenario: Category payload contract remains unchanged

- **WHEN** the rebalance page renders class summary cards in normative order
- **THEN** `RebalanceCategoryPlanRow` continues to expose exactly the existing seven fields
- **AND** the server `category_plan` payload is not mutated to carry display order

### Requirement: Row color-coding by deviation and action

The system SHALL color asset table rows based on action and deviation:
- `rebalance-asset-row--over`: `|deviation_pct| >= threshold_pct` OR
  `|deviation_value| >= thresholdAbs`
- `rebalance-asset-row--neutral`: `action = "hold"`
- `rebalance-asset-row--buy`: `action = "buy"`
- `rebalance-asset-row--sell`: `action = "sell"`

#### Scenario: Hold row gets neutral treatment

- **WHEN** an asset has `action = "hold"`
- **THEN** the row has class `rebalance-asset-row--neutral`

#### Scenario: Buy row gets green tint

- **WHEN** an asset has `action = "buy"`
- **THEN** the row has class `rebalance-asset-row--buy`

#### Scenario: Sell row gets red tint

- **WHEN** an asset has `action = "sell"`
- **THEN** the row has class `rebalance-asset-row--sell`

### Requirement: Blocked assets excluded from asset plan table

The system SHALL exclude from the asset plan table any asset where `buy_enabled == False AND sell_enabled == False`. These assets are permanently locked ("ativo travado no setup") and always render as "manter" with zero trade amounts — they contribute no actionable information to the operator.

Assets with at least one side enabled (`buy_enabled == True OR sell_enabled == True`) SHALL remain visible in the table regardless of their computed action.

The filter SHALL apply only to the asset plan table display. Category summary cards, waterfall charts, plan metrics, and warnings SHALL reflect the complete portfolio including blocked assets.

#### Scenario: Doubly blocked asset is hidden from table

- **WHEN** the plan contains an asset with `buy_enabled = False` AND `sell_enabled = False`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset does NOT appear in the asset plan table
- **AND** `data-testid="rebalance-asset-table"` contains no row with that asset's `data-asset-key`

#### Scenario: Asset with buy disabled but sell enabled remains visible

- **WHEN** the plan contains an asset with `buy_enabled = False` AND `sell_enabled = True`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset appears in the asset plan table
- **AND** the row carries the correct `data-asset-key`

#### Scenario: Asset with sell disabled but buy enabled remains visible

- **WHEN** the plan contains an asset with `buy_enabled = True` AND `sell_enabled = False`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset appears in the asset plan table
- **AND** the row carries the correct `data-asset-key`

#### Scenario: Category summary cards include blocked assets

- **WHEN** the plan contains blocked assets (`buy_enabled = False AND sell_enabled = False`)
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** category summary cards reflect the complete portfolio values including blocked assets
- **AND** waterfall charts render with the full category totals

#### Scenario: Plan metrics include blocked assets

- **WHEN** the plan contains blocked assets
- **THEN** `metrics.contribution`, `metrics.total_buy`, `metrics.total_sell`, and `metrics.residual_cash` reflect the complete plan including blocked assets
- **AND** the displayed metric values are unchanged from the unfiltered plan

### Requirement: Empty profile renders the empty-state card

The system SHALL render the empty-state card in the main
content area when the active profile has zero `AssetClass`
rows. The card carries a copy block + a "← Voltar ao
dashboard" link.

#### Scenario: Empty state copy and link render

- **WHEN** the profile has zero classes
- **THEN** the empty-state element contains the text
  "Nenhuma classe cadastrada"
- **AND** a link to `/` with the label "← Voltar ao dashboard"
