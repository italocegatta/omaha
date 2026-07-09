## Context

Current target allocation logic mixes two layers that should not have equal authority:

- canonical portfolio intent: `AssetClass.target_pct` (`% classe`) and `Asset.target_pct` (`% ativo na classe`)
- derived global presentation: `% ativo na carteira`

The dashboard currently lets the user edit `% ativo na carteira`, but the client back-solves that value into `target_pct` using browser `float` math and `toFixed(2)` before the request reaches the server. The rebalance builder then multiplies those rounded values into global weights and the validator treats the derived global totals as an independent truth check with `1e-6` tolerance. This combination produces false failures even when the operator's canonical allocation is valid for human financial use.

The slice crosses persistence, route/template semantics, rebalance builders, validation, and the CVXPY boundary. CVXPY and numpy still require `float`, so the design must improve decimal correctness without pretending the optimizer can run on Python `Decimal` objects directly.

## Goals / Non-Goals

**Goals:**

- Make `% classe` and `% ativo na classe` the only persisted target-allocation truth.
- Preserve editing of `% ativo na carteira` as a supported dashboard workflow.
- Move `% carteira -> % classe` conversion to the server and avoid early browser rounding deciding persisted target state.
- Increase `Asset.target_pct` precision enough that `% carteira` edits can round-trip with low loss.
- Perform target math and closure validation in `Decimal` up to the last practical boundary before numpy/CVXPY.
- Feed the optimizer deterministic, normalized float arrays derived from canonical Decimal inputs.

**Non-Goals:**

- No attempt to make CVXPY solve directly on `Decimal`; solver, policy, and post-processing remain float/numpy-based at execution time.
- No automatic residual redistribution across sibling assets during editing.
- No change to class-level source of truth: `AssetClass.target_pct` stays user-edited directly and remains the category anchor.
- No visual requirement that the displayed sum of rounded `% ativo na carteira` cells equals the class header exactly line-by-line.

## Decisions

### D-F17.1 - Canonical truth lives only in class and intra-class targets

`AssetClass.target_pct` and `Asset.target_pct` are the only persisted target-allocation truth. Any global per-asset target percentage is derived from those two fields and is not validated as an independent stored invariant.

Rationale: this matches operator intent and removes the semantic bug where a projection is treated as first-class truth.

Alternatives considered:

- Persist both intra-class and global per-asset targets - rejected; dual truth creates reconciliation bugs and unclear edit precedence.
- Make global target the only truth - rejected; owner explicitly thinks in `% ativo na classe` first.

### D-F17.2 - `% ativo na carteira` edit becomes an explicit server-side shortcut field

`PATCH /api/assets/{id}` will continue to accept canonical `target_pct`, but it will also accept one alternate input for the shortcut workflow: a global-target field representing `% ativo na carteira`. The server resolves that field against the owning class's current `target_pct`, computes canonical intra-class `Asset.target_pct` in Decimal, persists canonical value, and returns canonical + derived values needed by the UI.

Rationale: the browser should submit the operator's intended global number, not a client-rounded back-solve. Server-side conversion uses one source of truth for class target and one rounding policy for persistence.

Alternatives considered:

- Keep the current client back-solve and only swap `float` for JavaScript decimal helpers - rejected; still duplicates conversion logic and leaves server unaware of the user's actual global input intent.
- Remove `% carteira` editing entirely - rejected; owner still wants the shortcut.

### D-F17.3 - Raise `Asset.target_pct` precision to `Numeric(9, 6)`

`Asset.target_pct` moves from `Numeric(5, 2)` to `Numeric(9, 6)`. `AssetClass.target_pct` remains at current shape unless migration analysis finds a concrete need to widen it too.

Rationale: six decimal places are enough to preserve practical fidelity when converting a two-decimal global target through a two-decimal class anchor, while keeping schema and serialization simple across SQLite and Postgres. The visible UI can still render two decimals by default.

Alternatives considered:

- Keep `Numeric(5, 2)` and rely only on Decimal math - rejected; conversion still collapses meaningful information at persistence boundary.
- Increase both class and asset precision immediately - rejected for now; class precision is not the main round-trip loss point and widening both fields adds migration/test churn without proven benefit.
- Use `Numeric(7, 4)` - considered but rejected; works for many cases, but `6` decimal places gives safer headroom for repeated global-edit round-trips.

