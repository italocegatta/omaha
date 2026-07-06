## MODIFIED Requirements

### Requirement: GET /rebalance renders the rebalance plan page

The system SHALL expose `GET /rebalanceamento` (PT-BR slug, `D1`)
that returns HTTP 200 with the rendered `rebalance.html` template.
Auth follows the project standard (`require_user` +
`require_active_profile`).

When the active profile has zero `AssetClass` rows, the main
content area renders an empty-state card; the in-body form is
present but inert (the input + button carry `disabled`).
When the profile has classes, the main area renders either a
placeholder ("defina um aporte e clique em Rebalancear") or the
last computed plan if the request carried a previously-submitted
aporte in the form (default: placeholder).

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

#### Scenario: Authenticated user with populated profile sees placeholder

- **WHEN** the active profile has at least one `AssetClass` row
- **AND** `GET /rebalanceamento` is called without a prior form
  submission
- **THEN** the response is HTTP 200
- **AND** the main area contains an element with
  `data-testid="rebalance-placeholder"`
- **AND** the in-body form's input does NOT have the `disabled`
  attribute

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
`contribution` from the in-body form, calls `run_rebalance()`,
and re-renders the `rebalance.html` template with the resulting
`RebalancePlanResponse` in the Jinja context. Same URL — no
redirect, no JSON wire trip on the page flow.

The handler SHALL render the page with the plan visible when
the aporte is a finite float (including 0 and negative). On
non-finite (`NaN` / `inf`) or missing `contribution`, the
handler re-renders the page with an inline `form_error`.

#### Scenario: Valid finite contribution renders the plan

- **WHEN** `POST /rebalanceamento` is called with
  `contribution = 5000.00`
- **THEN** the response is HTTP 200 with the page rendered
- **AND** the main area contains an element with
  `data-testid="rebalance-plan"`
- **AND** six elements with `data-testid="rebalance-stat-*"`
  are visible (contribution, total_buy, total_sell,
  residual_cash, current_deviation_pct, projected_deviation_pct)
- **AND** the asset plan table has one `<tr>` per `asset_plan`
  row in the response
- **AND** the category summary table has one `<tr>` per
  `category_plan` row

#### Scenario: Zero contribution is a valid rebalance plan

- **WHEN** `POST /rebalanceamento` is called with `contribution = 0`
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

#### Scenario: Missing contribution re-renders with form error

- **WHEN** `POST /rebalanceamento` is called without a
  `contribution` field
- **THEN** the response is HTTP 200 with the page rendered
- **AND** the form error element contains "Informe um valor
  de aporte"

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

## REMOVED Requirements

### Requirement: Sidebar carries the rebalance form on every authenticated page
**Reason**: Sidebar removed in F02. Form lives in the body of
`/rebalanceamento` only — not on every authenticated page.
**Migration**: Visit `/rebalanceamento` to access the form.
On `/patrimonio`, the top nav link takes the user there.

### Requirement: Header navigation row on the rebalance page
**Reason**: Per-card navigation row (`← Dashboard` link +
`Plano de aporte` label) is replaced by the global top nav.
**Migration**: Use the top nav tabs (`Patrimônio |
Rebalanceamento | Rentabilidade | Proventos`) for site-wide
navigation. The rebalance page no longer renders its own
per-card nav row.
