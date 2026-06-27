# Spec: rebalance-route

## Purpose

Define the HTTP + JSON contract for the rebalance endpoint and the
orchestration glue that owns the contract translation between the
reference CVXPY solver (`rebalance-engine`, future change) and the
dashboard (`rebalance-page`, future change). This spec is the
**contract** — Phase 4 plugs the real solver into the glue's solver
hook; Phase 3b consumes the wire format defined here.

## Requirements

### Requirement: POST /api/rebalance returns a RebalancePlanResponse

The system SHALL expose `POST /api/rebalance` that accepts a
`RebalanceRequest` body and returns a `RebalancePlanResponse` JSON.

`RebalanceRequest` SHALL carry one field: `contribution` (float,
R$). `RebalancePlanResponse` SHALL carry five top-level fields:
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
  with `{"contribution": 5000.00}`
- **THEN** the response is HTTP 200 with a `RebalancePlanResponse`
  whose `asset_plan` length equals the number of `Asset` rows in the
  profile, whose `category_plan` length equals the number of
  `AssetClass` rows, and whose `metrics.contribution` equals `5000.00`

#### Scenario: Unauthenticated request returns 401

- **WHEN** `POST /api/rebalance` is called without a valid session
- **THEN** the response is HTTP 401 (FastAPI default for
  `require_user` failure)

#### Scenario: No active profile returns 400

- **WHEN** the authenticated user has no active profile selected and
  `POST /api/rebalance` is called
- **THEN** the response is HTTP 400 (FastAPI default for
  `require_active_profile` failure)

### Requirement: Request validates contribution greater than zero

The system SHALL reject `contribution <= 0` with HTTP 422 and a
`detail` message stating that the aporte must be greater than zero.

#### Scenario: Zero contribution returns 422

- **WHEN** `POST /api/rebalance` is called with `{"contribution": 0}`
- **THEN** the response is HTTP 422 with `detail` containing
  `"Aporte deve ser maior que zero"`

#### Scenario: Negative contribution returns 422

- **WHEN** `POST /api/rebalance` is called with
  `{"contribution": -100.00}`
- **THEN** the response is HTTP 422 with `detail` containing
  `"Aporte deve ser maior que zero"`

#### Scenario: Missing contribution field returns 422

- **WHEN** `POST /api/rebalance` is called with `{}`
- **THEN** the response is HTTP 422 (Pydantic validation error)

### Requirement: Wire format exposes a v1 subset of the solver's native output

The system SHALL expose `RebalanceAssetPlanRow` with exactly these
nine fields:

* `asset_key` (string, `Asset.name.casefold()`)
* `asset_name` (string, `Asset.name`)
* `category_name` (string, `AssetClass.name`)
* `current_value` (float, R$)
* `target_value` (float, R$)
* `buy_amount` (float, R$; `0.0` when no buy is recommended)
* `sell_amount` (float, R$; `0.0` when no sell is recommended)
* `projected_value` (float, R$)
* `action` (enum string: `"buy"`, `"sell"`, or `"hold"`)

The system SHALL expose `RebalanceCategoryPlanRow` with exactly these
four fields:

* `category_name` (string, `AssetClass.name`)
* `current_value` (float, R$)
* `projected_value` (float, R$)
* `delta` (float, R$; `projected_value - current_value`)

The system SHALL expose `RebalancePlanMetrics` with exactly these six
keys:

