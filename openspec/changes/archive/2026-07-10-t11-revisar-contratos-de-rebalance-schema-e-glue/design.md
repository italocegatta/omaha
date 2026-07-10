## Context

Rebalance engine data flow:

```
postprocessing._build_plan_metrics()  →  dict with keys:
  "current_asset_deviation"    (float, fraction 0-1)
  "projected_asset_deviation"  (float, fraction 0-1)
  "total_buy_amount"           (float)
  "total_sell_amount"          (float)
         ↓
engine._translate_metrics()    →  RebalancePlanMetricsNative:
  current_deviation_pct    (← current_asset_deviation, no scaling)
  projected_deviation_pct  (← projected_asset_deviation, no scaling)
  total_buy                (← total_buy_amount, key rename ok)
  total_sell               (← total_sell_amount, key rename ok)
         ↓
glue._metrics_from_native()   →  RebalancePlanMetrics (Pydantic wire)
```

Spec `rebalance-route` says `current_deviation_pct` and `projected_deviation_pct` are "percentage 0-100". Engine emits fraction (0-1). Fix: multiply by 100 in `_translate_metrics`.

Stub solver (`solver_stub.py`) fixture stores values already in percentage (e.g., `current_deviation_pct: 5.0`). No stub changes needed.

## Goals / Non-Goals

**Goals:**
- Engine `current_deviation_pct` and `projected_deviation_pct` output matches spec: percentage 0-100.
- Postprocessing dict keys `total_buy_amount` / `total_sell_amount` renamed to `total_buy` / `total_sell` so engine mapping is direct identity.
- All test assertions updated for new percentage values.

**Non-Goals:**
- No spec requirement changes.
- No schema/route/template/DB changes.
- No solver behavior changes (LP formulation unchanged).
- No stub fixture changes (already correct).

## Decisions

1. **Scale in `_translate_metrics` (engine.py) vs scale in glue or postprocessing.**
   `_translate_metrics` is the native-to-native translation layer. Scaling belongs here because `RebalancePlanMetricsNative` is the canonical intermediate shape shared by stub and real engine. Moving scale to glue would fix wire but leave native shape inconsistent. Moving to postprocessing would change the raw metrics dict, which has other consumers (policy cascade). Decision: scale in `_translate_metrics`.

2. **Rename postprocessing dict keys.**
   `total_buy_amount` → `total_buy`, `total_sell_amount` → `total_sell`. This removes the asymmetry where engine remaps keys. The rename is entirely internal to postprocessing's return dict; no external consumer references `total_buy_amount` by name (they access via engine's `_translate_metrics` or native dataclass fields). Postprocessing is the only producer of these keys. Safe.

3. **No delta spec needed.**
   Existing spec already mandates percentage 0-100. Change is code-to-spec alignment, not spec mutation.

## Risks / Trade-offs

- **Stale test expectations.** Several test files hardcode deviation values that will change after scaling. Task 3 covers full audit.
- **Projected deviation depends on postprocessed gated rows.** If gating suppression changes deviation, the percentage scaling is applied after gating — correct, since gating operates on the same gap weights.
- **`improves_asset_deviation` boolean (line 602).** This compares `projected_asset_deviation <= current_asset_deviation`. Since both are scaled by same factor (multiply by 100), boolean outcome is unchanged. No risk.
