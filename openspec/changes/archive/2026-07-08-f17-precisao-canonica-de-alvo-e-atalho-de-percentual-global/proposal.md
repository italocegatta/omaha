## Why

Today Omaha treats a derived number (`% ativo na carteira`) as if it were an independent source of truth for rebalance validation, even though the operator naturally defines allocation from `% classe` plus `% ativo na classe`. This creates false validation failures under legitimate round-trip editing (`% carteira -> % classe`) because `Asset.target_pct` is persisted with only two decimal places and the rebalance pipeline converts to `float` too early for a CVXPY domain that should only see binary floats at its final boundary.

## What Changes

- Redefine target allocation semantics so `AssetClass.target_pct` and `Asset.target_pct` are the only persisted truth; global per-asset target percentages become derived values for display, request translation, and solver input only.
- Preserve inline editing of `alvo % total`, but move the `% carteira -> % classe` conversion to the server so the canonical persisted field remains `Asset.target_pct` and client-side `toFixed(2)` does not decide the stored target.
- Increase internal precision of `Asset.target_pct` storage so `% carteira` edits can round-trip with materially less loss while keeping the visible dashboard format compact.
- Move pre-solver target math and validation to `Decimal`, delaying conversion to `float` until numpy/CVXPY arrays are built.
- Replace rebalance validation that compares derived global asset weights against class weights as an independent truth check; canonical validation will instead enforce class total = 100% and per-class asset totals = 100%, while still producing stable derived global weights for the optimizer.
- Audit optimizer touchpoints (`solver`, `policy`, `postprocessing`) so every place that still needs `float` receives normalized, deterministic inputs from the Decimal domain rather than UI-rounded artifacts.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `dashboard-inline-editing`: `alvo % total` remains editable, but the conversion from global target to in-class target becomes server-authoritative and must preserve canonical `% ativo na classe` semantics without client-side early rounding.
- `rebalance-data-bridges`: setup builder requirements change to derive optimizer weights from Decimal-backed canonical targets and to define the float boundary explicitly at numpy/CVXPY handoff.
- `rebalance-engine`: validation requirements change so canonical class/intra-class target closure is enforced, while derived global weights are no longer treated as an independent persisted truth check.

## Impact

- `src/omaha/models.py` plus a new Alembic migration - raise `Asset.target_pct` precision without changing ownership of `AssetClass.target_pct`.
- `src/omaha/routes/assets.py`, `src/omaha/routes/pages.py`, and dashboard Alpine/Jinja templates - shift `% carteira` edit semantics to server-side conversion and expose any necessary preview/response data.
- `src/omaha/rebalance/builders.py`, `validation.py`, and possibly helper modules - introduce Decimal-native canonical math before solver handoff.
- `src/omaha/rebalance/solver.py`, `policy.py`, `postprocessing.py` - review every float assumption so CVXPY still receives normalized arrays and tolerance logic remains meaningful in optimizer space.
- `openspec/specs/dashboard-inline-editing/spec.md`, `openspec/specs/rebalance-data-bridges/spec.md`, and `openspec/specs/rebalance-engine/spec.md` - update behavioral contract.
- Route/page/solver tests and migration coverage - add regressions for `% carteira` edit round-trip, canonical closure validation, and optimizer-stability expectations under precision-heavy targets.
