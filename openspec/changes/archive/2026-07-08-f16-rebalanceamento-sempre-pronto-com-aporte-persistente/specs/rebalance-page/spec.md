## MODIFIED Requirements

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

The previous URL `/rebalance` is no longer served - requests to
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
  (zero is the rebalance-only case - no new money, just
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