* `contribution` (float, R$; echoed from request)
* `total_buy` (float, R$; sum of `buy_amount` across `asset_plan`)
* `total_sell` (float, R$; sum of `sell_amount` across `asset_plan`)
* `residual_cash` (float, R$)
* `current_deviation_pct` (float, percentage 0–100; deviation of the
  portfolio's current weights vs target weights)
* `projected_deviation_pct` (float, percentage 0–100; deviation after
  the recommended buys/sells are applied)

The system SHALL expose `RebalanceWarning` with two fields:
`code` (string, machine-readable) and `message` (string, PT-BR
operator-facing).

#### Scenario: Asset plan row carries exactly nine fields

- **WHEN** a `RebalanceAssetPlanRow` is serialized
- **THEN** the JSON object has exactly the keys
  `asset_key, asset_name, category_name, current_value, target_value,
  buy_amount, sell_amount, projected_value, action` and no others

#### Scenario: Action enum is one of three values

- **WHEN** the solver recommends a buy of R$ 200 for an asset
- **THEN** the row's `action` field equals `"buy"`
- **WHEN** the solver recommends a sell of R$ 200
- **THEN** the row's `action` field equals `"sell"`
- **WHEN** the asset's `buy_amount < DISPLAY_TOLERANCE` AND
  `sell_amount < DISPLAY_TOLERANCE` (`DISPLAY_TOLERANCE = 1e-4`)
- **THEN** the row's `action` field equals `"hold"`

#### Scenario: Category delta equals projected minus current

- **WHEN** a category has `current_value = 1000.00` and
  `projected_value = 1500.00`
- **THEN** the row's `delta` field equals `500.00`

#### Scenario: Warning code is machine-readable

- **WHEN** the bridge emits a "Classe vazia com target_pct > 0"
  warning
- **THEN** the response's `warnings` list contains a
  `RebalanceWarning` with `code = "EMPTY_CLASS_NONZERO_TARGET"` and
  `message` equal to the bridge's PT-BR message verbatim

#### Scenario: Applied policy is echoed at the top of the response

- **WHEN** the solver returns a plan with
  `applied_policy = "contribution-only"`
- **THEN** the wire response's top-level `applied_policy` field
  equals `"contribution-only"` (not nested under `metrics`)

#### Scenario: Glue emits hold for sub-tolerance amounts

- **WHEN** the solver returns an asset row with
  `buy_amount = 0.00001` (below `DISPLAY_TOLERANCE = 1e-4`) and
  `sell_amount = 0.0`
- **THEN** the glue maps the row to `RebalanceAssetPlanRow` with
  `action = "hold"` (the round-down to "hold" happens in the
  glue's `_derive_action` helper, not in the solver)

### Requirement: Glue orchestrates profile loading, builders, adapter, and solver

The system SHALL provide `rebalance.glue.run_rebalance(db, profile,
contribution, *, solver=None)` that:

1. Loads the active profile (caller responsibility — `profile` is
   passed in pre-loaded).
2. Calls `rebalance.builders.build_setup_from_db(db, profile)` and
   collects its `warnings` list.
3. Calls `rebalance.builders.build_position_frame(db, profile)` to
   build the position aggregation frame.
4. Instantiates `OmahaMarketPriceLookup(db=db)` and calls
   `lookup.get_quotes(setup.assets)` to resolve quotes.
5. Calls the injected `solver` (default: `rebalance.solver_stub.stub_solver`)
   with `(setup, positions, quotes, contribution)` and receives the
   solver's native `RebalancePlan`.
6. Maps the native plan into the v1 wire format (`RebalancePlanResponse`).
7. Returns the response.

The glue SHALL NOT do any optimization or LP solving itself; that is
the solver's responsibility. The glue SHALL translate solver-native
output into wire format and own the Pydantic schemas.

#### Scenario: Glue invokes builders in the documented order

- **WHEN** `run_rebalance` is called against a profile with 2 classes
  and 5 assets
- **THEN** the glue calls `build_setup_from_db` once, then
  `build_position_frame` once, then `OmahaMarketPriceLookup.get_quotes`
  once, then the solver once, in that order

#### Scenario: Glue collects builder warnings

- **WHEN** `build_setup_from_db` returns warnings
  (e.g. `"Classe 'Cripto' está vazia mas com target_pct=20.00%..."`)
- **THEN** the resulting `RebalancePlanResponse.warnings` list contains
  the bridge warnings (each wrapped in a `RebalanceWarning` with
  `code = "EMPTY_CLASS_NONZERO_TARGET"`) plus any warnings the solver
  itself emits

#### Scenario: Glue passes contribution unchanged to the solver

- **WHEN** `run_rebalance` is called with `contribution = 5000.00`
- **THEN** the solver receives `contribution = 5000.00` (not
  rounded, not converted to int, not wrapped)

### Requirement: Solver stub returns a frozen fixture

The system SHALL provide `rebalance.solver_stub.stub_solver(setup,
positions, quotes, contribution)` that returns a `RebalancePlan`
populated from `tests/fixtures/rebalance_stub_fixture.json`.

The stub SHALL overlay `metrics.contribution = contribution` on
the loaded fixture so the response reflects the request.
All other arguments are ignored except for shape validation
(a `ValueError` is raised if `setup.assets.empty AND
setup.categories.empty` — defensive parity with the real solver).

The fixture SHALL contain:

* 2 `AssetClass` rows (one with `target_weight = 0.6`, one with
  `target_weight = 0.4`).
* 5 `Asset` rows distributed across the classes, including at least
  one with `buy_enabled = False` and at least one with
  `currency_code = "USD"`.
* A populated `asset_plan` (one row per asset) and `category_plan`
  (one row per class).
* `metrics` with all six v1 keys populated (`contribution = 1000.00`,
  the canonical reference value Phase 4's golden test compares against).
* `applied_policy = "stub-fixture-v1"` at the top of the plan.
* A `warnings` list containing exactly one warning: the
  `EMPTY_CLASS_NONZERO_TARGET` warning for a hypothetical empty class.

#### Scenario: Stub overlays contribution from request onto fixture

- **WHEN** `stub_solver` is called with `contribution = 5000.00` and
  the canonical Italo profile shape
- **THEN** the returned `RebalancePlan.metrics.contribution` equals
  `5000.00` (the overlay) and every other field equals the
  fixture value byte-for-byte

#### Scenario: Stub fixture matches golden test reference for canonical contribution

- **WHEN** `stub_solver` is called with `contribution = 1000.00` and
  the canonical Italo profile shape
- **THEN** the returned `RebalancePlan` equals the fixture
  byte-for-byte (the overlay is a no-op at the canonical value)

#### Scenario: Stub raises ValueError on empty inputs

- **WHEN** `stub_solver` is called with a setup whose `assets`
  DataFrame is empty AND `categories` DataFrame is empty
- **THEN** the stub raises `ValueError` (defensive parity with the
  real solver; the route never triggers this because the glue
  short-circuits on `EMPTY_PROFILE` first)

### Requirement: Solver is injected as a callable

The system SHALL accept a custom `solver` callable in
`run_rebalance(db, profile, contribution, *, solver=...)` and use
that callable instead of the default stub.

The route SHALL pass the stub as the default by NOT specifying the
`solver` keyword. Phase 4 (`rebalance-engine`) SHALL swap the
default by changing one line in the route (or by FastAPI dependency
override).

#### Scenario: Custom solver replaces the default

- **WHEN** `run_rebalance` is called with a custom `solver` callable
  that returns a sentinel `RebalancePlan`
- **THEN** the returned `RebalancePlanResponse` reflects the
  custom solver's output, not the stub fixture

#### Scenario: Default solver is the stub

- **WHEN** `run_rebalance` is called without a `solver` keyword
- **THEN** the stub is invoked with the prepared `(setup, positions,
  quotes, contribution)` tuple

### Requirement: RebalanceValidationError maps to HTTP 400

The system SHALL catch `RebalanceValidationError` raised by the
builders (or the solver) and return HTTP 400 with the exception
message in the `detail` field.

The system SHALL NOT catch generic `Exception` — unexpected
exceptions propagate to FastAPI's default 500 handler.

#### Scenario: Solver validation failure returns 400

- **WHEN** the solver raises `RebalanceValidationError` with
  message `"Classes devem somar 100%"` (the bridge itself does
  NOT raise — it returns warnings; Phase 4's solver raises)
- **THEN** the response is HTTP 400 with
  `detail = "Classes devem somar 100%"`

#### Scenario: Solver exception is not caught by the route

- **WHEN** the solver raises a generic `RuntimeError`
- **THEN** the response is HTTP 500 (FastAPI default), not 400

### Requirement: Empty profile returns empty plan with explanatory warning

The system SHALL handle a profile with zero `AssetClass` rows (or
zero `Asset` rows across all classes) by returning a
`RebalancePlanResponse` with empty `asset_plan`, empty
`category_plan`, zero-valued metrics, and a single warning
(`code = "EMPTY_PROFILE"`, `message = "..."`).

The route SHALL NOT raise `RebalanceValidationError` for an empty
profile — the response is well-formed (200), the warning surfaces
the condition for the operator.

#### Scenario: Profile with zero classes returns empty plan

- **WHEN** the active profile has zero `AssetClass` rows and
  `POST /api/rebalance` is called with a valid contribution
- **THEN** the response is HTTP 200 with `asset_plan = []`,
  `category_plan = []`, `metrics.total_buy = 0.0`,
  `metrics.total_sell = 0.0`, and `warnings[0].code = "EMPTY_PROFILE"`

#### Scenario: Profile with classes but no assets returns empty asset plan

- **WHEN** the active profile has 2 `AssetClass` rows but zero
  `Asset` rows across them
- **THEN** the response is HTTP 200 with `asset_plan = []`,
  `category_plan` containing 2 rows with `current_value = 0.0` and
  `projected_value = 0.0`, and `warnings` containing one entry per
  empty class with `code = "EMPTY_CLASS_NONZERO_TARGET"` (or one
  `EMPTY_PROFILE` warning if both classes are empty)

### Requirement: Glue translates solver-native shape to wire format

The glue SHALL accept the solver's native `RebalancePlan` shape (the
shape Phase 4 ships from `rebalance-engine`) and emit a
`RebalancePlanResponse` with only the v1 fields documented in the
"Wire format exposes a v1 subset" requirement.

When the solver emits a column not in the v1 subset, the glue SHALL
drop it silently (the response shape is fixed; future columns
require updating the spec and the glue mapper).

#### Scenario: Glue drops solver columns not in the v1 subset

- **WHEN** the solver returns a `RebalancePlan` whose `asset_plan`
  rows carry 31 columns (including columns not in v1 such as
  `current_weight` and `quote_symbol`)
- **THEN** the wire format `asset_plan` rows carry exactly the 9 v1
  fields and the dropped columns are not present in the response

#### Scenario: Glue preserves column order from the solver

- **WHEN** the solver returns `asset_plan` rows in a specific order
  (by `category_order`, then `asset_order`)
- **THEN** the wire format `asset_plan` rows appear in the same
  order