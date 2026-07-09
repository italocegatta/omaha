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
profile's current aporte, calls `run_rebalance()`, and re-renders the
`rebalance.html` template with the resulting `RebalancePlanResponse`
in the Jinja context. Same URL - no redirect, no JSON wire trip on
the page flow.

The handler SHALL persist the submitted finite contribution for the
active profile in the current session before rendering the page.
When the field is blank or missing, the handler SHALL normalize it to
`0` instead of rendering an error. On non-finite (`NaN` / `inf`), the
handler re-renders the page with an inline `form_error`.

#### Scenario: Valid finite contribution renders and persists the plan

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = 5000.00`
- **THEN** the response is HTTP 200 with the page rendered
- **AND** the main area contains an element with
  `data-testid="rebalance-plan"`
- **AND** the plan renders the compact parameter bar,
  horizontal class summary cards, and the asset plan table
- **AND** a later `GET /rebalanceamento` for the same active profile
  renders a plan with `metrics.contribution = 5000.00`

#### Scenario: Blank contribution is normalized to zero

- **WHEN** `POST /rebalanceamento` is called with an empty
  `contribution` field
- **THEN** the response is HTTP 200 with the page rendered
- **AND** the plan section is visible
- **AND** the rendered plan reflects `metrics.contribution = 0`

#### Scenario: Zero contribution is a valid rebalance plan

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = 0`
- **THEN** the response is HTTP 200 with the plan rendered
  (zero is the rebalance-only case — no new money, just
  reallocation)

