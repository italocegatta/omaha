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
- **AND** six elements with `data-testid="rebalance-stat-*"`
  are visible (contribution, total_buy, total_sell,
  residual_cash, current_deviation_pct, projected_deviation_pct)
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

### Requirement: Asset plan table renders eight visible columns plus a data attribute

The system SHALL render the asset plan table with exactly
eight visible `<th>` cells: Ativo, Classe, Valor atual,
Alvo, Compra, Venda, Projetado, Ação. Each row carries a
`data-asset-key` attribute holding the wire's `asset_key`
field (used by tests; not visible to the operator).

#### Scenario: Asset plan table has eight visible columns

- **WHEN** the plan renders
- **THEN** the asset plan `<table>` has exactly eight `<th>`
  elements in `<thead>`
- **AND** each `<tbody> <tr>` has the
  `data-asset-key="..."` attribute matching the row's
  `asset_key`

### Requirement: Sortable asset plan table

The system SHALL make the asset plan table sortable by
clicking the `<th>` cells. Click cycles `asc → desc → asc`
on the same column. Default order is the solver's native
order (by `category_order`, then `asset_order`).

#### Scenario: Clicking a column header sorts ascending

- **WHEN** the user clicks the "Valor atual" `<th>`
- **THEN** the rows are reordered by `current_value` ascending
- **AND** the clicked `<th>` shows a `↑` indicator

#### Scenario: Second click on same column sorts descending

- **WHEN** the user clicks "Valor atual" twice
- **THEN** the rows are reordered by `current_value` descending
- **AND** the `<th>` shows a `↓` indicator

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

### Requirement: Stub banner conditional on applied_policy

The system SHALL render the `<details>` stub banner when
`applied_policy === "stub-fixture-v1"`. The banner explains
the fixture is deterministic and will be replaced by the
CVXPY solver in Phase 4.

#### Scenario: Stub banner visible under fixture stub

- **WHEN** the plan has `applied_policy = "stub-fixture-v1"`
- **THEN** an element with `data-testid="rebalance-stub-banner"`
  is rendered (collapsed `<details>`)

#### Scenario: Stub banner absent under real solver

- **WHEN** the plan has `applied_policy != "stub-fixture-v1"`
- **THEN** no element with
  `data-testid="rebalance-stub-banner"` is rendered

### Requirement: Warnings panel renders all warnings with PT-BR copy

The system SHALL render an element with
`data-testid="rebalance-warnings"` when `warnings.length > 0`.
Each warning renders with the code (monospace) + the
PT-BR operator-facing message.

#### Scenario: Empty warnings list omits the panel

- **WHEN** the plan has `warnings = []`
- **THEN** no element with
  `data-testid="rebalance-warnings"` is rendered

#### Scenario: Multiple warnings render as a list

- **WHEN** the plan has two warnings (codes
  `EMPTY_CLASS_NONZERO_TARGET` and `STALE_QUOTES`)
- **THEN** the panel renders two `<li>` elements, each with
  the code in `<code>` and the message as body text

### Requirement: Six metric cards in a 3×2 grid

The system SHALL render six metric cards in a 3-column × 2-row
grid. Each card carries a `data-testid="rebalance-stat-{key}"`
attribute for testability.

#### Scenario: All six metric cards render

- **WHEN** the plan renders
- **THEN** six elements with `data-testid="rebalance-stat-*"`
  are visible (one per `RebalancePlanMetrics` field)
- **AND** the grid uses `grid-template-columns: repeat(3, 1fr)`

### Requirement: Category summary table renders four columns

The system SHALL render the category plan summary table with
exactly four visible `<th>` cells: Classe, Valor atual,
Projetado, Δ (delta).

#### Scenario: Category summary has four columns

- **WHEN** the plan renders
- **THEN** the category `<table>` has exactly four `<th>`
  elements in `<thead>`

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
