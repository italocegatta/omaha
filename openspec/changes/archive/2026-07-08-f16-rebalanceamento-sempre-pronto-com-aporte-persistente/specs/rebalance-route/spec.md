## MODIFIED Requirements

### Requirement: POST /api/rebalance returns a RebalancePlanResponse

The system SHALL expose `POST /api/rebalance` that accepts a
`RebalanceRequest` body and returns a `RebalancePlanResponse` JSON.

`RebalanceRequest` SHALL carry one optional field: `contribution`
(float, R$). When the field is omitted, the route SHALL resolve it as
`0`. `RebalancePlanResponse` SHALL carry five top-level fields:
`asset_plan` (list of `RebalanceAssetPlanRow`), `category_plan`
(list of `RebalanceCategoryPlanRow`), `metrics` (`RebalancePlanMetrics`
object), `warnings` (list of `RebalanceWarning`), and `applied_policy`
(string).

The route SHALL require an authenticated user with an active profile
(via `require_user` + `require_active_profile` from `omaha.auth`),
matching every other JSON route in the project.

#### Scenario: Active profile with classes and assets returns a populated plan

- **WHEN** the authenticated user has an active profile with at least
  one `AssetClass` and one `Asset`, and `POST /api/rebalance` is called
  with `{"contribution": 0}`
- **THEN** the response is HTTP 200 with a `RebalancePlanResponse`
  whose `asset_plan` length equals the number of `Asset` rows in the
  profile, whose `category_plan` length equals the number of
  `AssetClass` rows, and whose `metrics.contribution` equals `0.00`
  (zero is the canonical rebalance-only case - no new money, just
  reallocation)

#### Scenario: Omitted contribution defaults to zero

- **WHEN** `POST /api/rebalance` is called with `{}`
- **THEN** the response is HTTP 200 with a populated
  `RebalancePlanResponse`
- **AND** `metrics.contribution` equals `0.00`

#### Scenario: Unauthenticated request returns 401

- **WHEN** `POST /api/rebalance` is called without a valid session
- **THEN** the response is HTTP 401 (FastAPI default for
  `require_user` failure)

#### Scenario: No active profile returns 400

- **WHEN** the authenticated user has no active profile selected and
  `POST /api/rebalance` is called
- **THEN** the response is HTTP 400 (FastAPI default for
  `require_active_profile` failure)

### Requirement: Request validates contribution as a finite float

The system SHALL accept `contribution` as any finite float (positive,
zero, or negative). When `contribution` is omitted, the system SHALL
behave exactly as if `0` had been supplied. The system SHALL reject
`NaN` and `Infinity` (and `-Infinity`) with HTTP 422 and a `detail`
message stating that the aporte must be a finite number.

An explicit `null` `contribution` value SHALL be rejected with HTTP 422.

*(This requirement replaces "Request validates contribution greater
than zero" - zero is now valid for rebalance-only plans; negative is
permitted for future withdrawal support. The page gates
`contribution < 0` client-side with explanatory copy, but the server
contract stays permissive.)*

#### Scenario: Positive contribution renders the plan

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": 5000.00}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse`

#### Scenario: Zero contribution renders the plan

- **WHEN** `POST /api/rebalance` is called with `{"contribution": 0}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse` (rebalance-only - no new money, just
  reallocation)

#### Scenario: Omitted contribution renders the zero-default plan

- **WHEN** `POST /api/rebalance` is called with `{}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse`
- **AND** `metrics.contribution` equals `0.00`

#### Scenario: Negative contribution renders the plan

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": -1000.00}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse` (withdrawal; the page gates this
  client-side for v1, but the route is permissive in preparation for
  the CVXPY solver's withdrawal support)

#### Scenario: NaN contribution returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": NaN}` (Pydantic rejects via JSON parsing)
- **THEN** the response is HTTP 422

#### Scenario: Infinity contribution returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": Infinity}` (or `"-Infinity"` as a string)
- **THEN** the response is HTTP 422

#### Scenario: Null contribution returns 422

- **WHEN** `POST /api/rebalance` is called with `{"contribution": null}`
- **THEN** the response is HTTP 422
