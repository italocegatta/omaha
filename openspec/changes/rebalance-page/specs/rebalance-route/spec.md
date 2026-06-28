# Spec Delta: rebalance-route

## Purpose

The `rebalance-page` change extends the `rebalance-route`
contract to accept any finite float for `contribution`
(including 0 = rebalance-only and negative = withdrawal,
the latter gated client-side by the page for v1). The
schema's `gt=0` constraint is relaxed; the v1 "rejects
contribution ≤ 0 with 422" requirement is replaced by
"validates contribution as a finite float".

This delta applies on top of the locked
`openspec/specs/rebalance-route/spec.md`.

## MODIFIED Requirements

### Requirement: Request validates contribution as a finite float

The system SHALL accept `contribution` as any finite float
(positive, zero, or negative). The system SHALL reject `NaN`
and `Infinity` (and `-Infinity`) with HTTP 422 and a `detail`
message stating that the aporte must be a finite number.

*(This requirement replaces "Request validates contribution
greater than zero" — zero is now valid for rebalance-only
plans; negative is permitted for future withdrawal support.)*

A missing `contribution` field SHALL be rejected with HTTP
422 (Pydantic required-field error).

The page (`rebalance-page`) gates `contribution < 0`
client-side with explanatory copy ("saques serão suportados
em versão futura"), but the server-side contract is
permissive for forward compatibility with the CVXPY solver's
withdrawal support in Phase 4.

#### Scenario: Positive contribution renders the plan (UPDATED)

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": 5000.00}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse`

#### Scenario: Zero contribution renders the plan (NEW)

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": 0}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse` (rebalance-only, no new money)

#### Scenario: Negative contribution renders the plan (NEW)

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": -1000.00}`
- **THEN** the response is HTTP 200 with the populated
  `RebalancePlanResponse` (withdrawal; the page gates
  this client-side, but the route is permissive)

#### Scenario: NaN contribution returns 422 (NEW)

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": NaN}` (or `"NaN"` as a string)
- **THEN** the response is HTTP 422 (Pydantic finite-float
  validation)

#### Scenario: Infinity contribution returns 422 (NEW)

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": Infinity}` (or `"-Infinity"`)
- **THEN** the response is HTTP 422

#### Scenario: Missing contribution field returns 422 (UNCHANGED)

- **WHEN** `POST /api/rebalance` is called with `{}`
- **THEN** the response is HTTP 422 (Pydantic required-field
  error)

## REMOVED Scenarios

The following scenarios are removed from
`openspec/specs/rebalance-route/spec.md` because they are
no longer enforced:

* ~~"Zero contribution returns 422"~~ — zero is now valid.
* ~~"Negative contribution returns 422"~~ — negative is now
  accepted (gated client-side by the page).

## ADDED Requirements

*(none beyond the MODIFIED requirement above)*

## Notes

* The `RebalanceRequest` Pydantic schema drops `Field(gt=0)`.
  The schema becomes `contribution: float` with no extra
  constraint; Pydantic's built-in JSON parsing rejects
  `NaN`/`Infinity` via the `allow_inf_nan=False` default
  (verify during implementation; if Pydantic version differs,
  add a `field_validator` that calls `math.isfinite`).
* The fixture `tests/fixtures/rebalance_stub_fixture.json`
  is unchanged — it still carries `metrics.contribution =
  1000.00` as the canonical golden value Phase 4's tests
  compare against.
* The stub's `applied_policy = "stub-fixture-v1"` is unchanged.
  The page's stub banner reads this string verbatim; the
  banner disappears automatically when Phase 4 swaps in a
  different `applied_policy` value (e.g. `"contribution-
  only"`).
