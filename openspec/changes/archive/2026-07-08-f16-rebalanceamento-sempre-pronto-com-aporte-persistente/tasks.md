## 1. Session-backed aporte state

- [x] 1.1 Add helper(s) to read and write persisted rebalance aporte per active profile in session state
- [x] 1.2 Preserve per-profile aporte across profile switching while keeping logout/app restart reset semantics unchanged

## 2. Page materialization flow

- [x] 2.1 Update `GET /rebalanceamento` to auto-compute and render plan for populated profiles using persisted/default-zero aporte
- [x] 2.2 Update `POST /rebalanceamento` to normalize blank input to zero, persist finite aporte, and re-render from current DB state
- [x] 2.3 Keep zero-class empty state, family/sentinel redirect, and negative client-side gate behavior intact

## 3. JSON contract alignment

- [x] 3.1 Adjust rebalance request/schema parsing so omitted JSON `contribution` resolves to `0` while explicit non-finite/null values still fail validation
- [x] 3.2 Keep `run_rebalance()` invocation and response shape unchanged aside from zero-default contribution semantics

## 4. Spec and test updates

- [x] 4.1 Update rebalance page tests from placeholder-first expectations to always-materialized plan expectations
- [x] 4.2 Add coverage for persisted aporte across navigation/profile switching and for fresh recompute after portfolio mutations
- [x] 4.3 Update rebalance route tests for omitted contribution defaulting to zero
- [x] 4.4 Run `openspec list --specs` and resolve spec-health issues before apply handoff

## 5. Delivery readiness

- [x] 5.1 Confirm no DB migration/seed changes are required
- [x] 5.2 Document any residual UX decision around visible default input value (`0` vs blank) during apply if implementation forces one choice