#### Scenario: Negative contribution is accepted server-side

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = -1000.00`
- **THEN** the response is HTTP 200 with the plan rendered
  (server is permissive per the contract extension; the page
  client-side gates this for v1 with explanatory copy)

#### Scenario: NaN contribution re-renders with form error

- **WHEN** `POST /rebalanceamento` is called with `contribution = NaN`
- **THEN** the response is HTTP 200 with the page rendered
- **AND** the main area shows an element with
  `data-testid="rebalance-form-error"` containing
  "Use um número finito"
- **AND** the plan section is NOT rendered

#### Scenario: Solver validation failure renders inline error

- **WHEN** `run_rebalance()` raises `RebalanceValidationError`
  with message "Classes devem somar 100%"
- **THEN** the response is HTTP 200 with the page rendered
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
- **AND** clicks the "Rebalancear" button
- **THEN** the form does NOT submit (no POST round-trip)
- **AND** an element with `data-testid="rebalance-form-error"`
  (in-body, not `sidebar-form-error`) shows the message
  "Saques serão suportados em versão futura. Por enquanto,
  deixe o aporte em zero ou positivo."

### Requirement: Asset plan table renders ten visible columns plus a data attribute

The system SHALL render the asset plan table with eleven visible `<th>`
cells: Classe, Ativo, Valor atual, Alvo, Desvio (R$), Desvio (%), Compra,
Venda, Qtd, Projetado, Ação.
Each row carries a `data-asset-key` attribute holding the wire's
`asset_key` field (used by tests; not visible to the operator).

The `Qtd` column SHALL appear immediately after `Venda`. It SHALL show
the calculated trade quantity only for assets with negociação em bolsa
and finite market price. Rows that are not tradeable or lack an apt
price SHALL render the `Qtd` cell empty without shifting the column map.

#### Scenario: Asset plan table has eleven visible columns

- **WHEN** the plan renders
- **THEN** the asset plan `<table>` has exactly eleven `<th>`
  elements in `<thead>`
- **AND** `Qtd` appears after `Venda` and before `Projetado`
- **AND** each `<tbody> <tr>` has the
  `data-asset-key="..."` attribute matching the row's
  `asset_key`

#### Scenario: Desvio columns show deviation values

- **WHEN** an asset has `current_value = 5000` and `target_value = 5500`
- **THEN** the Desvio (R$) cell shows `-R$ 500,00`
- **AND** the Desvio (%) cell shows `-9.1%`

### Requirement: Sortable asset plan table

The system SHALL make the asset plan table sortable by
clicking the `<th>` cells. Click cycles `asc → desc → asc`
on the same column. Default order is the solver's native
order (by `category_order`, then `asset_order`).

The asset plan table SHALL also expose a client-side filter bar
with a class multi-select, an action multi-select, and a text
search input. Filtering happens entirely in Alpine, without
server round-trips.

#### Scenario: Clicking a column header sorts ascending

- **WHEN** the user clicks the "Valor atual" `<th>`
- **THEN** the rows are reordered by `current_value` ascending
- **AND** the clicked `<th>` shows a `↑` indicator

#### Scenario: Second click on same column sorts descending

- **WHEN** the user clicks "Valor atual" twice
- **THEN** the rows are reordered by `current_value` descending
- **AND** the `<th>` shows a `↓` indicator

#### Scenario: Filtering by class shows only matching assets

- **WHEN** the operator deselects all classes except "Ações BR"
- **THEN** only assets with `category_name = "Ações BR"` are visible

#### Scenario: Filtering by action shows only matching assets

- **WHEN** the operator selects only "Comprar"
- **THEN** only assets with `action = "buy"` are visible

#### Scenario: Text search filters by asset name

- **WHEN** the operator types "PETR" in the search input
- **THEN** only assets whose `asset_name` contains "PETR"
  (case-insensitive) are visible

#### Scenario: Filters compose (AND logic)

- **WHEN** class filter is "Ações BR" AND action filter is "Comprar"
- **THEN** only assets matching BOTH criteria are visible

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
four inline elements (not full-width):
1. Aporte (R$) input — `data-testid="rebalance-contribution-input"`
2. Desvio mínimo (R$) input — `data-testid="rebalance-threshold-abs"`
3. Desvio mínimo (%) input — `data-testid="rebalance-threshold-pct"`
4. Rebalancear button — `data-testid="rebalance-submit-btn"`

The bar uses `data-testid="rebalance-params-bar"`.

Threshold inputs SHALL be real form fields submitted with the page request. When
the page first loads or the caller omits the threshold values, the rendered
defaults SHALL be `1000` and `1`. The rendered plan SHALL reflect the submitted
thresholds, not only client-side color-coding.

#### Scenario: Parameter bar renders all four elements inline

- **WHEN** the plan renders
- **THEN** `data-testid="rebalance-params-bar"` contains the aporte
  input, two threshold inputs, and the submit button

#### Scenario: Threshold defaults are 1000 and 1

- **WHEN** the page loads without explicit threshold values
- **THEN** `data-testid="rebalance-threshold-abs"` has value `1000`
- **AND** `data-testid="rebalance-threshold-pct"` has value `1`

#### Scenario: Threshold fields submit with the form

- **WHEN** the operator posts aporte `5000`, threshold abs `2500`, and
  threshold pct `2`
- **THEN** the rendered plan reflects those threshold values
- **AND** rows below either threshold render as non-actionable hold rows

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

### Requirement: Category summary renders as horizontal class cards

The system SHALL render the category deviation summary as horizontal
cards (not a table). Each card displays: class name, current weight
(%), target weight (%), deviation in percentage points, deviation in
R$, projected weight (%).

The card container SHALL use `data-testid="rebalance-class-summary"`
and be a horizontal grid/flex container with wrapping on small viewports.

Color coding: the card SHALL apply `rebalance-class-card--ok` when
`|deviation_pct| < threshold_pct`, `rebalance-class-card--over` when
`|deviation_pct| >= threshold_pct`. Threshold defaults:
`thresholdPct = 1.0` (editable via params bar).

#### Scenario: Class cards render one per AssetClass

- **WHEN** the plan renders with 3 categories
- **THEN** three elements with `data-testid="rebalance-class-card-*"`
  are visible inside `data-testid="rebalance-class-summary"`

#### Scenario: Class card shows current, target, deviation, projected

- **WHEN** a category has `current_pct = 42.0`, `target_pct = 40.0`,
  `deviation_pct = 2.0`, `projected_pct = 40.1`
- **THEN** the card displays "Atual 42.0%", "Alvo 40.0%", "+2.0%",
  and "Projetado 40.1%"

#### Scenario: Class card color codes by threshold

- **WHEN** a category has `|deviation_pct| >= threshold_pct`
- **THEN** the card has class `rebalance-class-card--over`
- **WHEN** a category has `|deviation_pct| < threshold_pct`
- **THEN** the card has class `rebalance-class-card--ok`

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