### D-F17.4 - Split Decimal domain from optimizer float boundary

Pre-solver pipeline will be divided into two domains:

1. **Canonical Decimal domain**: parsing request payloads, validating class totals, validating intra-class totals, and deriving exact global weights from class/intra-class truth.
2. **Optimizer float domain**: building pandas/numpy/CVXPY arrays from already-normalized Decimal results immediately before solver/policy/post-processing operations that require floats.

Rationale: this isolates binary floating-point noise to the place where it is unavoidable and keeps all business-meaningful target arithmetic in decimal space.

Alternatives considered:

- Continue converting `Decimal -> float` in builder extraction - rejected; current bug proves that boundary is too early.
- Reimplement solver stack around Decimal matrices - rejected; incompatible with CVXPY/numpy and far beyond slice scope.

### D-F17.5 - Rebalance validation checks canonical closure, not redundant derived closure

Validation will continue to reject malformed setups, but target-closure rules change:

- class totals must close in Decimal within storage-compatible tolerance
- each class's asset totals must close in Decimal within storage-compatible tolerance
- derived global per-asset weights are computed from canonical truth for the optimizer, but mismatch between rounded display sums and class header is not a validation error by itself

Rationale: redundant global-vs-class closure is the direct source of the current false negative and provides no extra business safety once canonical layers are closed.

Alternatives considered:

- Keep redundant derived closure check with larger tolerance - rejected; still validates the wrong invariant and makes tolerance choice arbitrary.

### D-F17.6 - Keep display rounding separate from persistence rounding

Dashboard rendering continues to format percentages for readability (typically two decimals), while persistence and internal rebalance derivation use higher precision. The class header remains the authority for class target; rounded row-level global percentages are informative.

Rationale: this avoids inventing hidden residual adjustments while preserving a compact UI.

Alternatives considered:

- Force visible row sums to close exactly by adjusting one asset - rejected; owner explicitly does not want hidden residual compensation.
- Show six decimals everywhere - rejected; poor UX for routine editing.

## Risks / Trade-offs

- [Migration touches a persisted numeric column used in SQLite and Postgres] -> Mitigation: design the Alembic change as a precision-widening migration with explicit downgrade behavior and regression coverage for ORM serialization.
- [Global-target shortcut payload may drift from existing inline-edit tests and client assumptions] -> Mitigation: spec the new request shape clearly and update route/template/e2e tests together.
- [Float-based optimizer thresholds (`ALLOCATION_TOLERANCE`, `DISPLAY_TOLERANCE`) may still expose tiny binary noise after boundary conversion] -> Mitigation: normalize Decimal-derived weights before conversion and audit comparisons that currently assume builder-level floats already sum exactly.
- [Rounded dashboard values may still look visually off by 0.01 when summed by hand] -> Mitigation: keep class header authoritative and, if needed during apply, add lightweight explanatory affordance rather than hidden residual mutation.
- [CSV seed and snapshot flows may now emit more precise asset percentages than before] -> Mitigation: review seed, snapshot, and form serialization so precision expansion is lossless and intentional.

## Migration Plan

1. Add Alembic migration widening `Asset.target_pct` precision and confirm SQLAlchemy model/serialization alignment.
2. Extend asset update contract so server accepts either canonical `target_pct` or global shortcut input, with explicit mutual-exclusion rules.
3. Introduce Decimal helpers for target parsing, closure validation, and global-weight derivation.
4. Refactor rebalance builders/validation to consume Decimal-derived canonical weights and move `float` conversion to optimizer boundary.
5. Audit solver/policy/post-processing entry points to ensure they consume normalized float arrays without changing LP formulation.
6. Update specs and tests for new shortcut semantics, precision persistence, and false-negative validation removal.
7. Run OpenSpec spec validation before apply handoff.

Rollback: revert code plus precision migration. Existing data is widening-only, so rollback requires explicit down-rounding policy in Alembic downgrade and should be documented during apply.

## Open Questions

- Should the shortcut request field be named `target_pct_total`, `portfolio_target_pct`, or another route-local alias? Design intent is clear; exact name can be finalized during apply with minimal churn.
- Should successful asset PATCH responses include both canonical and derived target percentages so the client never re-derives after save, or is canonical response plus current class target enough?
- Do CSV seed and snapshot outputs need to preserve full six-decimal asset precision, or can they continue presenting rounded values while import path remains lossless?
