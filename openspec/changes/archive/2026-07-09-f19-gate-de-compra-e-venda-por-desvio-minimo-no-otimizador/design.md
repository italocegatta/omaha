## Context

F18 introduced two threshold inputs on `/rebalanceamento` (`Desvio minimo R$`
and `Desvio minimo %`) plus row/card highlighting, but the values stay in
Alpine-only state. The server still solves and renders the same plan regardless
of those inputs. That makes the visual language disagree with the actionable
recommendation.

This slice touches critical rebalance flow, but it does not need a new LP
formulation. The safer path is to keep the solver optimizing the full target and
then suppress sub-threshold trades in the native plan before wire/page mapping.

## Goals / Non-Goals

**Goals:**
- Make threshold inputs part of the rebalance request contract.
- Gate `buy_amount` / `sell_amount` using both absolute and percentual
  deviation thresholds.
- Recompute projected values, category totals, and plan metrics from the gated
  result so UI numbers stay internally consistent.
- Preserve existing defaults (`R$ 1000`, `1%`) when thresholds are omitted.

**Non-Goals:**
- Re-parameterize CVXPY objective or constraints with operator thresholds.
- Persist thresholds across sessions or profiles.
- Introduce per-asset custom thresholds, lot-size rounding, or broker-order
  execution logic.

## Decisions

### D1: Gate in post-processing, not inside LP constraints

**Decision:** run current solver unchanged, then apply threshold suppression in
native plan post-processing before route/page serialization.

**Rationale:** owner asks for execution gating, not a different optimization
objective. Post-processing is smaller, easier to test, and avoids destabilizing
critical CVXPY behavior.

**Alternative considered:** encode thresholds directly in phase-2 constraints.
Rejected because thresholds depend on rendered deviation semantics and would
force wider solver/model changes for little product gain.

### D2: Threshold semantics use logical AND

**Decision:** a trade remains actionable only when `abs(deviation_value) >=
min_deviation_value` AND `abs(deviation_pct) >= min_deviation_pct`.

**Rationale:** roadmap text says the asset must exceed absolute and percentual
minimums. AND semantics is conservative and matches operator intent to block
small drifts that are large in only one dimension.

**Alternative considered:** OR semantics. Rejected because it would still allow
many low-value or low-significance trades through.

### D3: Suppressed rows become hold rows and plan is recomputed

**Decision:** when a row fails the gate, zero its buy/sell amount, reset its
projected value to current value, and rebuild category/projected totals plus
portfolio metrics from gated rows.

**Rationale:** visual suppression alone would leave totals inconsistent. Full
recomputation keeps category cards, projected cash, action badges, and response
payload aligned.

**Alternative considered:** keep projected values from ungated solver output and
only relabel action. Rejected because operator would see totals assuming trades
the UI no longer recommends.

### D4: Thresholds live in both page form and JSON route contract

**Decision:** extend `RebalanceRequest` and page form handling with optional
`min_deviation_value` and `min_deviation_pct`, defaulting to `1000` and `1`
when omitted.

**Rationale:** one canonical contract keeps `/rebalanceamento` and
`POST /api/rebalance` behavior aligned and testable.

**Alternative considered:** page-only form fields with out-of-band server state.
Rejected because it would split behavior across entrypoints.

## Risks / Trade-offs

- **[Residual cash increases after suppression]** Gating may leave capital
  undeployed even when the ungated optimizer found trades. -> Mitigation:
  recompute `residual_cash` and keep it visible in plan metrics.
- **[Zero-target or non-tradeable rows]** Some rows already resolve to hold for
  unrelated reasons. -> Mitigation: apply threshold gate only after existing
  tradeability/action derivation inputs are known and keep current locks intact.
- **[Request-contract drift]** Page and JSON route can diverge if defaults or
  field names differ. -> Mitigation: centralize defaults in request/schema layer
  and cover both surfaces in tests.
