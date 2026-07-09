## MODIFIED Requirements

### Requirement: Solver validates inputs and raises on failure

The system SHALL provide
`omaha.rebalance.validation._validate_rebalance_inputs(setup,
position, contribution)` that runs validation checks and raises
`RebalanceValidationError(errors: list[str])` when any check
fails. The error message SHALL be the concatenation of all
failing checks separated by newlines.

Target-allocation validation SHALL treat the following as canonical truth:

1. class target percentages (`AssetClass.target_pct` / `setup.categories.target_weight`)
2. per-class asset target percentages (`Asset.target_pct` / `setup.assets.target_weight_in_category`)

The validator SHALL enforce canonical closure on those layers and SHALL NOT reject the setup
solely because rounded or float-converted derived global per-asset weights fail a redundant
`asset-global-sum-by-class == class-target` check.

At minimum, validation SHALL still reject:

1. `contribution < 0` ⇒ "O aporte informado nao pode ser
   negativo."
2. `setup.categories.empty` ⇒ "O setup nao possui categorias
   carregadas."
3. `setup.assets.empty` ⇒ "O setup nao possui ativos
   carregados."
4. class targets that do not close to 100% within canonical storage-compatible tolerance
5. per-class asset targets that do not close to the owning class's full 100% allocation within
   canonical storage-compatible tolerance
6. asset rows referencing a category absent from the setup
7. position `asset_key` values not present in setup assets
8. non-positive / negative total current-value invariants already required by the existing route
9. `NaN` / `inf` in numeric position columns

`RebalanceValidationError` is already defined in
`omaha.rebalance.models` and is mapped to HTTP 400 by
`routes/rebalance.py` (per `rebalance-route` spec §"Error
mapping") and to inline `form_error` by `routes/pages.py`
(per `rebalance-page` spec §"Validation failure").

#### Scenario: Negative contribution rejects

- **WHEN** `simulate_rebalance` is called with
  `contribution = -1000.0` and otherwise valid setup +
  position
- **THEN** `RebalanceValidationError` raises with the
  message containing "O aporte informado nao pode ser
  negativo."

#### Scenario: Canonical closure mismatch rejects

- **WHEN** `simulate_rebalance` is called with a setup whose
  class totals or per-class asset totals do not close within canonical tolerance
- **THEN** `RebalanceValidationError` raises with the
  corresponding closure message

#### Scenario: Derived global rounding drift does not reject

- **WHEN** `simulate_rebalance` is called with canonical class and intra-class targets that
  close correctly, but derived global per-asset weights would differ from a displayed rounded sum
  by a tiny amount after Decimal-to-float conversion
- **THEN** validation succeeds
- **AND** the solver proceeds using normalized derived weights

#### Scenario: Multiple checks fail, all errors reported

- **WHEN** `simulate_rebalance` is called with a setup +
  position that violates 3 checks simultaneously
- **THEN** `RebalanceValidationError` raises with all 3
  error messages joined by newlines (the user sees every
  problem in one pass, not one-at-a-time)
