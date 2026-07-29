## MODIFIED Requirements

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
