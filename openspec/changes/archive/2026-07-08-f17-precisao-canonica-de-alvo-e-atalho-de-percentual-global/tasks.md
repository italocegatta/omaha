## 1. Precision and persistence model

- [x] 1.1 Add Alembic migration widening `assets.target_pct` from 2-decimal storage to `Numeric(9, 6)` and align SQLAlchemy model metadata
- [x] 1.2 Audit asset create/update serialization paths so canonical `Asset.target_pct` round-trips with expanded precision in SQLite and Postgres
- [x] 1.3 Confirm seed/snapshot/import surfaces do not silently truncate the widened asset precision

## 2. Asset edit contract and dashboard shortcut flow

- [x] 2.1 Extend `PATCH /api/assets/{id}` to accept either canonical `target_pct` or a dedicated `% ativo na carteira` shortcut field, with mutual-exclusion and range-validation rules
- [x] 2.2 Move `% carteira -> % classe` conversion into server-side Decimal helpers keyed by the owning class target
- [x] 2.3 Update dashboard inline-edit JS/template flow so `commitEditTotal` submits the global shortcut value directly and re-renders from server-confirmed state instead of local back-solve rounding
- [x] 2.4 Keep per-class off-100 edits accepted while surfacing server 422 errors for invalid shortcut conversions without adding new client-side blockers

## 3. Canonical Decimal rebalance pipeline

- [x] 3.1 Refactor rebalance target helpers/builders so canonical class and intra-class percentages are derived and validated in Decimal before any float conversion
- [x] 3.2 Update rebalance validation to enforce canonical class closure + per-class asset closure and remove redundant derived-global closure rejection
- [x] 3.3 Introduce a single explicit float-boundary handoff from Decimal-normalized setup data into pandas/numpy/CVXPY structures
- [x] 3.4 Audit solver, policy, and post-processing tolerance touchpoints so optimizer behavior remains stable after the new Decimal-to-float handoff

## 4. Specs and regression coverage

- [x] 4.1 Add route/unit coverage for `% ativo na carteira` shortcut edits, including high-precision round-trip persistence and class-target-zero edge cases
- [x] 4.2 Update rebalance builder/validation/solver tests to cover canonical-closure acceptance when derived global display sums drift by tiny rounding amounts
- [x] 4.3 Update dashboard/e2e coverage so inline `% total` edits assert the new server-authoritative payload/response behavior
- [x] 4.4 Run `openspec list --specs` and resolve spec-health issues before apply handoff

## 5. Delivery safety

- [x] 5.1 Document rollback expectations for the precision-widening migration, including downgrade rounding policy
- [x] 5.2 Verify final implementation still respects CVXPY float limitations by keeping Decimal confined to pre-optimizer math
