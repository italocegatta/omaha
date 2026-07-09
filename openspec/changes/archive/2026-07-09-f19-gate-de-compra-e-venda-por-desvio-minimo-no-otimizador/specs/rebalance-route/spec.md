## MODIFIED Requirements

### Requirement: POST /api/rebalance returns a RebalancePlanResponse

The system SHALL expose `POST /api/rebalance` that accepts a
`RebalanceRequest` body and returns a `RebalancePlanResponse` JSON.

`RebalanceRequest` SHALL carry three optional fields:

- `contribution` (float, R$)
- `min_deviation_value` (float, R$)
- `min_deviation_pct` (float, percentage)

When omitted, the route SHALL resolve them as `0`, `1000`, and `1`
respectively. `RebalancePlanResponse` SHALL carry five top-level fields:
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

#### Scenario: Omitted thresholds default to page defaults

- **WHEN** `POST /api/rebalance` is called with `{}`
- **THEN** the response is HTTP 200 with a populated
  `RebalancePlanResponse`
- **AND** the route evaluates the plan using `min_deviation_value = 1000.0`
- **AND** the route evaluates the plan using `min_deviation_pct = 1.0`

#### Scenario: Explicit thresholds reach the rebalance pipeline unchanged

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": 5000, "min_deviation_value": 2500, "min_deviation_pct": 2}`
- **THEN** the response is HTTP 200
- **AND** the rebalance pipeline receives `5000`, `2500`, and `2` unchanged

#### Scenario: Unauthenticated request returns 401

- **WHEN** `POST /api/rebalance` is called without a valid session
- **THEN** the response is HTTP 401 (FastAPI default for
  `require_user` failure)

#### Scenario: No active profile returns 400

- **WHEN** the authenticated user has no active profile selected and
  `POST /api/rebalance` is called
- **THEN** the response is HTTP 400 (FastAPI default for
  `require_active_profile` failure)

## ADDED Requirements

### Requirement: Request validates threshold inputs as finite non-negative floats

The system SHALL accept `min_deviation_value` and `min_deviation_pct` as finite
non-negative floats. When omitted, the system SHALL behave exactly as if `1000`
and `1` had been supplied. The system SHALL reject negative, `NaN`, and infinite
threshold values with HTTP 422. Explicit `null` threshold values SHALL also be
rejected with HTTP 422.

#### Scenario: Negative absolute threshold returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"min_deviation_value": -1}`
- **THEN** the response is HTTP 422

#### Scenario: Infinite percentual threshold returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"min_deviation_pct": Infinity}`
- **THEN** the response is HTTP 422

#### Scenario: Null threshold returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"min_deviation_value": null}`
- **THEN** the response is HTTP 422
